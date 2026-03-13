"""
Rate limiter for LLM API calls.

Implements a token bucket algorithm for smooth rate limiting with support
for different operation types and configurable limits.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Types of LLM operations with potentially different rate limits."""

    ANALYSIS = "analysis"
    GENERATION = "generation"
    TRAINING = "training"
    DEFAULT = "default"


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded and request cannot be queued."""

    def __init__(
        self,
        message: str,
        operation_type: OperationType,
        wait_time: float,
        current_rate: float,
        limit: float,
    ):
        super().__init__(message)
        self.operation_type = operation_type
        self.wait_time = wait_time
        self.current_rate = current_rate
        self.limit = limit


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Default requests per minute
    default_limit: int = 60

    # Operation-specific limits (requests per minute)
    operation_limits: Dict[OperationType, int] = field(default_factory=dict)

    # Maximum queue size for waiting requests
    max_queue_size: int = 100

    # Maximum wait time in seconds before timing out
    max_wait_time: float = 60.0

    # Enable/disable rate limiting
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Create configuration from environment variables."""
        default_limit = int(os.environ.get("LLM_RATE_LIMIT_PER_MINUTE", "60"))
        enabled = os.environ.get("LLM_RATE_LIMIT_ENABLED", "true").lower() == "true"
        max_queue_size = int(os.environ.get("LLM_RATE_LIMIT_MAX_QUEUE", "100"))
        max_wait_time = float(os.environ.get("LLM_RATE_LIMIT_MAX_WAIT", "60.0"))

        # Operation-specific limits from environment
        operation_limits: Dict[OperationType, int] = {}
        for op_type in OperationType:
            env_key = f"LLM_RATE_LIMIT_{op_type.value.upper()}_PER_MINUTE"
            env_value = os.environ.get(env_key)
            if env_value:
                operation_limits[op_type] = int(env_value)

        return cls(
            default_limit=default_limit,
            operation_limits=operation_limits,
            max_queue_size=max_queue_size,
            max_wait_time=max_wait_time,
            enabled=enabled,
        )


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Tokens are added at a constant rate and consumed by requests.
    This provides smooth rate limiting rather than hard cutoffs.
    """

    def __init__(self, rate: float, capacity: Optional[float] = None):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second to add to the bucket
            capacity: Maximum tokens in the bucket (defaults to rate * 60 for 1 minute burst)
        """
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate * 60
        self.tokens = self.capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    async def acquire(self, tokens: float = 1.0, wait: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default 1)
            wait: Whether to wait for tokens to become available
            timeout: Maximum time to wait in seconds

        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not wait:
                return False

            # Calculate wait time
            wait_time = (tokens - self.tokens) / self.rate

            if timeout is not None and wait_time > timeout:
                return False

            # Release lock while waiting
        await asyncio.sleep(wait_time)

        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: float = 1.0) -> float:
        """Get estimated wait time for acquiring tokens."""
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        return (tokens - self.tokens) / self.rate

    def get_current_rate(self) -> float:
        """Get current token level as a percentage of capacity."""
        self._refill()
        return (self.tokens / self.capacity) * 100 if self.capacity > 0 else 0


class RateLimiter:
    """
    Rate limiter for LLM API calls with support for different operation types.

    Uses a token bucket algorithm for smooth rate limiting with configurable
    limits per operation type and graceful degradation through queuing.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize the rate limiter.

        Args:
            config: Rate limit configuration. If None, loads from environment.
        """
        self.config = config or RateLimitConfig.from_env()
        self._buckets: Dict[OperationType, TokenBucket] = {}
        self._queue_sizes: Dict[OperationType, int] = {}
        self._lock = asyncio.Lock()

        # Initialize buckets for each operation type
        self._init_buckets()

        logger.info(
            "Rate limiter initialized: enabled=%s, default_limit=%d/min",
            self.config.enabled,
            self.config.default_limit,
        )

    def _init_buckets(self) -> None:
        """Initialize token buckets for each operation type."""
        for op_type in OperationType:
            limit = self.config.operation_limits.get(op_type, self.config.default_limit)
            # Convert requests per minute to requests per second
            rate = limit / 60.0
            self._buckets[op_type] = TokenBucket(rate=rate, capacity=limit)
            self._queue_sizes[op_type] = 0

    def get_limit(self, operation_type: OperationType) -> int:
        """Get the rate limit for an operation type."""
        return self.config.operation_limits.get(operation_type, self.config.default_limit)

    async def acquire(
        self,
        operation_type: OperationType = OperationType.DEFAULT,
        wait: bool = True,
    ) -> None:
        """
        Acquire permission to make an API call.

        Args:
            operation_type: Type of operation being performed
            wait: Whether to wait for rate limit or raise immediately

        Raises:
            RateLimitExceededError: If rate limit is exceeded and cannot wait
        """
        if not self.config.enabled:
            return

        bucket = self._buckets[operation_type]

        # Check queue size
        async with self._lock:
            if wait and self._queue_sizes[operation_type] >= self.config.max_queue_size:
                limit = self.get_limit(operation_type)
                raise RateLimitExceededError(
                    f"Rate limit queue full for {operation_type.value}. "
                    f"Maximum queue size ({self.config.max_queue_size}) reached.",
                    operation_type=operation_type,
                    wait_time=bucket.get_wait_time(),
                    current_rate=bucket.get_current_rate(),
                    limit=limit,
                )
            if wait:
                self._queue_sizes[operation_type] += 1

        try:
            acquired = await bucket.acquire(
                tokens=1.0,
                wait=wait,
                timeout=self.config.max_wait_time if wait else None,
            )

            if not acquired:
                limit = self.get_limit(operation_type)
                wait_time = bucket.get_wait_time()

                logger.warning(
                    "Rate limit exceeded for %s: wait_time=%.2fs, limit=%d/min",
                    operation_type.value,
                    wait_time,
                    limit,
                )

                raise RateLimitExceededError(
                    f"Rate limit exceeded for {operation_type.value}. "
                    f"Limit: {limit}/min. Estimated wait: {wait_time:.2f}s",
                    operation_type=operation_type,
                    wait_time=wait_time,
                    current_rate=bucket.get_current_rate(),
                    limit=limit,
                )

            logger.debug(
                "Rate limit acquired for %s: remaining=%.1f%%",
                operation_type.value,
                bucket.get_current_rate(),
            )
        finally:
            if wait:
                async with self._lock:
                    self._queue_sizes[operation_type] = max(
                        0, self._queue_sizes[operation_type] - 1
                    )

    def check_limit(self, operation_type: OperationType = OperationType.DEFAULT) -> bool:
        """
        Check if rate limit would be exceeded without consuming a token.

        Args:
            operation_type: Type of operation being performed

        Returns:
            True if a request can be made, False otherwise
        """
        if not self.config.enabled:
            return True

        bucket = self._buckets[operation_type]
        bucket._refill()
        return bucket.tokens >= 1.0

    def get_status(self, operation_type: OperationType = OperationType.DEFAULT) -> Dict:
        """
        Get current rate limit status.

        Args:
            operation_type: Type of operation to check

        Returns:
            Dictionary with rate limit status information
        """
        bucket = self._buckets[operation_type]
        bucket._refill()

        return {
            "operation_type": operation_type.value,
            "enabled": self.config.enabled,
            "limit_per_minute": self.get_limit(operation_type),
            "available_tokens": round(bucket.tokens, 2),
            "capacity": round(bucket.capacity, 2),
            "utilization_percent": round(
                100 - bucket.get_current_rate(), 2
            ),
            "queue_size": self._queue_sizes.get(operation_type, 0),
            "max_queue_size": self.config.max_queue_size,
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        The global RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """
    Set the global rate limiter instance.

    Args:
        limiter: The RateLimiter instance to use globally
    """
    global _rate_limiter
    _rate_limiter = limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = None
