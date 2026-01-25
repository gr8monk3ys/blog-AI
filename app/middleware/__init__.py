"""Middleware components for the Blog AI application."""

from .https_redirect import HTTPSRedirectMiddleware
from .logging import (
    RequestLoggingMiddleware,
    get_request_logging_middleware,
    get_request_id_from_request,
)
from .quota_check import (
    QuotaCheckError,
    QuotaTracker,
    check_quota_soft,
    create_quota_check_for_tier,
    get_quota_status,
    increment_usage_for_operation,
    require_business_tier,
    require_pro_tier,
    require_quota,
    require_starter_tier,
)
from .rate_limiter import RateLimitMiddleware
from .rate_limit import (
    # Data models
    TierRateLimits,
    TIER_RATE_LIMITS,
    DEFAULT_RATE_LIMITS,
    RateLimitResult,
    RateLimitExceededError,
    RateLimitException,
    # Backend implementations
    RateLimitBackend,
    InMemoryBackend,
    RedisBackend,
    # Rate limiter
    RateLimiter,
    get_rate_limiter,
    # FastAPI dependencies
    rate_limit,
    rate_limit_soft,
    get_rate_limit_status,
)
from .security import (
    RequestIDMiddleware,
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
    create_security_middleware_stack,
    get_security_config_from_env,
)

__all__ = [
    # HTTPS
    "HTTPSRedirectMiddleware",
    # Logging
    "RequestLoggingMiddleware",
    "get_request_logging_middleware",
    "get_request_id_from_request",
    # Quota
    "QuotaCheckError",
    "QuotaTracker",
    "check_quota_soft",
    "create_quota_check_for_tier",
    "get_quota_status",
    "increment_usage_for_operation",
    "require_business_tier",
    "require_pro_tier",
    "require_quota",
    "require_starter_tier",
    # Rate Limiting (middleware)
    "RateLimitMiddleware",
    # Rate Limiting (dependency-based)
    "TierRateLimits",
    "TIER_RATE_LIMITS",
    "DEFAULT_RATE_LIMITS",
    "RateLimitResult",
    "RateLimitExceededError",
    "RateLimitException",
    "RateLimitBackend",
    "InMemoryBackend",
    "RedisBackend",
    "RateLimiter",
    "get_rate_limiter",
    "rate_limit",
    "rate_limit_soft",
    "get_rate_limit_status",
    # Security
    "RequestIDMiddleware",
    "RequestValidationMiddleware",
    "SecurityHeadersMiddleware",
    "create_security_middleware_stack",
    "get_security_config_from_env",
]
