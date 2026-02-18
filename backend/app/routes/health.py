"""
Health check, readiness, and root endpoints.

Provides:
- GET /health    -- Comprehensive health check (public, no auth)
- GET /ready     -- Lightweight readiness probe for container orchestration
- GET /health/db, /health/stripe, /health/sentry, /health/redis -- Detailed per-service checks (auth required)
- GET /health/cache, POST /health/cache/cleanup -- Cache management (auth required)
- GET /          -- Root API information
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import sentry_sdk
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import verify_api_key
from src.config import Settings, get_settings
from src.db import get_database_url, is_database_configured, fetchrow as db_fetchrow
from src.storage import redis_client as _redis_client_instance

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Application version -- single source of truth
APP_VERSION = "1.0.0"

# Timestamp recorded when the module loads (proxy for "server started")
_server_start_time = time.monotonic()


# =============================================================================
# Internal helpers
# =============================================================================


async def _check_database() -> Dict[str, Any]:
    """Probe Postgres and return status + latency."""
    if not is_database_configured():
        return {"status": "disconnected", "latency_ms": None}

    try:
        start = time.monotonic()
        row = await db_fetchrow("SELECT 1 AS ok")
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        if row:
            return {"status": "connected", "latency_ms": latency_ms}
        return {"status": "disconnected", "latency_ms": None}
    except Exception as exc:
        logger.warning("Database health probe failed: %s", exc)
        return {"status": "disconnected", "latency_ms": None}


async def _check_redis() -> Dict[str, Any]:
    """Probe Redis and return status + latency."""
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return {"status": "disconnected", "latency_ms": None}

    try:
        client = await _redis_client_instance.get_client()
        if client is None:
            return {"status": "disconnected", "latency_ms": None}

        start = time.monotonic()
        await client.ping()
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {"status": "connected", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("Redis health probe failed: %s", exc)
        return {"status": "disconnected", "latency_ms": None}


def _get_llm_providers_status(settings: Settings) -> Dict[str, Any]:
    """Return configured/model info for each LLM provider without exposing keys."""
    llm = settings.llm
    return {
        "openai": {
            "configured": bool(llm.openai_api_key),
            "model": llm.openai_model if llm.openai_api_key else None,
        },
        "anthropic": {
            "configured": bool(llm.anthropic_api_key),
            "model": llm.anthropic_model if llm.anthropic_api_key else None,
        },
        "gemini": {
            "configured": bool(llm.gemini_api_key),
            "model": llm.gemini_model if llm.gemini_api_key else None,
        },
    }


def _get_feature_availability(settings: Settings) -> Dict[str, Any]:
    """
    Determine which high-level product features are available
    based on the current configuration.

    Each feature entry contains:
      - available (bool)
      - note (str | None) -- human-readable reason when unavailable
    """
    db_ok = settings.is_database_configured
    stripe_ok = settings.is_stripe_configured
    has_llm = settings.has_llm_provider

    def _feature(available: bool, note: Optional[str] = None) -> Dict[str, Any]:
        return {"available": available, "note": note}

    return {
        "content_generation": _feature(
            has_llm,
            None if has_llm else "Requires at least one LLM provider API key",
        ),
        "brand_profiles": _feature(
            db_ok,
            None if db_ok else "Requires DATABASE_URL",
        ),
        "conversation_history": _feature(
            db_ok,
            None if db_ok else "Requires DATABASE_URL",
        ),
        "payments": _feature(
            stripe_ok,
            None if stripe_ok else "Requires STRIPE_SECRET_KEY",
        ),
        "analytics": _feature(
            db_ok,
            None if db_ok else "Requires DATABASE_URL",
        ),
        "web_research": _feature(
            settings.has_research_api,
            None if settings.has_research_api else "Requires SERP_API_KEY or TAVILY_API_KEY",
        ),
    }


def _overall_status(
    db_status: Dict[str, Any],
    redis_status: Dict[str, Any],
    settings: Settings,
) -> str:
    """
    Derive the top-level status string.

    - healthy:   All configured services are reachable and at least one LLM is available
    - degraded:  The server can accept requests but one or more optional services are down
    - unhealthy: A critical service that is configured is unreachable
    """
    has_llm = settings.has_llm_provider
    if not has_llm:
        return "unhealthy"

    db_configured = settings.is_database_configured
    db_connected = db_status.get("status") == "connected"

    # If database is configured but unreachable, the system is degraded
    if db_configured and not db_connected:
        return "degraded"

    redis_configured = settings.is_redis_configured
    redis_connected = redis_status.get("status") == "connected"

    if redis_configured and not redis_connected:
        return "degraded"

    return "healthy"


# =============================================================================
# Public endpoints (no authentication)
# =============================================================================


@router.get(
    "/health",
    summary="Comprehensive system health check",
    description="""
Comprehensive health check endpoint for monitoring systems and dashboards.

Returns:
- Overall system status (healthy / degraded / unhealthy)
- Per-service connectivity and latency (database, Redis, LLM providers)
- Feature availability map showing which product features are operational

**Authentication**: Not required. This endpoint is intentionally public
so that load balancers, uptime monitors, and container orchestrators can
call it without credentials.

**Security**: No API keys, connection strings, or other secrets are
included in the response.
    """,
    responses={
        200: {
            "description": "Health status retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2026-02-16T12:00:00+00:00",
                        "services": {
                            "database": {"status": "connected", "latency_ms": 5.2},
                            "redis": {"status": "connected", "latency_ms": 1.8},
                            "llm_providers": {
                                "openai": {"configured": True, "model": "gpt-4"},
                                "anthropic": {"configured": False, "model": None},
                                "gemini": {"configured": False, "model": None},
                            },
                        },
                        "features": {
                            "content_generation": {"available": True, "note": None},
                            "brand_profiles": {"available": True, "note": None},
                            "conversation_history": {"available": True, "note": None},
                            "payments": {"available": False, "note": "Requires STRIPE_SECRET_KEY"},
                            "analytics": {"available": True, "note": None},
                            "web_research": {"available": False, "note": "Requires SERP_API_KEY or TAVILY_API_KEY"},
                        },
                    }
                }
            },
        }
    },
)
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Probes database and Redis connectivity, enumerates LLM provider
    configuration, and reports feature availability.  Does not require
    authentication so monitoring tools can call it freely.
    """
    settings = get_settings()

    db_status = await _check_database()
    redis_status = await _check_redis()
    llm_status = _get_llm_providers_status(settings)
    features = _get_feature_availability(settings)
    status = _overall_status(db_status, redis_status, settings)

    return {
        "status": status,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "llm_providers": llm_status,
        },
        "features": features,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="""
Lightweight readiness probe for container orchestration (Kubernetes, ECS, etc.).

Returns **200** if the server is ready to accept traffic, or **503** if it is not.
This endpoint performs no external calls (no DB, no Redis) -- it only confirms
that the Python process has started and at least one LLM provider key is present.
    """,
    responses={
        200: {
            "description": "Server is ready",
            "content": {
                "application/json": {
                    "example": {"ready": True}
                }
            },
        },
        503: {
            "description": "Server is not ready",
            "content": {
                "application/json": {
                    "example": {"ready": False, "reason": "No LLM provider configured"}
                }
            },
        },
    },
)
async def readiness_probe():
    """
    Minimal readiness check for container orchestrators.

    No external calls are made.  Returns 200 when the server can accept
    requests, or 503 when critical configuration is missing.
    """
    settings = get_settings()

    if not settings.has_llm_provider:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "reason": "No LLM provider configured",
            },
        )

    return {"ready": True}


# =============================================================================
# Detailed per-service health checks (authentication required)
# =============================================================================


async def _get_full_database_status() -> Dict[str, Any]:
    """
    Full database status with configuration details.
    Used by the authenticated /health/db endpoint.
    """
    database_url = get_database_url()
    if not database_url:
        return {
            "configured": False,
            "connected": False,
            "error": "DATABASE_URL not set",
        }

    try:
        start = time.monotonic()
        response = await db_fetchrow("SELECT 1 AS ok")
        latency_ms = round((time.monotonic() - start) * 1000, 2)

        return {
            "configured": True,
            "connected": bool(response),
            "latency_ms": latency_ms,
            "tables_accessible": True,
        }
    except Exception as e:
        logger.warning("Database health check failed: %s", e)
        return {
            "configured": True,
            "connected": False,
            "error": "Database connection failed",
        }


def _get_full_stripe_status() -> Dict[str, Any]:
    """Full Stripe status with connectivity test."""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not stripe_key:
        return {
            "configured": False,
            "connected": False,
            "mode": None,
            "error": "STRIPE_SECRET_KEY not set",
        }

    if stripe_key.startswith("sk_test_"):
        mode = "test"
    elif stripe_key.startswith("sk_live_"):
        mode = "live"
    else:
        mode = "unknown"

    try:
        import stripe

        stripe.api_key = stripe_key

        start = time.monotonic()
        stripe.Account.retrieve()
        latency_ms = round((time.monotonic() - start) * 1000, 2)

        return {
            "configured": True,
            "connected": True,
            "mode": mode,
            "webhook_configured": bool(webhook_secret),
            "latency_ms": latency_ms,
        }
    except ImportError:
        return {
            "configured": True,
            "connected": False,
            "mode": mode,
            "webhook_configured": bool(webhook_secret),
            "error": "stripe package not installed",
        }
    except Exception as e:
        logger.warning("Stripe health check failed: %s", e)
        return {
            "configured": True,
            "connected": False,
            "mode": mode,
            "webhook_configured": bool(webhook_secret),
            "error": "Stripe connection failed",
        }


def _get_full_sentry_status() -> Dict[str, Any]:
    """Full Sentry status."""
    try:
        client = sentry_sdk.get_client()
        dsn = os.environ.get("SENTRY_DSN")
        environment = os.environ.get("SENTRY_ENVIRONMENT", "development")

        return {
            "configured": bool(dsn),
            "active": client.is_active() if dsn else False,
            "environment": environment if dsn else None,
            "dsn_set": bool(dsn),
        }
    except Exception as e:
        logger.warning(f"Sentry status check failed: {e}")
        return {
            "configured": False,
            "active": False,
            "environment": None,
            "dsn_set": False,
            "error": "Sentry status check failed",
        }


async def _get_full_redis_status() -> Dict[str, Any]:
    """Full Redis status with version info."""
    redis_url = os.environ.get("REDIS_URL")

    if not redis_url:
        return {
            "configured": False,
            "connected": False,
            "error": "REDIS_URL not set",
        }

    try:
        client = await _redis_client_instance.get_client()
        if client is None:
            return {
                "configured": True,
                "connected": False,
                "error": "Redis client not initialized",
            }

        start = time.monotonic()
        await client.ping()
        latency_ms = round((time.monotonic() - start) * 1000, 2)

        info = await client.info("server")

        return {
            "configured": True,
            "connected": True,
            "latency_ms": latency_ms,
            "version": info.get("redis_version", "unknown"),
        }
    except ImportError:
        return {
            "configured": True,
            "connected": False,
            "error": "redis package not installed",
        }
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        return {
            "configured": True,
            "connected": False,
            "error": "Redis connection failed",
        }


@router.get("/health/db")
async def database_health(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Detailed database health check.

    Returns comprehensive information about Postgres (Neon) connectivity.
    """
    db_status = await _get_full_database_status()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
    }


@router.get("/health/stripe")
async def stripe_health(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Detailed Stripe health check.

    Returns comprehensive information about Stripe payment configuration.
    """
    stripe_status = _get_full_stripe_status()

    price_ids_configured = {
        "starter": bool(os.environ.get("STRIPE_PRICE_ID_STARTER")),
        "pro": bool(os.environ.get("STRIPE_PRICE_ID_PRO")),
        "business": bool(os.environ.get("STRIPE_PRICE_ID_BUSINESS")),
    }
    stripe_status["price_ids_configured"] = price_ids_configured

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stripe": stripe_status,
    }


@router.get("/health/sentry")
async def sentry_health(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Detailed Sentry configuration status.

    Returns comprehensive information about Sentry error tracking configuration.
    """
    sentry_status = _get_full_sentry_status()

    sentry_status["traces_sample_rate"] = float(
        os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    sentry_status["profiles_sample_rate"] = float(
        os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
    )
    sentry_status["release"] = os.environ.get("SENTRY_RELEASE", "blog-ai@1.0.0")
    sentry_status["server_name"] = os.environ.get("SERVER_NAME", "blog-ai-api")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sentry": sentry_status,
    }


@router.get("/health/redis")
async def redis_health(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Detailed Redis health check.

    Returns comprehensive information about Redis connectivity and status.
    """
    redis_status = await _get_full_redis_status()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis": redis_status,
    }


@router.get("/health/cache")
async def cache_stats(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.

    Returns hit rates and sizes for all caches.
    """
    from src.utils.cache import get_content_analysis_cache, get_voice_analysis_cache

    content_cache = get_content_analysis_cache()
    voice_cache = get_voice_analysis_cache()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "caches": {
            "content_analysis": content_cache.stats,
            "voice_analysis": voice_cache.stats,
        },
    }


@router.post("/health/cache/cleanup")
async def cleanup_caches(_: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Cleanup expired cache entries.

    Returns count of removed entries from each cache.
    """
    from src.utils.cache import get_content_analysis_cache, get_voice_analysis_cache

    content_cache = get_content_analysis_cache()
    voice_cache = get_voice_analysis_cache()

    content_cleaned = content_cache.cleanup_expired()
    voice_cleaned = voice_cache.cleanup_expired()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cleaned": {
            "content_analysis": content_cleaned,
            "voice_analysis": voice_cleaned,
        },
    }


# =============================================================================
# Root endpoint
# =============================================================================


@router.get(
    "/",
    summary="API information",
    description="Root endpoint providing API information and documentation links.",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Welcome to the Blog AI API",
                        "version": "1.0.0",
                        "api_version": "v1",
                        "docs": "/docs",
                        "health": "/health",
                        "ready": "/ready",
                        "api_base": "/api/v1",
                    }
                }
            },
        }
    },
)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Blog AI API",
        "version": APP_VERSION,
        "api_version": "v1",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "api_base": "/api/v1",
    }
