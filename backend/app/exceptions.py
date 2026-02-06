"""
Custom exception classes for the Blog AI application.

This module provides a hierarchy of custom exceptions that map to specific
HTTP status codes and error scenarios. All exceptions inherit from BlogAIException
to enable consistent error handling across the application.

Exception Hierarchy:
    BlogAIException (base)
    ├── ValidationError (400)
    ├── AuthenticationError (401)
    ├── AuthorizationError (403)
    ├── ResourceNotFoundError (404)
    ├── ConflictError (409)
    ├── RateLimitError (429)
    ├── ExternalServiceError (502)
    │   ├── StripeServiceError
    │   ├── OpenAIServiceError
    │   ├── AnthropicServiceError
    │   └── GeminiServiceError
    └── DatabaseError (500)
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """
    Standardized error codes for API responses.

    These codes provide machine-readable identifiers for error conditions,
    enabling clients to programmatically handle specific error scenarios.
    """

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"

    # Authentication errors (401)
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_API_KEY = "INVALID_API_KEY"
    EXPIRED_API_KEY = "EXPIRED_API_KEY"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"

    # Authorization errors (403)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    FEATURE_NOT_AVAILABLE = "FEATURE_NOT_AVAILABLE"
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"

    # Resource errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    CONTENT_NOT_FOUND = "CONTENT_NOT_FOUND"

    # Conflict errors (409)
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"

    # Rate limiting errors (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    GENERATION_LIMIT_EXCEEDED = "GENERATION_LIMIT_EXCEEDED"

    # External service errors (502)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    STRIPE_ERROR = "STRIPE_ERROR"
    OPENAI_ERROR = "OPENAI_ERROR"
    ANTHROPIC_ERROR = "ANTHROPIC_ERROR"
    GEMINI_ERROR = "GEMINI_ERROR"
    LLM_PROVIDER_ERROR = "LLM_PROVIDER_ERROR"
    WEBHOOK_ERROR = "WEBHOOK_ERROR"

    # Database errors (500)
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"

    # Content generation errors
    GENERATION_ERROR = "GENERATION_ERROR"
    CONTENT_GENERATION_FAILED = "CONTENT_GENERATION_FAILED"
    RESEARCH_FAILED = "RESEARCH_FAILED"


class BlogAIException(Exception):
    """
    Base exception class for all Blog AI application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and response formatting.

    Attributes:
        message: Human-readable error message (sanitized for external display).
        error_code: Machine-readable error code from ErrorCode enum.
        status_code: HTTP status code to return.
        details: Additional context about the error (optional).
        internal_message: Detailed message for logging (not exposed to clients).
    """

    status_code: int = 500
    default_error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message for the client.
            error_code: Machine-readable error code.
            details: Additional context (must not contain sensitive data).
            internal_message: Detailed message for logging only.
        """
        self.message = message or self.default_message
        self.error_code = error_code or self.default_error_code
        self.details = details or {}
        self.internal_message = internal_message
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to a dictionary for API response.

        Returns:
            Dictionary with error information suitable for JSON serialization.
        """
        response = {
            "success": False,
            "error": self.message,
            "error_code": self.error_code.value,
        }
        if self.details:
            response["details"] = self.details
        return response

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code.value!r}, "
            f"status_code={self.status_code})"
        )


# =============================================================================
# Validation Errors (400 Bad Request)
# =============================================================================

class ValidationError(BlogAIException):
    """
    Raised when request data fails validation.

    Use this for:
    - Invalid input formats
    - Missing required fields
    - Values outside acceptable ranges
    - Malformed request bodies
    """

    status_code = 400
    default_error_code = ErrorCode.VALIDATION_ERROR
    default_message = "Invalid request data"

    def __init__(
        self,
        message: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message.
            field: Name of the field that failed validation.
            value: The invalid value (will be truncated if too long).
            error_code: Specific error code.
            details: Additional details.
            internal_message: Internal logging message.
        """
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            # Truncate long values to avoid exposing sensitive data
            str_value = str(value)
            details["value"] = str_value[:100] + "..." if len(str_value) > 100 else str_value

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Authentication Errors (401 Unauthorized)
# =============================================================================

class AuthenticationError(BlogAIException):
    """
    Raised when authentication fails.

    Use this for:
    - Missing API key
    - Invalid API key
    - Expired tokens
    - Malformed authentication headers
    """

    status_code = 401
    default_error_code = ErrorCode.AUTHENTICATION_REQUIRED
    default_message = "Authentication required"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Authorization Errors (403 Forbidden)
# =============================================================================

class AuthorizationError(BlogAIException):
    """
    Raised when the authenticated user lacks permission.

    Use this for:
    - Insufficient permissions for an action
    - Quota exceeded
    - Feature not available on current plan
    - Attempting to access another user's resources
    """

    status_code = 403
    default_error_code = ErrorCode.PERMISSION_DENIED
    default_message = "Permission denied"

    def __init__(
        self,
        message: Optional[str] = None,
        required_permission: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


class QuotaExceededError(AuthorizationError):
    """
    Raised when a user exceeds their usage quota.

    This is a specific type of authorization error for quota violations.
    """

    default_error_code = ErrorCode.QUOTA_EXCEEDED
    default_message = "Usage quota exceeded"

    def __init__(
        self,
        message: Optional[str] = None,
        quota_type: Optional[str] = None,
        limit: Optional[int] = None,
        current_usage: Optional[int] = None,
        reset_time: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if quota_type:
            details["quota_type"] = quota_type
        if limit is not None:
            details["limit"] = limit
        if current_usage is not None:
            details["current_usage"] = current_usage
        if reset_time:
            details["reset_time"] = reset_time

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Resource Not Found Errors (404 Not Found)
# =============================================================================

class ResourceNotFoundError(BlogAIException):
    """
    Raised when a requested resource does not exist.

    Use this for:
    - Conversation not found
    - User not found
    - Content not found
    - Any 404 scenario
    """

    status_code = 404
    default_error_code = ErrorCode.RESOURCE_NOT_FOUND
    default_message = "Resource not found"

    def __init__(
        self,
        message: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            # Truncate ID to avoid exposing full UUIDs in some cases
            details["resource_id"] = resource_id[:36] if len(resource_id) > 36 else resource_id

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Conflict Errors (409 Conflict)
# =============================================================================

class ConflictError(BlogAIException):
    """
    Raised when there is a resource conflict.

    Use this for:
    - Duplicate resource creation
    - Concurrent modification conflicts
    - State conflicts
    """

    status_code = 409
    default_error_code = ErrorCode.RESOURCE_CONFLICT
    default_message = "Resource conflict"

    def __init__(
        self,
        message: Optional[str] = None,
        resource_type: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Rate Limit Errors (429 Too Many Requests)
# =============================================================================

class RateLimitError(BlogAIException):
    """
    Raised when rate limits are exceeded.

    Use this for:
    - API rate limiting
    - Generation request limits
    - Any throttling scenario
    """

    status_code = 429
    default_error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    default_message = "Rate limit exceeded"

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if limit is not None:
            details["limit"] = limit
        if window_seconds is not None:
            details["window_seconds"] = window_seconds

        self.retry_after = retry_after

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )

    def to_dict(self) -> Dict[str, Any]:
        response = super().to_dict()
        if self.retry_after:
            response["retry_after"] = self.retry_after
        return response


# =============================================================================
# External Service Errors (502 Bad Gateway)
# =============================================================================

class ExternalServiceError(BlogAIException):
    """
    Base class for external service failures.

    Use this for:
    - Third-party API failures
    - External service timeouts
    - Integration errors
    """

    status_code = 502
    default_error_code = ErrorCode.EXTERNAL_SERVICE_ERROR
    default_message = "External service error"

    def __init__(
        self,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = details or {}
        if service_name:
            details["service"] = service_name

        self.original_error = original_error

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message or (str(original_error) if original_error else None),
        )


class StripeServiceError(ExternalServiceError):
    """Raised when Stripe API calls fail."""

    default_error_code = ErrorCode.STRIPE_ERROR
    default_message = "Payment service temporarily unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        stripe_error_code: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        details = details or {}
        # Only include safe Stripe error codes, not detailed messages
        if stripe_error_code:
            details["stripe_code"] = stripe_error_code

        super().__init__(
            message=message,
            service_name="stripe",
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
            original_error=original_error,
        )


class OpenAIServiceError(ExternalServiceError):
    """Raised when OpenAI API calls fail."""

    default_error_code = ErrorCode.OPENAI_ERROR
    default_message = "AI service temporarily unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            service_name="openai",
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
            original_error=original_error,
        )


class AnthropicServiceError(ExternalServiceError):
    """Raised when Anthropic API calls fail."""

    default_error_code = ErrorCode.ANTHROPIC_ERROR
    default_message = "AI service temporarily unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            service_name="anthropic",
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
            original_error=original_error,
        )


class GeminiServiceError(ExternalServiceError):
    """Raised when Google Gemini API calls fail."""

    default_error_code = ErrorCode.GEMINI_ERROR
    default_message = "AI service temporarily unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            service_name="gemini",
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
            original_error=original_error,
        )


class LLMProviderError(ExternalServiceError):
    """
    Generic LLM provider error.

    Use when the specific provider is not known or for general LLM failures.
    """

    default_error_code = ErrorCode.LLM_PROVIDER_ERROR
    default_message = "Content generation service temporarily unavailable"

    def __init__(
        self,
        message: Optional[str] = None,
        provider_name: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            service_name=provider_name or "llm_provider",
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
            original_error=original_error,
        )


# =============================================================================
# Database Errors (500 Internal Server Error)
# =============================================================================

class DatabaseError(BlogAIException):
    """
    Raised when database operations fail.

    Use this for:
    - Connection failures
    - Query errors
    - Transaction failures
    - Migration issues

    Note: Database errors should never expose internal details to clients.
    """

    status_code = 500
    default_error_code = ErrorCode.DATABASE_ERROR
    default_message = "A database error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        # Never expose database operation details to clients
        # Only use internal_message for logging
        self.original_error = original_error

        super().__init__(
            message=message or self.default_message,
            error_code=error_code or self.default_error_code,
            details=details or {},  # Intentionally minimal for security
            internal_message=internal_message or (
                f"Database operation '{operation}' failed: {original_error}"
                if operation and original_error
                else None
            ),
        )


# =============================================================================
# Content Generation Errors
# =============================================================================

class ContentGenerationError(BlogAIException):
    """
    Raised when content generation fails.

    Use this for:
    - Blog generation failures
    - Book generation failures
    - Research failures
    """

    status_code = 500
    default_error_code = ErrorCode.CONTENT_GENERATION_FAILED
    default_message = "Content generation failed"

    def __init__(
        self,
        message: Optional[str] = None,
        content_type: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None,
    ):
        details = details or {}
        if content_type:
            details["content_type"] = content_type

        super().__init__(
            message=message,
            error_code=error_code or self.default_error_code,
            details=details,
            internal_message=internal_message,
        )


# =============================================================================
# Utility Functions
# =============================================================================

def is_retryable_error(exc: Exception) -> bool:
    """
    Check if an error is potentially retryable.

    Args:
        exc: The exception to check.

    Returns:
        True if the client should consider retrying the request.
    """
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, ExternalServiceError):
        # External service errors are often transient
        return True
    if isinstance(exc, DatabaseError):
        # Connection errors might be retryable
        return exc.error_code == ErrorCode.CONNECTION_ERROR
    return False


def get_safe_error_message(exc: Exception) -> str:
    """
    Get a safe error message that doesn't leak sensitive information.

    Args:
        exc: The exception to get a message for.

    Returns:
        A sanitized error message safe for client display.
    """
    if isinstance(exc, BlogAIException):
        return exc.message

    # For unknown exceptions, return a generic message
    return "An unexpected error occurred. Please try again later."
