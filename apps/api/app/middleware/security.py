"""
Security middleware for production hardening.

Provides:
- Security headers middleware (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
- Request ID middleware for distributed tracing
- Request validation middleware (body size, content-type)
"""

import logging
import os
import uuid
from typing import Optional, Set

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


# =============================================================================
# Security Headers Middleware
# =============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff - Prevents MIME type sniffing
    - X-Frame-Options: DENY - Prevents clickjacking attacks
    - X-XSS-Protection: 1; mode=block - Legacy XSS protection for older browsers
    - Strict-Transport-Security - Enforces HTTPS (when enabled)
    - Content-Security-Policy - Controls resource loading
    - Referrer-Policy - Controls referrer information
    - Permissions-Policy - Controls browser features
    - Cache-Control - For sensitive endpoints
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        csp_policy: Optional[str] = None,
        exclude_paths: Optional[Set[str]] = None,
    ):
        """
        Initialize the security headers middleware.

        Args:
            app: The FastAPI application.
            enable_hsts: Enable Strict-Transport-Security header.
            hsts_max_age: HSTS max-age in seconds.
            hsts_include_subdomains: Include subdomains in HSTS.
            hsts_preload: Enable HSTS preload (requires careful consideration).
            csp_policy: Custom Content-Security-Policy. If None, uses default.
            exclude_paths: Paths to exclude from security headers.
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.exclude_paths = exclude_paths or set()

        # Default CSP policy - restrictive but functional for API
        self.csp_policy = csp_policy or self._get_default_csp()

    def _get_default_csp(self) -> str:
        """
        Generate a default Content-Security-Policy.

        This is a restrictive policy suitable for an API backend.
        Adjust based on your specific requirements.
        """
        directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # Swagger UI needs inline styles
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
            "upgrade-insecure-requests",
        ]
        return "; ".join(directives)

    def _build_hsts_header(self) -> str:
        """Build the Strict-Transport-Security header value."""
        parts = [f"max-age={self.hsts_max_age}"]
        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")
        if self.hsts_preload:
            parts.append("preload")
        return "; ".join(parts)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Skip for excluded paths
        if request.url.path in self.exclude_paths:
            return response

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # HSTS - only add when request is HTTPS or has X-Forwarded-Proto: https
        if self.enable_hsts:
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
            is_https = forwarded_proto == "https" or request.url.scheme == "https"
            if is_https:
                response.headers["Strict-Transport-Security"] = self._build_hsts_header()

        # Cache control for API responses (prevent caching of sensitive data)
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


# =============================================================================
# Request ID Middleware
# =============================================================================


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request for tracing.

    The request ID is:
    - Generated for each incoming request (or extracted from X-Request-ID header)
    - Added to the request state for use in logging
    - Added to the response headers for client-side correlation
    """

    REQUEST_ID_HEADER = "X-Request-ID"

    def __init__(
        self,
        app,
        trust_incoming_id: bool = False,
        id_prefix: str = "",
    ):
        """
        Initialize the request ID middleware.

        Args:
            app: The FastAPI application.
            trust_incoming_id: If True, use X-Request-ID from client if present.
            id_prefix: Optional prefix for generated request IDs.
        """
        super().__init__(app)
        self.trust_incoming_id = trust_incoming_id
        self.id_prefix = id_prefix

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        request_id = str(uuid.uuid4())
        if self.id_prefix:
            return f"{self.id_prefix}-{request_id}"
        return request_id

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add request ID."""
        # Get or generate request ID
        request_id = None
        if self.trust_incoming_id:
            request_id = request.headers.get(self.REQUEST_ID_HEADER)

        if not request_id:
            request_id = self._generate_request_id()

        # Store in request state for logging
        request.state.request_id = request_id

        # Log the request with ID
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{self.REQUEST_ID_HEADER}: {request_id}]"
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{self.REQUEST_ID_HEADER}: {request_id}] - {str(e)}"
            )
            raise

        # Add request ID to response
        response.headers[self.REQUEST_ID_HEADER] = request_id

        return response


# =============================================================================
# Request Validation Middleware
# =============================================================================


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating incoming requests.

    Validates:
    - Request body size (prevents denial of service via large payloads)
    - Content-Type header for POST/PUT/PATCH requests
    """

    # Default maximum body size: 10MB
    DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024

    # Allowed content types for request bodies
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    }

    # Methods that can have a request body
    BODY_METHODS = {"POST", "PUT", "PATCH"}

    def __init__(
        self,
        app,
        max_body_size: Optional[int] = None,
        validate_content_type: bool = True,
        allowed_content_types: Optional[Set[str]] = None,
        exclude_paths: Optional[Set[str]] = None,
    ):
        """
        Initialize the request validation middleware.

        Args:
            app: The FastAPI application.
            max_body_size: Maximum allowed body size in bytes. Default 10MB.
            validate_content_type: Whether to validate Content-Type headers.
            allowed_content_types: Set of allowed Content-Type values.
            exclude_paths: Paths to exclude from validation.
        """
        super().__init__(app)
        self.max_body_size = max_body_size or self.DEFAULT_MAX_BODY_SIZE
        self.validate_content_type = validate_content_type
        self.allowed_content_types = allowed_content_types or self.ALLOWED_CONTENT_TYPES
        self.exclude_paths = exclude_paths or {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

    def _is_valid_content_type(self, content_type: Optional[str]) -> bool:
        """Check if the Content-Type is allowed."""
        if not content_type:
            return False

        # Extract base content type (without parameters like charset)
        base_type = content_type.split(";")[0].strip().lower()
        return base_type in self.allowed_content_types

    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate request and process if valid."""
        # Skip validation for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check Content-Type for body methods
        if request.method in self.BODY_METHODS and self.validate_content_type:
            content_type = request.headers.get("Content-Type")
            content_length = request.headers.get("Content-Length")

            # Only validate Content-Type if there's a body
            if content_length and int(content_length) > 0:
                if not self._is_valid_content_type(content_type):
                    logger.warning(
                        f"Invalid Content-Type: {content_type} for {request.method} {request.url.path}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported media type. Allowed types: {', '.join(self.allowed_content_types)}",
                    )

        # Check body size
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                body_size = int(content_length)
                if body_size > self.max_body_size:
                    logger.warning(
                        f"Request body too large: {body_size} bytes for {request.url.path}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request body too large. Maximum size: {self.max_body_size} bytes",
                    )
            except ValueError:
                # Invalid Content-Length header
                logger.warning(f"Invalid Content-Length header: {content_length}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header",
                )

        return await call_next(request)


# =============================================================================
# Factory Functions for Easy Configuration
# =============================================================================


def create_security_middleware_stack(
    app,
    enable_hsts: bool = True,
    hsts_max_age: int = 31536000,
    max_body_size: int = 10 * 1024 * 1024,
    trust_request_id: bool = False,
    request_id_prefix: str = "blog-ai",
    custom_csp: Optional[str] = None,
):
    """
    Create and add the full security middleware stack to an app.

    This is a convenience function that adds all security middleware
    in the correct order.

    Args:
        app: The FastAPI application.
        enable_hsts: Enable HSTS header.
        hsts_max_age: HSTS max-age in seconds.
        max_body_size: Maximum request body size in bytes.
        trust_request_id: Trust incoming X-Request-ID headers.
        request_id_prefix: Prefix for generated request IDs.
        custom_csp: Custom Content-Security-Policy.

    Returns:
        The app with middleware added.
    """
    # Add middleware in reverse order (first added = last executed)
    # Request validation first (innermost)
    app.add_middleware(
        RequestValidationMiddleware,
        max_body_size=max_body_size,
    )

    # Security headers
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=enable_hsts,
        hsts_max_age=hsts_max_age,
        csp_policy=custom_csp,
    )

    # Request ID last (outermost - first to execute)
    app.add_middleware(
        RequestIDMiddleware,
        trust_incoming_id=trust_request_id,
        id_prefix=request_id_prefix,
    )

    return app


# =============================================================================
# Configuration from Environment
# =============================================================================


def get_security_config_from_env() -> dict:
    """
    Load security configuration from environment variables.

    Environment variables:
    - SECURITY_HSTS_ENABLED: Enable HSTS (default: true in production)
    - SECURITY_HSTS_MAX_AGE: HSTS max-age in seconds (default: 31536000)
    - SECURITY_MAX_BODY_SIZE: Max request body size in bytes (default: 10485760)
    - SECURITY_TRUST_REQUEST_ID: Trust incoming X-Request-ID (default: false)
    - SECURITY_CSP_POLICY: Custom CSP policy (optional)
    """
    environment = os.environ.get("ENVIRONMENT", "development")
    is_production = environment.lower() == "production"

    return {
        "enable_hsts": os.environ.get(
            "SECURITY_HSTS_ENABLED", str(is_production)
        ).lower() == "true",
        "hsts_max_age": int(os.environ.get("SECURITY_HSTS_MAX_AGE", "31536000")),
        "max_body_size": int(os.environ.get("SECURITY_MAX_BODY_SIZE", str(10 * 1024 * 1024))),
        "trust_request_id": os.environ.get(
            "SECURITY_TRUST_REQUEST_ID", "false"
        ).lower() == "true",
        "request_id_prefix": os.environ.get("SECURITY_REQUEST_ID_PREFIX", "blog-ai"),
        "custom_csp": os.environ.get("SECURITY_CSP_POLICY"),
    }
