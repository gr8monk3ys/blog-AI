"""
Health check and root endpoints.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

import sentry_sdk
from fastapi import APIRouter

from src.storage import redis_client, job_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def get_database_status() -> Dict[str, Any]:
    """
    Check Supabase database connectivity.

    Performs a simple query to verify the database is accessible.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        return {
            "configured": False,
            "connected": False,
            "error": "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set",
        }

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)

        # Simple query to verify connection
        start_time = datetime.now()
        response = client.table("tier_limits").select("tier").limit(1).execute()
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "configured": True,
            "connected": True,
            "latency_ms": round(latency_ms, 2),
            "tables_accessible": True,
        }

    except ImportError:
        return {
            "configured": True,
            "connected": False,
            "error": "supabase package not installed",
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {
            "configured": True,
            "connected": False,
            "error": str(e)[:100],  # Truncate for safety
        }


def get_stripe_status() -> Dict[str, Any]:
    """
    Check Stripe configuration and API connectivity.
    """
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not stripe_key:
        return {
            "configured": False,
            "connected": False,
            "mode": None,
            "error": "STRIPE_SECRET_KEY not set",
        }

    # Determine mode from key prefix
    if stripe_key.startswith("sk_test_"):
        mode = "test"
    elif stripe_key.startswith("sk_live_"):
        mode = "live"
    else:
        mode = "unknown"

    try:
        import stripe

        stripe.api_key = stripe_key

        # Simple API call to verify connection
        start_time = datetime.now()
        stripe.Account.retrieve()
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "configured": True,
            "connected": True,
            "mode": mode,
            "webhook_configured": bool(webhook_secret),
            "latency_ms": round(latency_ms, 2),
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
        logger.warning(f"Stripe health check failed: {e}")
        return {
            "configured": True,
            "connected": False,
            "mode": mode,
            "webhook_configured": bool(webhook_secret),
            "error": str(e)[:100],
        }


def get_sentry_status() -> Dict[str, Any]:
    """
    Get the current Sentry configuration status.

    Returns information about whether Sentry is configured and active.
    """
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
        return {
            "configured": False,
            "active": False,
            "environment": None,
            "dsn_set": False,
            "error": str(e),
        }


async def get_redis_status() -> Dict[str, Any]:
    """
    Check Redis connectivity and health.

    Returns information about Redis connection status and latency.
    """
    redis_url = os.environ.get("REDIS_URL")

    if not redis_url:
        return {
            "configured": False,
            "connected": False,
            "error": "REDIS_URL not set",
        }

    try:
        # Check if redis client is available
        if redis_client is None:
            return {
                "configured": True,
                "connected": False,
                "error": "Redis client not initialized",
            }

        # Ping Redis to verify connection
        start_time = datetime.now()
        await redis_client.ping()
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Get basic info
        info = await redis_client.info("server")

        return {
            "configured": True,
            "connected": True,
            "latency_ms": round(latency_ms, 2),
            "version": info.get("redis_version", "unknown"),
        }

    except ImportError:
        return {
            "configured": True,
            "connected": False,
            "error": "redis package not installed",
        }
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return {
            "configured": True,
            "connected": False,
            "error": str(e)[:100],
        }


@router.get(
    "/health",
    summary="System health check",
    description="""
Health check endpoint for monitoring and load balancers.

Returns overall system health including:
- Database connectivity status
- Stripe payment service status
- Sentry error tracking status
- Redis cache status
- Service latency metrics

**Authentication**: Not required. This endpoint is public for load balancer health checks.
    """,
    responses={
        200: {
            "description": "Health status retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-24T12:00:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "services": {
                            "database": {"status": "up", "latency_ms": 5.2},
                            "stripe": {"status": "up", "mode": "live"},
                            "sentry": {"status": "up"},
                            "redis": {"status": "up", "latency_ms": 1.2}
                        }
                    }
                }
            }
        }
    }
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns overall system health including all critical services.
    This is the primary endpoint for load balancer health checks.
    """
    db_status = await get_database_status()
    stripe_status = get_stripe_status()
    sentry_status = get_sentry_status()
    redis_status = await get_redis_status()

    # Determine overall health
    # Critical: database must be connected for core functionality
    # Non-critical: Stripe (payments can be degraded), Sentry (monitoring), Redis (caching)
    is_healthy = db_status.get("connected", False) or not db_status.get("configured", False)

    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": os.environ.get("SENTRY_RELEASE", "1.0.0"),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "services": {
            "database": {
                "status": "up" if db_status.get("connected") else ("unconfigured" if not db_status.get("configured") else "down"),
                "latency_ms": db_status.get("latency_ms"),
            },
            "stripe": {
                "status": "up" if stripe_status.get("connected") else ("unconfigured" if not stripe_status.get("configured") else "down"),
                "mode": stripe_status.get("mode"),
            },
            "sentry": {
                "status": "up" if sentry_status.get("active") else ("unconfigured" if not sentry_status.get("configured") else "down"),
            },
            "redis": {
                "status": "up" if redis_status.get("connected") else ("unconfigured" if not redis_status.get("configured") else "down"),
                "latency_ms": redis_status.get("latency_ms"),
            },
        },
    }


@router.get("/health/db")
async def database_health() -> Dict[str, Any]:
    """
    Detailed database health check.

    Returns comprehensive information about Supabase database connectivity.
    """
    db_status = await get_database_status()

    return {
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
    }


@router.get("/health/stripe")
async def stripe_health() -> Dict[str, Any]:
    """
    Detailed Stripe health check.

    Returns comprehensive information about Stripe payment configuration.
    """
    stripe_status = get_stripe_status()

    # Add price ID configuration check
    price_ids_configured = {
        "starter": bool(os.environ.get("STRIPE_PRICE_ID_STARTER")),
        "pro": bool(os.environ.get("STRIPE_PRICE_ID_PRO")),
        "business": bool(os.environ.get("STRIPE_PRICE_ID_BUSINESS")),
    }
    stripe_status["price_ids_configured"] = price_ids_configured

    return {
        "timestamp": datetime.now().isoformat(),
        "stripe": stripe_status,
    }


@router.get("/health/sentry")
async def sentry_health() -> Dict[str, Any]:
    """
    Detailed Sentry configuration status.

    Returns comprehensive information about Sentry error tracking configuration.
    """
    sentry_status = get_sentry_status()

    # Add additional configuration details
    sentry_status["traces_sample_rate"] = float(
        os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    sentry_status["profiles_sample_rate"] = float(
        os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
    )
    sentry_status["release"] = os.environ.get("SENTRY_RELEASE", "blog-ai@1.0.0")
    sentry_status["server_name"] = os.environ.get("SERVER_NAME", "blog-ai-api")

    return {
        "timestamp": datetime.now().isoformat(),
        "sentry": sentry_status,
    }


@router.get("/health/redis")
async def redis_health() -> Dict[str, Any]:
    """
    Detailed Redis health check.

    Returns comprehensive information about Redis connectivity and status.
    """
    redis_status = await get_redis_status()

    return {
        "timestamp": datetime.now().isoformat(),
        "redis": redis_status,
    }


@router.get("/health/cache")
async def cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.

    Returns hit rates and sizes for all caches.
    """
    from src.utils.cache import get_content_analysis_cache, get_voice_analysis_cache

    content_cache = get_content_analysis_cache()
    voice_cache = get_voice_analysis_cache()

    return {
        "timestamp": datetime.now().isoformat(),
        "caches": {
            "content_analysis": content_cache.stats,
            "voice_analysis": voice_cache.stats,
        },
    }


@router.post("/health/cache/cleanup")
async def cleanup_caches() -> Dict[str, Any]:
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
        "timestamp": datetime.now().isoformat(),
        "cleaned": {
            "content_analysis": content_cleaned,
            "voice_analysis": voice_cleaned,
        },
    }


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
                        "api_base": "/api/v1"
                    }
                }
            }
        }
    }
)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Blog AI API",
        "version": "1.0.0",
        "api_version": "v1",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1",
    }
