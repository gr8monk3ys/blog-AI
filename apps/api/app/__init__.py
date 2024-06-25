"""
Blog AI Application Package

This package contains the modularized FastAPI application components.
"""

from .error_handlers import register_exception_handlers
from .exceptions import (
    AnthropicServiceError,
    AuthenticationError,
    AuthorizationError,
    BlogAIException,
    ConflictError,
    ContentGenerationError,
    DatabaseError,
    ErrorCode,
    ExternalServiceError,
    GeminiServiceError,
    LLMProviderError,
    OpenAIServiceError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    StripeServiceError,
    ValidationError,
)

__version__ = "1.0.0"

__all__ = [
    # Exception classes
    "BlogAIException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "QuotaExceededError",
    "ResourceNotFoundError",
    "ConflictError",
    "RateLimitError",
    "ExternalServiceError",
    "StripeServiceError",
    "OpenAIServiceError",
    "AnthropicServiceError",
    "GeminiServiceError",
    "LLMProviderError",
    "DatabaseError",
    "ContentGenerationError",
    "ErrorCode",
    # Error handlers
    "register_exception_handlers",
]
