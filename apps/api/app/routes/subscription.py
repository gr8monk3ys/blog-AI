"""
Subscription status endpoint.

Provides a unified view of the user's subscription plan, usage, and renewal
date by reading from the local database (not Stripe API). This is the
source of truth for access control and is kept in sync by webhook handlers.

Authorization:
- Requires valid API key / session token
"""

import logging
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from src.db import fetchrow as db_fetchrow, is_database_configured
from src.types.usage import get_tier_config
from src.usage.quota_service import get_quota_service

from ..auth import verify_api_key
from ..middleware.quota_check import require_business_tier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["payments"])


@router.get(
    "/status",
    summary="Get subscription status with usage",
    description="""
Returns the authenticated user's current subscription plan, usage statistics,
and renewal date.

This endpoint reads from the local database (kept in sync by Stripe webhooks)
rather than calling the Stripe API directly, so it is fast and always available.

**Response fields:**
- `plan` - Current tier name (free, starter, pro, business)
- `status` - Stripe subscription status or "none" for free users
- `usage` - Current period usage and limits
- `renewal_date` - ISO timestamp of next billing cycle (null for free)
- `cancel_at_period_end` - Whether cancellation is scheduled
- `payment_status` - Payment health indicator (current, grace_period, payment_failed)
""",
    responses={
        200: {"description": "Subscription status with usage"},
        500: {"description": "Internal server error"},
    },
)
async def get_subscription_status_with_usage(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get the current user's plan, usage, and renewal date.

    Reads from the local database rather than the Stripe API for speed
    and reliability. The database is kept in sync by webhook handlers.

    Args:
        user_id: Authenticated user ID from API key / session

    Returns:
        Dictionary with plan, usage, renewal_date, and payment health.
    """
    try:
        # Get usage stats from quota service (source of truth for tier + usage)
        quota_service = get_quota_service()
        usage_stats = await quota_service.get_usage_stats(user_id)

        tier_config = get_tier_config(usage_stats.tier)

        # Build base response from quota data
        response: Dict = {
            "success": True,
            "plan": usage_stats.tier.value,
            "plan_name": tier_config.name,
            "status": "none",
            "usage": {
                "current": usage_stats.current_usage,
                "limit": usage_stats.quota_limit,
                "remaining": usage_stats.remaining,
                "percentage_used": usage_stats.percentage_used,
                "daily_current": usage_stats.daily_usage,
                "daily_limit": usage_stats.daily_limit,
                "daily_remaining": usage_stats.daily_remaining,
                "tokens_used": usage_stats.tokens_used,
                "is_exceeded": usage_stats.is_quota_exceeded,
            },
            "period_start": usage_stats.period_start.isoformat() + "Z",
            "period_end": usage_stats.reset_date.isoformat() + "Z",
            "renewal_date": None,
            "cancel_at_period_end": False,
            "payment_status": "current",
        }

        # Enrich with subscription details from the database if available
        if is_database_configured():
            sub_row = await db_fetchrow(
                """
                SELECT
                    ss.status,
                    ss.current_period_end,
                    ss.cancel_at_period_end,
                    ss.payment_status,
                    ss.tier
                FROM stripe_subscriptions ss
                WHERE ss.user_id = $1
                  AND ss.status IN ('active', 'trialing', 'past_due')
                ORDER BY ss.updated_at DESC
                LIMIT 1
                """,
                user_id,
            )

            if sub_row:
                response["status"] = sub_row["status"] or "active"
                response["cancel_at_period_end"] = bool(
                    sub_row.get("cancel_at_period_end", False)
                )
                response["payment_status"] = sub_row.get("payment_status", "current") or "current"

                period_end = sub_row.get("current_period_end")
                if period_end:
                    if isinstance(period_end, datetime):
                        response["renewal_date"] = period_end.isoformat() + "Z"
                    elif isinstance(period_end, (int, float)):
                        response["renewal_date"] = (
                            datetime.fromtimestamp(period_end, tz=timezone.utc).isoformat()
                        )

        logger.info(
            f"Subscription status retrieved for user {user_id[:8]}...: "
            f"plan={response['plan']}, status={response['status']}"
        )

        return response

    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve subscription status",
                "success": False,
            },
        )


@router.post(
    "/reconcile",
    summary="Reconcile subscriptions with Stripe",
    description="""
Compares all paid-tier users in the database against their actual Stripe
subscription status and fixes mismatches. This catches cases where a Stripe
webhook was missed (e.g. cancellation event lost) and a user retained a
higher tier than they should have.

**Requires Business tier (admin only).**

Query parameters:
- `skip_manual_overrides` - Skip users with no Stripe subscription ID (default: true)
- `dry_run` - Detect mismatches without applying fixes (default: false)
""",
    responses={
        200: {"description": "Reconciliation summary"},
        403: {"description": "Insufficient tier"},
        500: {"description": "Internal server error"},
    },
)
async def reconcile_subscriptions(
    skip_manual_overrides: bool = True,
    dry_run: bool = False,
    user_id: str = Depends(require_business_tier),
) -> Dict:
    """
    Trigger a reconciliation of Stripe subscriptions against the database.

    Scans all users with paid tiers, verifies their Stripe subscription
    status, and corrects any mismatches found.

    Args:
        skip_manual_overrides: If True, skip users without a Stripe subscription
            (they were manually upgraded and should not be touched).
        dry_run: If True, report mismatches without applying fixes.
        user_id: Authenticated user ID (must be Business tier).

    Returns:
        Summary of reconciliation results.
    """
    try:
        from src.payments.subscription_sync import get_sync_service

        sync_service = get_sync_service()
        result = await sync_service.reconcile_subscriptions(
            skip_manual_overrides=skip_manual_overrides,
            dry_run=dry_run,
        )

        return {
            "success": True,
            **result,
        }

    except Exception as e:
        logger.error(f"Reconciliation endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to run subscription reconciliation",
                "success": False,
            },
        )
