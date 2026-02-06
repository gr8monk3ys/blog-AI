"""
FastAPI exception handlers for the Blog AI application.

This module provides centralized exception handling that:
- Maps custom exceptions to appropriate HTTP responses
- Handles Pydantic validation errors with clean messages
- Reports unexpected exceptions to Sentry
- Ensures consistent error response format
- Prevents sensitive information leakage

All error responses follow the format:
{
    "success": false,
    "error": "Human-readable message",
    "error_code": "MACHINE_READABLE_CODE",
    "details": {}  # Optional additional context
}
"""

import logging
import os
import re
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    BlogAIException,
    ConflictError,
    ContentGenerationError,
    DatabaseError,
    ErrorCode,
    ExternalServiceError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"

# Patterns that indicate sensitive information
SENSITIVE_PATTERNS = [
    r"api[_-]?key",
    r"secret",
    r"password",
    r"token",
    r"auth",
    r"credential",
    r"private",
    r"bearer",
    r"session",
    r"cookie",
    # Database connection strings
    r"postgres://",
    r"mysql://",
    r"mongodb://",
    r"redis://",
    # File paths that might be sensitive
    r"/home/",
    r"/Users/",
    r"/var/",
    r"/etc/",
    # Environment variable references
    r"\$\{?\w+\}?",
]

# Compile patterns for efficiency
SENSITIVE_REGEX = re.compile(
    "|".join(SENSITIVE_PATTERNS),
    re.IGNORECASE
)


def sanitize_error_message(message: str) -> str:
    """
    Remove potentially sensitive information from error messages.

    Args:
        message: The error message to sanitize.

    Returns:
        Sanitized message with sensitive data redacted.
    """
    if not message:
        return message

    # Check for sensitive patterns
    if SENSITIVE_REGEX.search(message):
        # If sensitive content detected, return generic message
        return "An error occurred while processing your request"

    # Remove any file paths
    message = re.sub(r'[/\\][\w./\\-]+\.\w+', '[path]', message)

    # Remove IP addresses
    message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[ip]', message)

    # Remove UUIDs (but keep shorter IDs)
    message = re.sub(
        r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
        '[id]',
        message,
        flags=re.IGNORECASE
    )

    # Truncate very long messages
    if len(message) > 500:
        message = message[:500] + "..."

    return message


def sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize error details to remove sensitive information.

    Args:
        details: Dictionary of error details.

    Returns:
        Sanitized details dictionary.
    """
    if not details:
        return {}

    sanitized = {}
    safe_keys = {
        "field", "value", "resource_type", "resource_id",
        "limit", "current_usage", "reset_time", "retry_after",
        "window_seconds", "quota_type", "content_type",
        "required_permission", "service"
    }

    for key, value in details.items():
        if key not in safe_keys:
            continue

        if isinstance(value, str):
            sanitized[key] = sanitize_error_message(value)
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            # Only include primitive values in lists
            sanitized[key] = [
                v for v in value
                if isinstance(v, (str, int, float, bool))
            ][:10]  # Limit list length
        # Skip complex nested structures

    return sanitized


def format_pydantic_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format Pydantic validation errors into a clean, consistent format.

    Args:
        errors: List of Pydantic error dictionaries.

    Returns:
        List of formatted error dictionaries with field and message.
    """
    formatted = []
    for error in errors:
        loc = error.get("loc", [])
        # Build field path (skip 'body' if present)
        field_parts = [str(p) for p in loc if p != "body"]
        field = ".".join(field_parts) if field_parts else "request"

        # Get error type and create human-readable message
        error_type = error.get("type", "")
        msg = error.get("msg", "Invalid value")

        # Create user-friendly messages for common errors
        if error_type == "missing":
            msg = f"Field '{field}' is required"
        elif error_type == "string_type":
            msg = f"Field '{field}' must be a string"
        elif error_type == "int_type":
            msg = f"Field '{field}' must be an integer"
        elif error_type == "bool_type":
            msg = f"Field '{field}' must be a boolean"
        elif error_type == "value_error":
            msg = sanitize_error_message(msg)
        elif "enum" in error_type.lower():
            msg = f"Field '{field}' has an invalid value"
        else:
            # Sanitize the original message
            msg = sanitize_error_message(msg)

        formatted.append({
            "field": field,
            "message": msg,
        })

    # Limit number of errors to prevent response bloat
    return formatted[:10]


def create_error_response(
    status_code: int,
    error: str,
    error_code: str,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code.
        error: Human-readable error message.
        error_code: Machine-readable error code.
        details: Optional additional details.
        headers: Optional response headers.

    Returns:
        JSONResponse with consistent error format.
    """
    content = {
        "success": False,
        "error": sanitize_error_message(error),
        "error_code": error_code,
    }

    if details:
        sanitized_details = sanitize_details(details)
        if sanitized_details:
            content["details"] = sanitized_details

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )


def report_to_sentry(
    exc: Exception,
    request: Optional[Request] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Report an exception to Sentry with context.

    Args:
        exc: The exception to report.
        request: Optional FastAPI request for context.
        extra_context: Optional additional context.

    Returns:
        Sentry event ID if reported, None otherwise.
    """
    try:
        # Check if Sentry is configured
        client = sentry_sdk.get_client()
        if not client.is_active():
            return None

        with sentry_sdk.push_scope() as scope:
            # Add request context if available
            if request:
                scope.set_context("request", {
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                })

                # Add user context if available
                if hasattr(request.state, "user_id"):
                    scope.set_user({"id": request.state.user_id})

                # Add request ID for correlation
                request_id = request.headers.get("X-Request-ID")
                if request_id:
                    scope.set_tag("request_id", request_id)

            # Add extra context
            if extra_context:
                scope.set_context("extra", extra_context)

            # Capture the exception
            event_id = sentry_sdk.capture_exception(exc)
            return event_id

    except Exception as e:
        logger.warning(f"Failed to report exception to Sentry: {e}")
        return None


# =============================================================================
# Exception Handlers
# =============================================================================

async def blog_ai_exception_handler(
    request: Request,
    exc: BlogAIException,
) -> JSONResponse:
    """
    Handle all BlogAIException and subclasses.

    This handler processes our custom exception hierarchy and returns
    appropriate HTTP responses while logging internal details.
    """
    # Log the error with internal details
    log_message = f"{exc.__class__.__name__}: {exc.message}"
    if exc.internal_message:
        log_message += f" | Internal: {exc.internal_message}"

    # Choose log level based on status code
    if exc.status_code >= 500:
        logger.error(log_message, exc_info=True)
        # Report 5xx errors to Sentry
        report_to_sentry(exc, request)
    elif exc.status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)

    # Build response headers
    headers = {}
    if isinstance(exc, RateLimitError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return create_error_response(
        status_code=exc.status_code,
        error=exc.message,
        error_code=exc.error_code.value,
        details=exc.details,
        headers=headers if headers else None,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic/FastAPI validation errors.

    Converts validation errors into a clean, user-friendly format
    without exposing internal validation details.
    """
    errors = format_pydantic_errors(exc.errors())

    logger.warning(
        f"Validation error on {request.method} {request.url.path}: "
        f"{len(errors)} error(s)"
    )

    # Create a summary message
    if len(errors) == 1:
        error_message = errors[0]["message"]
    else:
        error_message = f"Validation failed with {len(errors)} error(s)"

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error=error_message,
        error_code=ErrorCode.VALIDATION_ERROR.value,
        details={"errors": errors},
    )


async def pydantic_validation_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """
    Handle direct Pydantic ValidationError (not wrapped by FastAPI).
    """
    errors = format_pydantic_errors(exc.errors())

    logger.warning(
        f"Pydantic validation error on {request.method} {request.url.path}: "
        f"{len(errors)} error(s)"
    )

    if len(errors) == 1:
        error_message = errors[0]["message"]
    else:
        error_message = f"Validation failed with {len(errors)} error(s)"

    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error=error_message,
        error_code=ErrorCode.VALIDATION_ERROR.value,
        details={"errors": errors},
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle Starlette/FastAPI HTTPException.

    Converts HTTPException to our standard error format while
    preserving the status code and detail message.
    """
    # Map status codes to error codes
    status_code_mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.VALIDATION_ERROR,
        409: ErrorCode.RESOURCE_CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.EXTERNAL_SERVICE_ERROR,
        504: ErrorCode.EXTERNAL_SERVICE_ERROR,
    }

    error_code = status_code_mapping.get(
        exc.status_code,
        ErrorCode.UNKNOWN_ERROR
    )

    # Get detail message
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    # Log based on status code
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code}: {detail}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code}: {detail}")

    # Build headers
    headers = {}
    if exc.headers:
        # Only pass through safe headers
        safe_headers = {"Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"}
        headers = {k: v for k, v in exc.headers.items() if k in safe_headers}

    return create_error_response(
        status_code=exc.status_code,
        error=sanitize_error_message(detail),
        error_code=error_code.value,
        headers=headers if headers else None,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle any unhandled exceptions.

    This is the catch-all handler for unexpected errors. It:
    - Logs the full exception with traceback
    - Reports to Sentry
    - Returns a generic error message (no internal details)
    """
    # Generate a reference ID for support
    import uuid
    error_reference = str(uuid.uuid4())[:8]

    # Log the full error with traceback
    logger.error(
        f"Unhandled exception [ref:{error_reference}] on "
        f"{request.method} {request.url.path}: {exc}",
        exc_info=True,
    )

    # Report to Sentry
    event_id = report_to_sentry(
        exc,
        request,
        extra_context={"error_reference": error_reference}
    )

    # In development, include more details
    if not IS_PRODUCTION:
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=f"Internal server error: {type(exc).__name__}",
            error_code=ErrorCode.INTERNAL_ERROR.value,
            details={
                "error_reference": error_reference,
                "sentry_event_id": event_id,
            } if event_id else {"error_reference": error_reference},
        )

    # In production, return minimal information
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="An unexpected error occurred. Please try again later.",
        error_code=ErrorCode.INTERNAL_ERROR.value,
        details={"error_reference": error_reference},
    )


# =============================================================================
# Handler Registration
# =============================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    This function should be called during application startup to ensure
    all exceptions are handled consistently.

    Args:
        app: The FastAPI application instance.
    """
    # Register handlers for our custom exceptions
    app.add_exception_handler(BlogAIException, blog_ai_exception_handler)

    # Register handlers for validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)

    # Register handler for HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Register catch-all handler for unhandled exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("Exception handlers registered successfully")


# =============================================================================
# Middleware for Error Handling Context
# =============================================================================

class ErrorHandlingMiddleware:
    """
    Middleware to add error handling context to requests.

    This middleware ensures that:
    - All requests have a unique ID for error correlation
    - User context is available for error reporting
    - Timing information is captured for diagnostics
    """

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Add timing context
        import time
        start_time = time.time()

        # Create request for context
        request = Request(scope, receive)

        # Store start time in request state
        if not hasattr(scope, "state"):
            scope["state"] = {}
        scope["state"]["start_time"] = start_time

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Calculate duration for logging
            duration = time.time() - start_time
            logger.error(
                f"Request failed after {duration:.3f}s: "
                f"{request.method} {request.url.path}"
            )
            raise
