"""
Text generation module for the blog-AI project.
"""

from ..types.providers import GenerationOptions
from .core import (
    TextGenerationError,
    RateLimitError,
    generate_text,
    generate_text_async,
    create_provider_from_env,
)
from .rate_limiter import (
    OperationType,
    RateLimitConfig,
    RateLimitExceededError,
    RateLimiter,
    TokenBucket,
    get_rate_limiter,
    set_rate_limiter,
    reset_rate_limiter,
)
from .streaming import (
    StreamEvent,
    StreamEventType,
    StreamingError,
    collect_stream,
    stream_text,
    stream_text_simple,
)

__all__ = [
    # Core generation
    "TextGenerationError",
    "RateLimitError",
    "generate_text",
    "generate_text_async",
    "create_provider_from_env",
    # Types
    "GenerationOptions",
    # Streaming generation
    "StreamEvent",
    "StreamEventType",
    "StreamingError",
    "collect_stream",
    "stream_text",
    "stream_text_simple",
    # Rate limiting
    "OperationType",
    "RateLimitConfig",
    "RateLimitExceededError",
    "RateLimiter",
    "TokenBucket",
    "get_rate_limiter",
    "set_rate_limiter",
    "reset_rate_limiter",
]
