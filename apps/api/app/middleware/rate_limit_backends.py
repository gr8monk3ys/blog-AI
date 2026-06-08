"""
Rate limiter storage backends.

Defines the backend abstraction and two implementations:
- ``InMemoryBackend``: thread-safe sliding-window log for single-instance/dev.
- ``RedisBackend``: distributed sliding window using Redis sorted sets.

Extracted from rate_limit.py to keep the middleware module focused on policy
and dependency wiring (see docs/REMEDIATION_PLAN.md P2.2).
"""

import logging
import random
import threading
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


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
                logger.debug(
                    f"Cleaned up {len(keys_to_remove)} expired rate limit keys"
                )

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

    Uses sorted sets with timestamp scores for efficient sliding window
    rate limiting. Each request is stored as a unique member (timestamp +
    random suffix) with the timestamp as the score, ensuring concurrent
    requests within the same microsecond are counted separately.

    Reuses the project's singleton RedisClient from src.storage.redis_client
    for connection pooling, health checks, and reconnection support.
    Falls back gracefully when Redis is unavailable.
    """

    def __init__(self, redis_url: str, key_prefix: str = "ratelimit:"):
        """
        Initialize the Redis backend.

        Args:
            redis_url: Redis connection URL (used only if the singleton
                       RedisClient has not been initialised yet).
            key_prefix: Prefix for all rate limit keys in Redis.
        """
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._connected = False
        self._connection_verified = False

    def _get_key(self, key: str) -> str:
        """Get the full Redis key with prefix."""
        return f"{self._key_prefix}{key}"

    async def _get_client(self):
        """
        Get a live Redis client, verifying the connection on first use.

        Returns:
            An async Redis client instance.

        Raises:
            ConnectionError: If Redis is not available.
        """
        from src.storage.redis_client import redis_client

        client = await redis_client.get_client()
        if client is None:
            self._connected = False
            raise ConnectionError("Redis not available")

        if not self._connection_verified:
            try:
                await client.ping()
                self._connected = True
                self._connection_verified = True
                logger.info("Redis rate limit backend connection verified")
            except Exception as e:
                self._connected = False
                raise ConnectionError(f"Redis ping failed: {e}") from e

        return client

    @staticmethod
    def _unique_member(timestamp: float) -> str:
        """
        Generate a unique sorted-set member for a request.

        Using only the timestamp string as the member causes silent
        overwrites when two requests share the same timestamp (sorted
        set members must be unique).  Appending a random suffix avoids
        this collision while keeping the score as the real timestamp for
        window queries.
        """
        import uuid

        return f"{timestamp}:{uuid.uuid4().hex[:8]}"

    async def record_request(
        self, key: str, timestamp: float, window_seconds: int
    ) -> Tuple[int, float]:
        """Record a request using Redis sorted set."""
        client = await self._get_client()

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds
        member = self._unique_member(timestamp)

        try:
            # Use pipeline for atomic operations
            async with client.pipeline(transaction=True) as pipe:
                # Remove expired entries
                pipe.zremrangebyscore(redis_key, "-inf", cutoff)
                # Add current request – unique member, timestamp as score
                pipe.zadd(redis_key, {member: timestamp})
                # Get count of entries in window
                pipe.zcard(redis_key)
                # Get oldest entry
                pipe.zrange(redis_key, 0, 0, withscores=True)
                # Set TTL on the key (window + buffer)
                pipe.expire(redis_key, window_seconds + 60)

                results = await pipe.execute()

            count = results[2]
            oldest_entries = results[3]
            oldest = oldest_entries[0][1] if oldest_entries else timestamp

            return count, oldest

        except Exception as e:
            self._connection_verified = False
            self._connected = False
            logger.error(f"Redis error recording request: {e}")
            raise

    async def get_request_count(
        self, key: str, timestamp: float, window_seconds: int
    ) -> int:
        """Get request count from Redis sorted set."""
        client = await self._get_client()

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds

        try:
            # Count entries with score > cutoff
            count = await client.zcount(redis_key, cutoff, "+inf")
            return count
        except Exception as e:
            self._connection_verified = False
            self._connected = False
            logger.error(f"Redis error getting request count: {e}")
            raise

    async def cleanup(self, key: str, timestamp: float, window_seconds: int) -> None:
        """Remove expired entries from Redis sorted set."""
        try:
            client = await self._get_client()
        except ConnectionError:
            return

        redis_key = self._get_key(key)
        cutoff = timestamp - window_seconds

        try:
            await client.zremrangebyscore(redis_key, "-inf", cutoff)
        except Exception as e:
            self._connection_verified = False
            self._connected = False
            logger.warning(f"Redis cleanup error: {e}")
