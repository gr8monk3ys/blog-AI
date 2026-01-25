"""
Rate limiting middleware to prevent abuse and control API costs.
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Dict, List, Set

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Default configuration for memory management
DEFAULT_MAX_TRACKED_IPS = 100000  # Maximum IPs to track (prevents DoS via IP exhaustion)
DEFAULT_CLEANUP_INTERVAL = 60  # Seconds between full cleanup runs


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse and control API costs.

    Limits:
    - Configurable requests per minute per IP for general endpoints
    - Configurable requests per minute per IP for generation endpoints (expensive LLM calls)
    """

    def __init__(
        self,
        app,
        general_limit: int = 60,
        generation_limit: int = 10,
        window_seconds: int = 60,
        generation_endpoints: Set[str] = None,
        exclude_paths: Set[str] = None,
        max_tracked_ips: int = DEFAULT_MAX_TRACKED_IPS,
        cleanup_interval: int = DEFAULT_CLEANUP_INTERVAL,
    ):
        """
        Initialize the rate limiter.

        Args:
            app: The FastAPI application.
            general_limit: Maximum requests per minute for general endpoints.
            generation_limit: Maximum requests per minute for generation endpoints.
            window_seconds: Time window in seconds for rate limiting.
            generation_endpoints: Set of paths that are considered generation endpoints.
            exclude_paths: Set of paths to exclude from rate limiting.
            max_tracked_ips: Maximum number of IPs to track (prevents memory exhaustion).
            cleanup_interval: Seconds between periodic cleanup of expired entries.
        """
        super().__init__(app)
        self.general_limit = general_limit
        self.generation_limit = generation_limit
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.generation_endpoints = generation_endpoints or {
            "/generate-blog",
            "/generate-book",
            "/api/v1/generate-blog",
            "/api/v1/generate-book",
        }
        self.exclude_paths = exclude_paths or {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

        # Memory leak prevention settings
        self.max_tracked_ips = max_tracked_ips
        self.cleanup_interval = cleanup_interval
        self._lock = threading.RLock()
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, ip: str, current_time: float) -> None:
        """Remove requests outside the current time window for a specific IP."""
        cutoff = current_time - self.window_seconds
        with self._lock:
            if ip in self.request_counts:
                self.request_counts[ip] = [
                    t for t in self.request_counts[ip] if t > cutoff
                ]
                # Remove entry completely if empty to prevent memory leak
                if not self.request_counts[ip]:
                    del self.request_counts[ip]

    def _cleanup_expired_entries(self, current_time: float) -> None:
        """
        Periodically clean up all expired entries to prevent memory leak.

        This method runs at most once per cleanup_interval to avoid performance
        impact on every request.
        """
        # Check if cleanup is needed (without lock for quick check)
        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        with self._lock:
            # Double-check after acquiring lock
            if current_time - self._last_cleanup < self.cleanup_interval:
                return

            cutoff = current_time - self.window_seconds
            expired_keys = []

            # Find and clean all entries
            for ip, timestamps in self.request_counts.items():
                # Filter old timestamps
                valid_timestamps = [t for t in timestamps if t > cutoff]
                if valid_timestamps:
                    self.request_counts[ip] = valid_timestamps
                else:
                    expired_keys.append(ip)

            # Remove empty entries
            for ip in expired_keys:
                del self.request_counts[ip]

            if expired_keys:
                logger.debug(
                    f"Rate limiter cleanup: removed {len(expired_keys)} expired entries, "
                    f"{len(self.request_counts)} active IPs remaining"
                )

            self._last_cleanup = current_time

    def _enforce_ip_limit(self, current_time: float) -> None:
        """
        Enforce maximum tracked IPs to prevent DoS via IP exhaustion.

        When the limit is exceeded, removes the oldest entries (those with
        the earliest last request timestamp).
        """
        with self._lock:
            if len(self.request_counts) <= self.max_tracked_ips:
                return

            # Calculate how many entries to remove
            excess = len(self.request_counts) - self.max_tracked_ips

            # Sort IPs by their most recent request timestamp (oldest first)
            sorted_ips = sorted(
                self.request_counts.keys(),
                key=lambda ip: max(self.request_counts[ip]) if self.request_counts[ip] else 0,
            )

            # Remove the oldest entries
            for ip in sorted_ips[:excess]:
                del self.request_counts[ip]

            logger.warning(
                f"Rate limiter IP limit enforced: removed {excess} oldest entries, "
                f"limit is {self.max_tracked_ips}"
            )

    def get_stats(self) -> Dict[str, int]:
        """
        Get current rate limiter statistics for monitoring.

        Returns:
            Dictionary with tracked_ips count and total_requests count.
        """
        with self._lock:
            total_requests = sum(len(ts) for ts in self.request_counts.values())
            return {
                "tracked_ips": len(self.request_counts),
                "total_requests": total_requests,
                "max_tracked_ips": self.max_tracked_ips,
            }

    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Perform periodic cleanup of all expired entries
        self._cleanup_expired_entries(current_time)

        # Clean old requests for this specific IP
        self._clean_old_requests(client_ip, current_time)

        # Determine rate limit based on endpoint
        is_generation = request.url.path in self.generation_endpoints
        limit = self.generation_limit if is_generation else self.general_limit

        # Check if over limit (thread-safe read)
        with self._lock:
            current_count = len(self.request_counts.get(client_ip, []))

        if current_count >= limit:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, endpoint: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute for this endpoint.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record this request (thread-safe write)
        with self._lock:
            self.request_counts[client_ip].append(current_time)
            current_count = len(self.request_counts[client_ip])

        # Enforce IP limit to prevent memory exhaustion from DoS attacks
        self._enforce_ip_limit(current_time)

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = limit - current_count
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )

        return response
