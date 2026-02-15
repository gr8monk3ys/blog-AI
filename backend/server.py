"""
Backend server for the Blog AI application.
Provides API endpoints for generating blog posts and books.

This is the main entry point that assembles the modular components
from the app package.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Configure structured logging FIRST, before other imports that use logging
from src.utils.logging import setup_logging

logger = setup_logging(service_name="blog-ai-api")

# Import configuration system
from src.config import Settings, get_settings
from src.config_validator import (
    ConfigurationError,
    log_config_summary,
    validate_config,
)
from src.research.cache import clear_research_cache
from src.text_generation.core import close_llm_clients
from src.webhooks import webhook_service

# =============================================================================
# Configuration Validation
# =============================================================================

try:
    # Load and validate configuration at startup
    settings: Settings = get_settings()
    validation_result = validate_config(settings, fail_on_error=True)
    log_config_summary(settings)
except ConfigurationError as e:
    logger.critical(f"Configuration validation failed: {e}")
    logger.critical("Application cannot start due to configuration errors.")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Unexpected error loading configuration: {e}")
    sys.exit(1)

# =============================================================================
# Import middleware and routes after config is validated
# =============================================================================

from app.error_handlers import register_exception_handlers
from app.middleware import (
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)
from app.routes import (
    analytics_router,
    batch_router,
    blog_router,
    book_router,
    brand_voice_router,
    bulk_router,
    content_router,
    conversations_router,
    export_router,
    extension_router,
    health_router,
    images_router,
    organizations_router,
    payments_router,
    remix_router,
    social_router,
    sso_admin_router,
    sso_router,
    streaming_router,
    tools_router,
    usage_router,
    webhooks_router,
    websocket_router,
    zapier_router,
)


def _env_true(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# Legacy / Supabase-dependent modules. Keep code in-repo, but disable by default
# for a Neon-only SaaS until they're migrated.
ENABLE_KNOWLEDGE_BASE = _env_true("ENABLE_KNOWLEDGE_BASE", default=False)
ENABLE_PERFORMANCE_ANALYTICS = _env_true("ENABLE_PERFORMANCE_ANALYTICS", default=False)
ENABLE_CONTENT_VERSIONING = _env_true("ENABLE_CONTENT_VERSIONING", default=False)

# =============================================================================
# Sentry Error Tracking Configuration
# =============================================================================


def filter_sensitive_breadcrumbs(crumb, hint):
    """
    Filter sensitive data from Sentry breadcrumbs.

    Removes or sanitizes breadcrumbs that may contain:
    - API keys
    - Passwords
    - Authorization headers
    - Personal information
    """
    import re

    # List of sensitive keys to filter
    sensitive_keys = [
        "password", "api_key", "apikey", "api-key", "secret", "token",
        "authorization", "auth", "bearer", "credential", "private"
    ]

    if crumb.get("category") == "http":
        # Filter sensitive headers from HTTP breadcrumbs
        if "data" in crumb and isinstance(crumb["data"], dict):
            data = crumb["data"]
            # Remove authorization headers
            if "headers" in data and isinstance(data["headers"], dict):
                for key in list(data["headers"].keys()):
                    if any(s in key.lower() for s in sensitive_keys):
                        data["headers"][key] = "[FILTERED]"
            # Filter URL query parameters that might contain sensitive data
            if "url" in data:
                url = data["url"]
                for key in sensitive_keys:
                    if f"{key}=" in url.lower():
                        # Replace the parameter value with [FILTERED]
                        pattern = re.compile(f"({key}=)[^&]*", re.IGNORECASE)
                        data["url"] = pattern.sub(r"\1[FILTERED]", url)

    # Filter console/log breadcrumbs
    if crumb.get("category") in ("console", "log"):
        if "message" in crumb:
            message = str(crumb["message"]).lower()
            for key in sensitive_keys:
                if key in message:
                    crumb["message"] = "[FILTERED - may contain sensitive data]"
                    break

    return crumb


# Initialize Sentry using validated settings
if settings.is_sentry_configured:
    sentry_settings = settings.sentry
    sentry_sdk.init(
        dsn=sentry_settings.sentry_dsn,
        environment=sentry_settings.sentry_environment,
        # Sample rate for error events (1.0 = 100% of errors are sent)
        sample_rate=1.0,
        # Sample rate for performance transactions
        traces_sample_rate=sentry_settings.sentry_traces_sample_rate,
        # Sample rate for profiling (requires traces)
        profiles_sample_rate=sentry_settings.sentry_profiles_sample_rate,
        # Enable performance monitoring
        enable_tracing=True,
        # Integrations for FastAPI
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        # Filter sensitive data from breadcrumbs
        before_breadcrumb=filter_sensitive_breadcrumbs,
        # Send default PII (set to False to be more privacy-conscious)
        send_default_pii=False,
        # Attach stack traces to messages
        attach_stacktrace=True,
        # Server name for identifying the instance
        server_name=sentry_settings.server_name,
        # Release version for tracking deployments
        release=sentry_settings.sentry_release,
    )
    logger.info(f"Sentry initialized for environment: {sentry_settings.sentry_environment}")
else:
    logger.info("Sentry DSN not configured, error tracking disabled")


def is_sentry_initialized() -> bool:
    """Check if Sentry is properly initialized and configured."""
    try:
        client = sentry_sdk.get_client()
        return client.is_active() and settings.is_sentry_configured
    except Exception:
        return False


# =============================================================================
# Initialize FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown for shared resources."""
    yield
    try:
        close_llm_clients()
    except Exception as e:
        logger.warning("Failed to close LLM clients: %s", e)
    try:
        from src.db import close_pool

        await close_pool()
    except Exception as e:
        logger.warning("Failed to close Postgres pool: %s", e)
    try:
        clear_research_cache()
    except Exception as e:
        logger.warning("Failed to clear research cache: %s", e)
    try:
        await webhook_service.close()
    except Exception as e:
        logger.warning("Failed to close webhook service client: %s", e)

app = FastAPI(
    title="Blog AI API",
    description="""
## AI-Powered Content Generation API

Blog AI provides a comprehensive API for generating high-quality content including blog posts, books, and social media content using advanced AI models.

### Key Features

- **Blog Generation**: Create SEO-optimized blog posts with research integration
- **Book Generation**: Generate full-length books with structured chapters
- **Brand Voice Training**: Train and apply custom brand voices to content
- **Content Remix**: Transform content across multiple formats (Twitter, LinkedIn, etc.)
- **Batch Processing**: Process multiple content items in parallel
- **Image Generation**: Create AI-powered images for your content
- **Multi-Provider Support**: OpenAI, Anthropic Claude, and Google Gemini

### Authentication

All API endpoints require authentication. Supported methods:

- **Cloud SaaS (recommended):** Clerk session JWT via `Authorization: Bearer <token>`
- **API / CLI:** API key via `X-API-Key: <key>`

### Rate Limiting

Rate limits are applied per subscription tier:
- **Free**: 10 requests/minute, 100 requests/hour
- **Starter**: 30 requests/minute, 500 requests/hour
- **Pro**: 60 requests/minute, 2000 requests/hour
- **Business**: 120 requests/minute, 10000 requests/hour

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the limit resets

### Versioning

The API supports versioning via URL path. Current version: `v1`
- Root endpoints: `https://api.blogai.com/endpoint`
- Versioned endpoints: `https://api.blogai.com/api/v1/endpoint`

### Support

- Documentation: [https://docs.blogai.com](https://docs.blogai.com)
- Email: support@blogai.com
""",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health checks and system status"},
        {"name": "blog", "description": "Blog post generation endpoints"},
        {"name": "book", "description": "Book generation endpoints"},
        {"name": "Brand Voice Training", "description": "Train and apply custom brand voices"},
        {"name": "Content Remix", "description": "Transform content across formats"},
        {"name": "content", "description": "Content quality and plagiarism detection"},
        {"name": "Knowledge Base", "description": "Upload documents and search your knowledge base for RAG"},
        {"name": "batch", "description": "Batch processing for bulk content generation"},
        {"name": "images", "description": "AI-powered image generation"},
        {"name": "export", "description": "Export content to various formats"},
        {"name": "tools", "description": "Content generation tools and utilities"},
        {"name": "usage", "description": "Usage tracking and quota management"},
        {"name": "payments", "description": "Subscription and billing management"},
        {"name": "conversations", "description": "Conversation history management"},
        {"name": "social", "description": "Social media scheduling and publishing"},
        {"name": "sso", "description": "Single Sign-On authentication (SAML/OIDC)"},
        {"name": "sso-admin", "description": "SSO configuration and administration"},
        {"name": "debug", "description": "Debug and development endpoints"},
    ],
    contact={
        "name": "Blog AI Support",
        "email": "support@blogai.com",
        "url": "https://blogai.com/support",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://blogai.com/terms",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.blogai.com", "description": "Production"},
    ],
)

# =============================================================================
# Exception Handlers
# =============================================================================

# Register centralized exception handlers for consistent error responses
register_exception_handlers(app)
logger.info("Centralized exception handlers registered")

# =============================================================================
# Security Configuration (using validated settings)
# =============================================================================

security_settings = settings.security
rate_limit_settings = settings.rate_limit
logging_settings = settings.logging

# CORS middleware with hardened configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_settings.origins_list,
    allow_credentials=True,
    # Restrict to necessary HTTP methods only
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # Restrict to necessary headers only
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
        "Accept",
        "Accept-Language",
        "Origin",
    ],
    # Expose custom headers to the client
    expose_headers=[
        "X-Request-ID",
        "X-Correlation-ID",
        "X-Response-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    # Cache preflight requests for 10 minutes
    max_age=600,
)

# Add HTTPS redirect middleware in production
if security_settings.https_redirect_enabled:
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS redirect middleware enabled")

# Add rate limiting middleware
if rate_limit_settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=rate_limit_settings.rate_limit_general,
        generation_limit=rate_limit_settings.rate_limit_generation,
        window_seconds=60,
    )
    logger.info(
        f"Rate limiting enabled (general: {rate_limit_settings.rate_limit_general}/min, "
        f"generation: {rate_limit_settings.rate_limit_generation}/min)"
    )

# =============================================================================
# Security Middleware Stack
# =============================================================================

if security_settings.security_enabled:
    # Request validation - check body size and content type
    app.add_middleware(
        RequestValidationMiddleware,
        max_body_size=security_settings.security_max_body_size,
        validate_content_type=True,
    )
    logger.info(
        f"Request validation enabled (max body: {security_settings.security_max_body_size} bytes)"
    )

    # Security headers middleware
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=security_settings.hsts_enabled,
        hsts_max_age=security_settings.security_hsts_max_age,
        csp_policy=security_settings.security_csp_policy,
    )
    logger.info(
        f"Security headers enabled (HSTS: {security_settings.hsts_enabled})"
    )

    # Request ID middleware for tracing
    app.add_middleware(
        RequestIDMiddleware,
        trust_incoming_id=security_settings.security_trust_request_id,
        id_prefix=security_settings.security_request_id_prefix,
    )
    logger.info("Request ID tracing enabled")

# =============================================================================
# Request Logging Middleware
# =============================================================================
# Add request logging middleware last so it executes first and wraps all other middleware
# This ensures accurate timing and captures the full request lifecycle
if logging_settings.request_logging_enabled:
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware enabled")


# =============================================================================
# Include Routers
# =============================================================================

# Health and root endpoints (no auth required)
app.include_router(health_router)

# Main API routes (at root level for backward compatibility)
app.include_router(analytics_router)
app.include_router(batch_router)
app.include_router(brand_voice_router)
app.include_router(content_router)
app.include_router(conversations_router)
app.include_router(blog_router)
app.include_router(book_router)
app.include_router(bulk_router)
app.include_router(export_router)
app.include_router(extension_router)
app.include_router(images_router)
app.include_router(organizations_router)
app.include_router(payments_router)
app.include_router(remix_router)
app.include_router(streaming_router)
app.include_router(tools_router)
app.include_router(usage_router)
app.include_router(webhooks_router)
app.include_router(websocket_router)
app.include_router(zapier_router)
app.include_router(social_router)
app.include_router(sso_router)
app.include_router(sso_admin_router)

if ENABLE_KNOWLEDGE_BASE:
    from app.routes.knowledge import router as knowledge_router  # noqa: WPS433

    app.include_router(knowledge_router)
else:
    logger.info("Knowledge base routes disabled (ENABLE_KNOWLEDGE_BASE=false)")

if ENABLE_PERFORMANCE_ANALYTICS:
    from app.routes.performance import router as performance_router  # noqa: WPS433

    app.include_router(performance_router)
else:
    logger.info("Performance analytics routes disabled (ENABLE_PERFORMANCE_ANALYTICS=false)")

if ENABLE_CONTENT_VERSIONING:
    from app.routes.versions import router as versions_router  # noqa: WPS433

    app.include_router(versions_router)
else:
    logger.info("Content versioning routes disabled (ENABLE_CONTENT_VERSIONING=false)")

# Create versioned API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Add versioned routes
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(batch_router)
api_v1_router.include_router(brand_voice_router)
api_v1_router.include_router(content_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(blog_router)
api_v1_router.include_router(book_router)
api_v1_router.include_router(bulk_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(extension_router)
api_v1_router.include_router(images_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(remix_router)
api_v1_router.include_router(streaming_router)
api_v1_router.include_router(tools_router)
api_v1_router.include_router(usage_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(zapier_router)
api_v1_router.include_router(social_router)
api_v1_router.include_router(sso_router)
api_v1_router.include_router(sso_admin_router)

if ENABLE_KNOWLEDGE_BASE:
    from app.routes.knowledge import router as knowledge_router  # noqa: WPS433

    api_v1_router.include_router(knowledge_router)

if ENABLE_PERFORMANCE_ANALYTICS:
    from app.routes.performance import router as performance_router  # noqa: WPS433

    api_v1_router.include_router(performance_router)

if ENABLE_CONTENT_VERSIONING:
    from app.routes.versions import router as versions_router  # noqa: WPS433

    api_v1_router.include_router(versions_router)

# Include versioned router
app.include_router(api_v1_router)


# =============================================================================
# Debug Endpoints
# =============================================================================


@app.get("/debug-sentry", tags=["debug"])
async def trigger_sentry_error():
    """
    Debug endpoint to verify Sentry error tracking is working.

    WARNING: This endpoint intentionally raises an exception.
    Only use this in development/staging to verify Sentry integration.
    Should be disabled or protected in production.
    """
    if settings.is_production:
        return {
            "error": "Debug endpoint disabled in production",
            "sentry_configured": is_sentry_initialized(),
        }

    # This will trigger an error in Sentry
    division_by_zero = 1 / 0
    return {"this": "will never be reached"}


@app.get("/config-status", tags=["debug"])
async def get_config_status():
    """
    Get current configuration status (without secrets).

    This endpoint returns the configuration summary for debugging
    and operational visibility.
    """
    if settings.is_production and not settings.is_dev_mode:
        return {
            "error": "Config status endpoint disabled in production",
            "environment": settings.security.environment,
        }

    return {
        "success": True,
        "config": settings.get_config_summary(),
    }


if __name__ == "__main__":
    reload_enabled = os.environ.get("UVICORN_RELOAD", "false").lower() == "true"
    # Railway (and many other PaaS) provide `PORT`.
    port = int(os.environ.get("PORT") or os.environ.get("BACKEND_PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=reload_enabled)
