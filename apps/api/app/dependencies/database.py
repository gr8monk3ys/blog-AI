"""
Database availability dependencies.

Provides FastAPI dependencies that return a clear 503 error when
a database-dependent feature is called without a configured database,
instead of letting the request silently fail or return empty data.

Usage in route handlers:

    from app.dependencies.database import require_database

    @router.get("/analytics/overview")
    async def get_overview(
        _db: None = Depends(require_database("analytics")),
        auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
    ):
        ...
"""

import logging
from typing import Callable

from fastapi import HTTPException, status

from src.db import is_database_configured

logger = logging.getLogger(__name__)


def require_database(feature: str) -> Callable:
    """
    Return a FastAPI dependency that raises HTTP 503 when the database
    is not configured.

    Args:
        feature: Human-readable feature name (e.g. "analytics",
                 "brand_profiles", "conversation_history").
                 Included in the error response so the caller knows
                 which feature is unavailable and why.

    Returns:
        An async dependency function suitable for ``Depends(...)``.
    """

    async def _check_db() -> None:
        if not is_database_configured():
            logger.warning(
                "Blocked request to '%s': database not configured", feature
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": "This feature requires database configuration",
                    "error_code": "SERVICE_UNAVAILABLE",
                    "feature": feature,
                    "setup_url": "/docs/setup#database",
                },
            )

    return _check_db


def require_stripe(feature: str) -> Callable:
    """
    Return a FastAPI dependency that raises HTTP 503 when Stripe
    is not configured.

    Args:
        feature: Human-readable feature name (e.g. "payments",
                 "subscriptions").

    Returns:
        An async dependency function suitable for ``Depends(...)``.
    """
    import os

    async def _check_stripe() -> None:
        if not os.environ.get("STRIPE_SECRET_KEY"):
            logger.warning(
                "Blocked request to '%s': Stripe not configured", feature
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": "This feature requires payment processing configuration",
                    "error_code": "SERVICE_UNAVAILABLE",
                    "feature": feature,
                    "setup_url": "/docs/setup#payments",
                },
            )

    return _check_stripe
