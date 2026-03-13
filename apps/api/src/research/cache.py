"""
Simple in-memory TTL cache for research results.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """Thread-safe TTL cache with a max size."""

    def __init__(self, max_entries: int, ttl_seconds: int) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._data: Dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            if entry.expires_at < now:
                self._data.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        expires_at = now + self._ttl_seconds
        with self._lock:
            if len(self._data) >= self._max_entries:
                # Drop expired entries first, then oldest by expiry.
                self._prune(now)
                if len(self._data) >= self._max_entries:
                    oldest_key = min(
                        self._data, key=lambda k: self._data[k].expires_at
                    )
                    self._data.pop(oldest_key, None)
            self._data[key] = _CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def _prune(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        expired = [k for k, v in self._data.items() if v.expires_at < now]
        for key in expired:
            self._data.pop(key, None)


_cache_instance: Optional[TTLCache] = None


def get_research_cache() -> TTLCache:
    """Get the singleton research cache instance."""
    global _cache_instance
    if _cache_instance is None:
        ttl = int(os.environ.get("RESEARCH_CACHE_TTL_SECONDS", "3600"))
        max_entries = int(os.environ.get("RESEARCH_CACHE_MAX_ENTRIES", "128"))
        _cache_instance = TTLCache(max_entries=max_entries, ttl_seconds=ttl)
    return _cache_instance


def clear_research_cache() -> None:
    """Clear the research cache (used during shutdown)."""
    cache = get_research_cache()
    cache.clear()
