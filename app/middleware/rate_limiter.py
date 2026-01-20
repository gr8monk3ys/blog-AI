"""
Rate limiting middleware to prevent abuse and control API costs.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Set

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


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

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, ip: str, current_time: float) -> None:
        """Remove requests outside the current time window."""
        cutoff = current_time - self.window_seconds
        self.request_counts[ip] = [t for t in self.request_counts[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, current_time)

        # Determine rate limit based on endpoint
        is_generation = request.url.path in self.generation_endpoints
        limit = self.generation_limit if is_generation else self.general_limit

        # Check if over limit
        if len(self.request_counts[client_ip]) >= limit:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, endpoint: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute for this endpoint.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record this request
        self.request_counts[client_ip].append(current_time)

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = limit - len(self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )

        return response
