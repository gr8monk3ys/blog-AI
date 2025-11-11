"""Caching utilities for blog-AI.

Provides response caching for LLM providers to reduce API calls
and improve performance for repeated requests.
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL (time to live in seconds)."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all values from cache."""
        pass

    @abstractmethod
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend using a dictionary.

    Simple and fast, but data is lost when process ends.
    Good for development and single-process applications.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries (default: 1000)
        """
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key not in self._cache:
            self._misses += 1
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if expiry is not None and time.time() > expiry:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL."""
        # Evict oldest entry if cache is full
        if len(self._cache) >= self._max_size and key not in self._cache:
            # Simple FIFO eviction
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1
            logger.debug(f"Evicted cache entry: {oldest_key}")

        expiry = time.time() + ttl if ttl else None
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all values from cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


class CacheManager:
    """Manages caching for LLM responses.

    Generates cache keys based on prompt, model, and parameters,
    and handles getting/setting cached responses.
    """

    def __init__(
        self,
        backend: CacheBackend | None = None,
        enabled: bool = True,
        default_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize cache manager.

        Args:
            backend: Cache backend to use (default: MemoryCache)
            enabled: Whether caching is enabled (default: True)
            default_ttl: Default TTL in seconds (default: 3600)
        """
        self._backend = backend or MemoryCache()
        self._enabled = enabled
        self._default_ttl = default_ttl

    def generate_key(
        self,
        prompt: str,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate cache key from prompt and parameters.

        Args:
            prompt: The input prompt
            model: Model name
            temperature: Temperature setting
            max_tokens: Max tokens setting
            **kwargs: Additional parameters

        Returns:
            Cache key (hex digest)
        """
        # Create deterministic key from parameters
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Sort keys for consistent ordering
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()

        return f"llm:{model}:{key_hash[:16]}"

    def get(self, key: str) -> Any | None:
        """Get cached response."""
        if not self._enabled:
            return None

        value = self._backend.get(key)
        if value is not None:
            logger.debug(f"Cache hit: {key}")
        else:
            logger.debug(f"Cache miss: {key}")

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached response."""
        if not self._enabled:
            return

        ttl = ttl if ttl is not None else self._default_ttl
        self._backend.set(key, value, ttl)
        logger.debug(f"Cached response: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> None:
        """Delete cached response."""
        self._backend.delete(key)

    def clear(self) -> None:
        """Clear all cached responses."""
        self._backend.clear()

    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True
        logger.info("Cache enabled")

    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False
        logger.info("Cache disabled")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = self._backend.stats()
        stats["enabled"] = self._enabled
        stats["default_ttl"] = self._default_ttl
        return stats

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled


# Global cache manager instance (can be replaced with custom backend)
_default_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get the default cache manager instance."""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager()
    return _default_cache_manager


def set_cache_manager(manager: CacheManager) -> None:
    """Set a custom cache manager instance."""
    global _default_cache_manager
    _default_cache_manager = manager
