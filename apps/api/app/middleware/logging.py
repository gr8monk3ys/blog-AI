"""
Request logging middleware for Blog AI.

Provides:
- Automatic request/response logging
- Request ID generation and propagation
- Response time tracking
- Health check endpoint exclusion
- Correlation ID support for distributed tracing
"""

import logging
import time
import uuid
from typing import Callable, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import (
    clear_request_context,
    get_request_id,
    set_request_context,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging.

    Features:
    - Generates unique request IDs for tracing
    - Logs request method, path, status code, and response time
    - Extracts user ID from authenticated requests
    - Excludes health check endpoints from verbose logging
    - Adds X-Request-ID and X-Response-Time headers to responses
    - Supports correlation IDs for distributed tracing
    """

    # Paths to exclude from verbose logging (health checks, docs, etc.)
    DEFAULT_EXCLUDE_PATHS: Set[str] = frozenset({
        "/",
        "/health",
        "/health/db",
        "/health/stripe",
        "/health/sentry",
        "/health/cache",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    })

    # Paths that should only log errors (never INFO)
    ERROR_ONLY_PATHS: Set[str] = frozenset({
        "/health",
        "/health/db",
        "/health/stripe",
        "/health/sentry",
        "/health/cache",
    })

    def __init__(
        self,
        app,
        exclude_paths: Optional[Set[str]] = None,
        error_only_paths: Optional[Set[str]] = None,
    ):
        """
        Initialize the request logging middleware.

        Args:
            app: The FastAPI/Starlette application
            exclude_paths: Paths to completely exclude from logging
            error_only_paths: Paths to only log on errors
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or self.DEFAULT_EXCLUDE_PATHS
        self.error_only_paths = error_only_paths or self.ERROR_ONLY_PATHS

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())

    def _get_request_id(self, request: Request) -> str:
        """
        Get or generate request ID.

        Checks for existing request ID from upstream proxy/load balancer,
        otherwise generates a new one.
        """
        # Check for existing request ID from upstream
        request_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Request-Id")
            or request.headers.get("X-Amzn-Trace-Id")  # AWS ALB
            or self._generate_request_id()
        )
        return request_id

    def _get_correlation_id(self, request: Request) -> Optional[str]:
        """Get correlation ID from request headers."""
        return (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Correlation-Id")
        )

    def _get_user_id(self, request: Request) -> str:
        """
        Extract user ID from request if available.

        Checks request state (set by auth middleware) first,
        then falls back to API key identification.
        """
        # Check for user ID set by auth middleware
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return str(user_id)

        # Check for authenticated user object
        user = getattr(request.state, "user", None)
        if user:
            user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
            if user_id:
                return str(user_id)

        # Check for API key based identification
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Return truncated key for privacy (first 8 chars)
            return f"key:{api_key[:8]}..."

        return "-"

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address, handling proxy headers.

        Checks X-Forwarded-For and X-Real-IP headers commonly set
        by reverse proxies and load balancers.
        """
        # Check X-Forwarded-For (may contain multiple IPs)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def _should_log(self, path: str, status_code: int) -> bool:
        """
        Determine if request should be logged.

        Args:
            path: Request path
            status_code: Response status code

        Returns:
            True if request should be logged
        """
        # Never log completely excluded paths
        if path in self.exclude_paths:
            return False

        # For error-only paths, only log on errors
        if path in self.error_only_paths:
            return status_code >= 400

        return True

    def _get_log_level(self, status_code: int) -> int:
        """
        Determine log level based on status code.

        Args:
            status_code: HTTP response status code

        Returns:
            Appropriate logging level
        """
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        else:
            return logging.INFO

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging.

        Wraps request handling with timing, context setup, and logging.
        """
        # Generate/get request identifiers
        request_id = self._get_request_id(request)
        correlation_id = self._get_correlation_id(request)

        # Set request context for all loggers in this async context
        set_request_context(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id
        if correlation_id:
            request.state.correlation_id = correlation_id

        # Capture request details
        method = request.method
        path = request.url.path
        query_string = str(request.query_params) if request.query_params else ""
        client_ip = self._get_client_ip(request)

        # Start timing
        start_time = time.perf_counter()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate response time
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Get user ID after auth middleware has processed
            user_id = self._get_user_id(request)
            set_request_context(user_id=user_id)

            # Add tracing headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            if correlation_id:
                response.headers["X-Correlation-ID"] = correlation_id

            # Log completed request
            if self._should_log(path, response.status_code):
                log_level = self._get_log_level(response.status_code)
                logger.log(
                    log_level,
                    f"{method} {path} {response.status_code} ({duration_ms:.2f}ms)",
                    extra={
                        "event": "http_request",
                        "http_method": method,
                        "http_path": path,
                        "http_query": query_string,
                        "http_status": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "client_ip": client_ip,
                        "user_agent": request.headers.get("User-Agent", "-"),
                    },
                )

            return response

        except Exception as exc:
            # Calculate response time even for errors
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log the error
            logger.error(
                f"{method} {path} FAILED ({duration_ms:.2f}ms): {type(exc).__name__}",
                extra={
                    "event": "http_request_error",
                    "http_method": method,
                    "http_path": path,
                    "http_query": query_string,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:200],  # Truncate for safety
                },
                exc_info=True,
            )

            # Re-raise to let FastAPI handle the error
            raise

        finally:
            # Clear request context
            clear_request_context()


def get_request_logging_middleware(
    exclude_paths: Optional[Set[str]] = None,
    error_only_paths: Optional[Set[str]] = None,
) -> type:
    """
    Factory function to create configured logging middleware.

    This allows customizing the middleware configuration while still
    using the class-based middleware pattern that FastAPI expects.

    Args:
        exclude_paths: Additional paths to exclude from logging
        error_only_paths: Additional paths to only log on errors

    Returns:
        Configured RequestLoggingMiddleware class

    Usage:
        ConfiguredMiddleware = get_request_logging_middleware(
            exclude_paths={"/metrics", "/internal/health"}
        )
        app.add_middleware(ConfiguredMiddleware)
    """
    combined_exclude = RequestLoggingMiddleware.DEFAULT_EXCLUDE_PATHS
    if exclude_paths:
        combined_exclude = combined_exclude | exclude_paths

    combined_error_only = RequestLoggingMiddleware.ERROR_ONLY_PATHS
    if error_only_paths:
        combined_error_only = combined_error_only | error_only_paths

    class ConfiguredLoggingMiddleware(RequestLoggingMiddleware):
        """Pre-configured logging middleware."""

        def __init__(self, app):
            super().__init__(
                app,
                exclude_paths=combined_exclude,
                error_only_paths=combined_error_only,
            )

    return ConfiguredLoggingMiddleware


def get_request_id_from_request(request: Request) -> Optional[str]:
    """
    Get request ID from a request object.

    This is a utility function for use in route handlers.

    Args:
        request: FastAPI Request object

    Returns:
        Request ID if available, None otherwise
    """
    return getattr(request.state, "request_id", None) or get_request_id()
