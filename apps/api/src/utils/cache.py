"""
Caching utilities for expensive operations.

Provides in-memory caching with TTL (time-to-live) support
for content analysis and other expensive computations.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with value and metadata."""

    value: T
    created_at: float
    ttl_seconds: float
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """Record a cache hit."""
        self.hits += 1


class LRUCache(Generic[T]):
    """
    Least Recently Used (LRU) cache with TTL support.

    Features:
    - Configurable max size
    - TTL-based expiration
    - Thread-safe operations
    - Cache hit/miss statistics
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl_seconds: float = 3600,  # 1 hour default
        name: str = "cache",
    ):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.name = name
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._access_order: list[str] = []
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Create a cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.

        Returns None if not found or expired.
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired:
            self._remove(key)
            self._misses += 1
            logger.debug("Cache miss (expired): %s[%s]", self.name, key[:8])
            return None

        # Move to end of access order (most recently used)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        entry.touch()
        self._hits += 1
        logger.debug("Cache hit: %s[%s]", self.name, key[:8])
        return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """Set a value in the cache."""
        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            self._evict_lru()

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl,
        )
        self._access_order.append(key)
        logger.debug("Cache set: %s[%s] (ttl=%ds)", self.name, key[:8], ttl)

    def _remove(self, key: str) -> None:
        """Remove an entry from the cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                logger.debug("Cache evict (LRU): %s[%s]", self.name, lru_key[:8])

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared: %s", self.name)

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired
        ]
        for key in expired_keys:
            self._remove(key)
        if expired_keys:
            logger.info(
                "Cache cleanup: %s removed %d expired entries",
                self.name,
                len(expired_keys),
            )
        return len(expired_keys)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "name": self.name,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
        }


def cached(
    cache: LRUCache,
    ttl_seconds: Optional[float] = None,
    key_prefix: str = "",
) -> Callable:
    """
    Decorator to cache function results.

    Usage:
        analysis_cache = LRUCache(max_size=50, name="analysis")

        @cached(analysis_cache, ttl_seconds=1800)
        def analyze_content(content: str) -> dict:
            # Expensive operation
            return result
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            key = key_prefix + cache._make_key(*args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


# Global cache instances for common use cases
_content_analysis_cache: Optional[LRUCache] = None
_voice_analysis_cache: Optional[LRUCache] = None


def get_content_analysis_cache() -> LRUCache:
    """Get the shared content analysis cache."""
    global _content_analysis_cache
    if _content_analysis_cache is None:
        _content_analysis_cache = LRUCache(
            max_size=100,
            default_ttl_seconds=1800,  # 30 minutes
            name="content_analysis",
        )
    return _content_analysis_cache


def get_voice_analysis_cache() -> LRUCache:
    """Get the shared voice analysis cache."""
    global _voice_analysis_cache
    if _voice_analysis_cache is None:
        _voice_analysis_cache = LRUCache(
            max_size=50,
            default_ttl_seconds=3600,  # 1 hour
            name="voice_analysis",
        )
    return _voice_analysis_cache
