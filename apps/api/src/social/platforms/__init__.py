"""
Social media platform integrations.

Provides concrete implementations for each supported platform:
- Twitter/X (API v2)
- LinkedIn
- Buffer (multi-platform fallback)
"""

from .base import BasePlatform, PlatformError, RateLimitError
from .buffer import BufferPlatform
from .linkedin import LinkedInPlatform
from .twitter import TwitterPlatform

__all__ = [
    "BasePlatform",
    "PlatformError",
    "RateLimitError",
    "TwitterPlatform",
    "LinkedInPlatform",
    "BufferPlatform",
]
