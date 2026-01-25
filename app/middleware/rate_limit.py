"""
Production-grade rate limiting with tier-based limits and dual backend support.

This module provides a sliding window rate limiter that:
- Enforces per-minute and per-hour limits based on user subscription tier
- Uses Redis for distributed rate limiting across multiple instances
- Falls back to thread-safe in-memory storage for single-instance deployments
- Returns proper 429 responses with Retry-After headers
- Integrates with the existing quota service for tier detection

Usage:
    @router.post("/generate-blog")
    async def generate_blog(
        request: Request,
        user_id: str = Depends(verify_api_key),
        _: None = Depends(rate_limit)
    ):
        ...
"""

import asyncio
import logging
import os
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.types.usage import SubscriptionTier
from src.usage.quota_service import get_quota_service

from ..auth import verify_api_key

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class TierRateLimits:
    """Rate limits for a subscription tier."""

    per_minute: int
    per_hour: int

    def __post_init__(self):
        """Validate limits."""
        if self.per_minute <= 0:
            raise ValueError("per_minute must be positive")
        if self.per_hour <= 0:
            raise ValueError("per_hour must be positive")
        if self.per_hour < self.per_minute:
            raise ValueError("per_hour must be >= per_minute")


# Tier-based rate limits configuration
# These are request rate limits, separate from the quota (generation) limits
TIER_RATE_LIMITS: Dict[SubscriptionTier, TierRateLimits] = {
    SubscriptionTier.FREE: TierRateLimits(per_minute=10, per_hour=100),
    SubscriptionTier.STARTER: TierRateLimits(per_minute=30, per_hour=500),
    SubscriptionTier.PRO: TierRateLimits(per_minute=60, per_hour=2000),
    SubscriptionTier.BUSINESS: TierRateLimits(per_minute=120, per_hour=10000),
}

# Default limits for unknown tiers
DEFAULT_RATE_LIMITS = TierRateLimits(per_minute=10, per_hour=100)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    window: str  # "minute" or "hour"
    retry_after: Optional[int] = None  # Seconds until reset, if blocked


class RateLimitExceededError(BaseModel):
    """
    Error response when rate limit is exceeded.

    Returned with 429 Too Many Requests status.
    """

    success: bool = False
    error: str
    error_code: str = "RATE_LIMIT_EXCEEDED"
    limit: int
    remaining: int = 0
    reset_at: int
    retry_after: int
    window: str
    tier: str
    upgrade_url: str = "/pricing"


class RateLimitException(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        result: RateLimitResult,
        tier: SubscriptionTier,
        limits: TierRateLimits,
    ):
        error_response = RateLimitExceededError(
            error=f"Rate limit exceeded. Maximum {result.limit} requests per {result.window}.",
            limit=result.limit,
            remaining=0,
            reset_at=result.reset_at,
            retry_after=result.retry_after or 60,
            window=result.window,
            tier=tier.value,
        )

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_response.model_dump(),
            headers={
                "Retry-After": str(result.retry_after or 60),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(result.reset_at),
            },
        )


# =============================================================================
# Backend Implementations
# =============================================================================


class RateLimitBackend(ABC):
    """Abstract base class for rate limit storage backends."""

    @abstractmethod
    async def record_request(
        self, key: str, timestamp: float, window_seconds: int
    ) -> Tuple[int, float]:
        """
        Record a request and return the count within the window.

        Args:
            key: Unique identifier for the rate limit bucket.
            timestamp: Current Unix timestamp.
            window_seconds: Size of the sliding window in seconds.

        Returns:
            Tuple of (count within window, oldest timestamp in window).
        """
        pass

    @abstractmethod
    async def get_request_count(
        self, key: str, timestamp: float, window_seconds: int
    ) -> int:
        """
        Get the current request count within the window without recording.

        Args:
            key: Unique identifier for the rate limit bucket.
            timestamp: Current Unix timestamp.
            window_seconds: Size of the sliding window in seconds.

        Returns:
            Number of requests within the window.
        """
        pass

    @abstractmethod
    async def cleanup(self, key: str, timestamp: float, window_seconds: int) -> None:
        """
        Remove expired entries from the window.

        Args:
            key: Unique identifier for the rate limit bucket.
            timestamp: Current Unix timestamp.
            window_seconds: Size of the sliding window in seconds.
        """
        pass


class InMemoryBackend(RateLimitBackend):
    """
    Thread-safe in-memory rate limit backend.

    Uses a sliding window log algorithm with periodic cleanup.
    Suitable for single-instance deployments or development.
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Initialize the in-memory backend.

        Args:
            cleanup_interval: Seconds between automatic cleanup runs.
        """
        self._storage: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def _maybe_cleanup_all(self, current_time: float) -> None:
        """Periodically clean up all expired entries."""
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._last_cleanup = current_time
            # Clean up entries older than 1 hour (max window)
            cutoff = current_time - 3600
            keys_to_remove = []

            for key, timestamps in self._storage.items():
                self._storage[key] = [t for t in timestamps if t > cutoff]
                if not self._storage[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._storage[key]

            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit keys")

    async def record_request(
        self, key: str, timestamp: float, window_seconds: int
    ) -> Tuple[int, float]:
        """Record a request and return count within window."""
        with self._lock:
            self._maybe_cleanup_all(timestamp)

            if key not in self._storage:
                self._storage[key] = []

            # Remove expired entries for this key
            cutoff = timestamp - window_seconds
            self._storage[key] = [t for t in self._storage[key] if t > cutoff]

            # Add current request
            self._storage[key].append(timestamp)

            count = len(self._storage[key])
            oldest = self._storage[key][0] if self._storage[key] else timestamp

            return count, oldest

    async def get_request_count(
        self, key: str, timestamp: float, window_seconds: int
    ) -> int:
        """Get request count within window without recording."""
        with self._lock:
            if key not in self._storage:
                return 0

            cutoff = timestamp - window_seconds
            valid_requests = [t for t in self._storage[key] if t > cutoff]
            return len(valid_requests)

    async def cleanup(self, key: str, timestamp: float, window_seconds: int) -> None:
        """Remove expired entries for a key."""
        with self._lock:
            if key in self._storage:
                cutoff = timestamp - window_seconds
                self._storage[key] = [t for t in self._storage[key] if t > cutoff]


class RedisBackend(RateLimitBackend):
    """
    Redis-based rate limit backend for distributed deployments.

    Uses sorted sets with timestamp scores for efficient sliding window.
    Automatically handles connection failures with graceful degradation.
    """

    def __init__(self, redis_url: str, key_prefix: str = "ratelimit:"):
        """
        Initialize the Redis backend.

        Args:
            redis_url: Redis connection URL.
            key_prefix: Prefix for all rate limit keys.
        """
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._client = None
        self._connected = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Redis client."""
        try:
            import redis.asyncio as redis

            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            self._connected = True
            logger.info("Redis rate limit backend initialized")
        except ImportError:
            logger.warning("redis package not installed, Redis backend unavailable")
            self._connected = False
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self._connected = False

    def _get_key(self, key: str) -> str:
        """Get the full Redis key with prefix."""
        return f"{self._key_prefix}{key}"

    async def record_request(
        self, key: str, timestamp: float, window_seconds: int
    ) -> Tuple[int, float]:
        """Record a request using Redis sorted set."""
        if not self._connected or not self._client:
            raise ConnectionError("Redis not connected")

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds

        try:
            # Use pipeline for atomic operations
            async with self._client.pipeline(transaction=True) as pipe:
                # Remove expired entries
                pipe.zremrangebyscore(redis_key, "-inf", cutoff)
                # Add current request with timestamp as score
                pipe.zadd(redis_key, {str(timestamp): timestamp})
                # Get count of entries in window
                pipe.zcard(redis_key)
                # Get oldest entry
                pipe.zrange(redis_key, 0, 0, withscores=True)
                # Set expiry on the key (window + buffer)
                pipe.expire(redis_key, window_seconds + 60)

                results = await pipe.execute()

            count = results[2]
            oldest_entries = results[3]
            oldest = oldest_entries[0][1] if oldest_entries else timestamp

            return count, oldest

        except Exception as e:
            logger.error(f"Redis error recording request: {e}")
            raise

    async def get_request_count(
        self, key: str, timestamp: float, window_seconds: int
    ) -> int:
        """Get request count from Redis sorted set."""
        if not self._connected or not self._client:
            raise ConnectionError("Redis not connected")

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds

        try:
            # Count entries with score > cutoff
            count = await self._client.zcount(redis_key, cutoff, "+inf")
            return count
        except Exception as e:
            logger.error(f"Redis error getting request count: {e}")
            raise

    async def cleanup(self, key: str, timestamp: float, window_seconds: int) -> None:
        """Remove expired entries from Redis sorted set."""
        if not self._connected or not self._client:
            return

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds

        try:
            await self._client.zremrangebyscore(redis_key, "-inf", cutoff)
        except Exception as e:
            logger.warning(f"Redis cleanup error: {e}")


# =============================================================================
# Rate Limiter
# =============================================================================


class RateLimiter:
    """
    Production rate limiter with tier-based limits and automatic backend selection.

    Implements sliding window log algorithm for accurate rate limiting.
    Checks both per-minute and per-hour limits.
    """

    def __init__(
        self,
        backend: Optional[RateLimitBackend] = None,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            backend: Optional backend override.
            redis_url: Optional Redis URL. If not provided, checks REDIS_URL env var.
        """
        self._backend: Optional[RateLimitBackend] = backend
        self._fallback_backend: Optional[InMemoryBackend] = None

        if self._backend is None:
            self._init_backend(redis_url)

    def _init_backend(self, redis_url: Optional[str] = None) -> None:
        """Initialize the appropriate backend."""
        url = redis_url or os.environ.get("REDIS_URL")

        if url:
            try:
                self._backend = RedisBackend(url)
                logger.info("Rate limiter using Redis backend")
            except Exception as e:
                logger.warning(f"Failed to init Redis backend: {e}, using in-memory")
                self._backend = InMemoryBackend()
        else:
            self._backend = InMemoryBackend()
            logger.info("Rate limiter using in-memory backend")

        # Keep a fallback ready for Redis failures
        self._fallback_backend = InMemoryBackend()

    async def _check_window(
        self,
        user_id: str,
        window_name: str,
        window_seconds: int,
        limit: int,
    ) -> RateLimitResult:
        """
        Check rate limit for a specific time window.

        Args:
            user_id: The user identifier.
            window_name: Window identifier (e.g., "minute", "hour").
            window_seconds: Window size in seconds.
            limit: Maximum requests allowed in window.

        Returns:
            RateLimitResult with current status.
        """
        now = time.time()
        key = f"{user_id}:{window_name}"

        try:
            count, oldest = await self._backend.record_request(key, now, window_seconds)
        except Exception as e:
            logger.warning(f"Backend error, using fallback: {e}")
            count, oldest = await self._fallback_backend.record_request(
                key, now, window_seconds
            )

        remaining = max(0, limit - count)
        reset_at = int(oldest + window_seconds)

        if count > limit:
            retry_after = max(1, reset_at - int(now))
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                window=window_name,
                retry_after=retry_after,
            )

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            window=window_name,
        )

    async def check_rate_limit(
        self,
        user_id: str,
        tier: SubscriptionTier,
    ) -> RateLimitResult:
        """
        Check rate limits for a user based on their tier.

        Checks both per-minute and per-hour limits, returning the most
        restrictive result.

        Args:
            user_id: The user identifier.
            tier: The user's subscription tier.

        Returns:
            RateLimitResult. If allowed is False, includes retry_after.
        """
        limits = TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMITS)

        # Check per-minute limit first (more likely to be hit)
        minute_result = await self._check_window(
            user_id=user_id,
            window_name="minute",
            window_seconds=60,
            limit=limits.per_minute,
        )

        if not minute_result.allowed:
            return minute_result

        # Check per-hour limit
        hour_result = await self._check_window(
            user_id=user_id,
            window_name="hour",
            window_seconds=3600,
            limit=limits.per_hour,
        )

        if not hour_result.allowed:
            return hour_result

        # Return minute result (has more relevant remaining/reset info)
        return minute_result

    async def get_current_usage(
        self,
        user_id: str,
        tier: SubscriptionTier,
    ) -> Dict[str, Dict]:
        """
        Get current usage without recording a request.

        Useful for displaying rate limit status to users.

        Args:
            user_id: The user identifier.
            tier: The user's subscription tier.

        Returns:
            Dictionary with minute and hour usage statistics.
        """
        now = time.time()
        limits = TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMITS)

        try:
            minute_count = await self._backend.get_request_count(
                f"{user_id}:minute", now, 60
            )
            hour_count = await self._backend.get_request_count(
                f"{user_id}:hour", now, 3600
            )
        except Exception:
            minute_count = await self._fallback_backend.get_request_count(
                f"{user_id}:minute", now, 60
            )
            hour_count = await self._fallback_backend.get_request_count(
                f"{user_id}:hour", now, 3600
            )

        return {
            "minute": {
                "used": minute_count,
                "limit": limits.per_minute,
                "remaining": max(0, limits.per_minute - minute_count),
            },
            "hour": {
                "used": hour_count,
                "limit": limits.per_hour,
                "remaining": max(0, limits.per_hour - hour_count),
            },
        }


# =============================================================================
# Singleton and Dependency
# =============================================================================


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit(
    request: Request,
    user_id: str = Depends(verify_api_key),
) -> str:
    """
    FastAPI dependency that enforces rate limits.

    This dependency should be added to endpoints to prevent abuse.
    Rate limits are based on the user's subscription tier.

    Args:
        request: The FastAPI request object.
        user_id: The authenticated user ID from API key verification.

    Returns:
        The user_id if rate limit check passes.

    Raises:
        HTTPException: 429 Too Many Requests if rate limit is exceeded.

    Usage:
        @router.post("/generate-blog")
        async def generate_blog(
            request: Request,
            user_id: str = Depends(rate_limit)
        ):
            # Will only reach here if under rate limit
            ...
    """
    limiter = get_rate_limiter()
    quota_service = get_quota_service()

    # Get user's tier from quota service
    try:
        usage_stats = await quota_service.get_usage_stats(user_id)
        tier = usage_stats.tier
    except Exception as e:
        logger.warning(f"Failed to get user tier, using FREE: {e}")
        tier = SubscriptionTier.FREE

    # Check rate limit
    result = await limiter.check_rate_limit(user_id, tier)

    if not result.allowed:
        limits = TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMITS)
        logger.warning(
            f"Rate limit exceeded for user {user_id[:8]}... "
            f"({tier.value}): {result.limit}/{result.window}"
        )
        raise RateLimitException(result, tier, limits)

    # Add rate limit headers to response state for middleware to pick up
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_at),
    }

    logger.debug(
        f"Rate limit check passed for {user_id[:8]}...: "
        f"{result.remaining}/{result.limit} remaining ({result.window})"
    )

    return user_id


async def rate_limit_soft(
    request: Request,
    user_id: str = Depends(verify_api_key),
) -> Tuple[str, bool, Optional[RateLimitResult]]:
    """
    Soft rate limit check that returns status instead of raising exception.

    Useful for endpoints that want to warn users about rate limits
    without blocking the request.

    Args:
        request: The FastAPI request object.
        user_id: The authenticated user ID.

    Returns:
        Tuple of (user_id, is_within_limit, rate_limit_result).
    """
    limiter = get_rate_limiter()
    quota_service = get_quota_service()

    try:
        usage_stats = await quota_service.get_usage_stats(user_id)
        tier = usage_stats.tier
    except Exception:
        tier = SubscriptionTier.FREE

    result = await limiter.check_rate_limit(user_id, tier)
    return user_id, result.allowed, result


async def get_rate_limit_status(
    user_id: str = Depends(verify_api_key),
) -> Dict[str, Dict]:
    """
    Get current rate limit status for a user.

    Useful for displaying rate limit info in API responses.

    Args:
        user_id: The authenticated user ID.

    Returns:
        Dictionary with minute and hour usage statistics.
    """
    limiter = get_rate_limiter()
    quota_service = get_quota_service()

    try:
        usage_stats = await quota_service.get_usage_stats(user_id)
        tier = usage_stats.tier
    except Exception:
        tier = SubscriptionTier.FREE

    return await limiter.get_current_usage(user_id, tier)
