"""
Usage tracking and tier management endpoints.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.types.usage import (
    SubscriptionTier,
    UsageStats as NewUsageStats,
    get_all_tiers as get_all_tier_configs,
    get_tier_config,
)
from src.usage import (
    TIER_CONFIGS,
    UsageLimitExceeded,
    UsageStats,
    UsageTier,
    check_usage_limit,
    get_tier_info,
    get_usage_stats,
    usage_limiter,
)
from src.usage.quota_service import (
    QuotaExceeded,
    get_quota_service,
    get_usage_stats as get_quota_stats,
)

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..models import (
    AllTiersResponse,
    TierInfoResponse,
    UpgradeTierRequest,
    UsageLimitErrorResponse,
    UsageStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage"])


def _stats_to_response(stats: UsageStats) -> UsageStatsResponse:
    """Convert UsageStats dataclass to response model."""
    return UsageStatsResponse(
        user_hash=stats.user_hash[:8] + "...",  # Truncate for privacy
        tier=stats.tier.value,
        daily_count=stats.daily_count,
        daily_limit=stats.daily_limit,
        daily_remaining=stats.daily_remaining,
        monthly_count=stats.monthly_count,
        monthly_limit=stats.monthly_limit,
        monthly_remaining=stats.monthly_remaining,
        tokens_used_today=stats.tokens_used_today,
        tokens_used_month=stats.tokens_used_month,
        is_limit_reached=stats.is_limit_reached,
        percentage_used_daily=stats.percentage_used_daily,
        percentage_used_monthly=stats.percentage_used_monthly,
        reset_daily_at=stats.reset_daily_at,
        reset_monthly_at=stats.reset_monthly_at,
    )


@router.get("/stats")
async def get_user_usage_stats(
    user_id: str = Depends(verify_api_key),
) -> UsageStatsResponse:
    """
    Get usage statistics for the authenticated user.

    Returns current usage counts, limits, and remaining quota.
    """
    logger.info(f"Usage stats requested by user: {user_id}")
    stats = get_usage_stats(user_id)
    return _stats_to_response(stats)


@router.get("/check")
async def check_user_limit(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Check if user has remaining usage quota.

    Returns remaining count or raises 429 if limit reached.
    """
    try:
        remaining = check_usage_limit(user_id)
        stats = get_usage_stats(user_id)
        return {
            "success": True,
            "can_generate": True,
            "remaining_today": remaining,
            "tier": stats.tier.value,
            "daily_limit": stats.daily_limit,
            "monthly_remaining": stats.monthly_remaining,
        }
    except UsageLimitExceeded as e:
        stats = get_usage_stats(user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=UsageLimitErrorResponse(
                error=sanitize_error_message(str(e)),
                tier=e.tier.value,
                limit_type=e.limit_type,
                daily_limit=stats.daily_limit,
                daily_remaining=stats.daily_remaining,
                monthly_limit=stats.monthly_limit,
                monthly_remaining=stats.monthly_remaining,
            ).model_dump(),
        )


@router.get("/tiers")
async def get_all_tiers(
    user_id: str = Depends(verify_api_key),
) -> AllTiersResponse:
    """
    Get information about all available tiers.

    Returns configuration for each tier including limits and pricing.
    """
    tiers = []
    for tier in UsageTier:
        config = get_tier_info(tier)
        tiers.append(TierInfoResponse(
            name=config.name,
            daily_limit=config.daily_limit,
            monthly_limit=config.monthly_limit,
            features_enabled=config.features_enabled,
            price_monthly=config.price_monthly,
            price_yearly=config.price_yearly,
            description=config.description,
        ))

    current_tier = usage_limiter.get_user_tier(user_id)

    return AllTiersResponse(
        tiers=tiers,
        current_tier=current_tier.value,
    )


@router.get("/tier/{tier_name}")
async def get_tier_details(
    tier_name: str,
    user_id: str = Depends(verify_api_key),
) -> TierInfoResponse:
    """
    Get detailed information about a specific tier.

    Args:
        tier_name: The tier name (free, pro, enterprise).

    Returns:
        Tier configuration and features.
    """
    try:
        tier = UsageTier(tier_name.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier_name}. Must be one of: free, pro, enterprise",
        )

    config = get_tier_info(tier)
    return TierInfoResponse(
        name=config.name,
        daily_limit=config.daily_limit,
        monthly_limit=config.monthly_limit,
        features_enabled=config.features_enabled,
        price_monthly=config.price_monthly,
        price_yearly=config.price_yearly,
        description=config.description,
    )


@router.post("/upgrade")
async def upgrade_user_tier(
    request: UpgradeTierRequest,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Upgrade user to a new tier.

    Note: In production, this would integrate with a payment system.
    For now, it directly updates the tier (for testing purposes).

    Args:
        request: The upgrade request with target tier.

    Returns:
        Success status and new tier information.
    """
    try:
        new_tier = UsageTier(request.tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {request.tier}. Must be one of: free, pro, enterprise",
        )

    current_tier = usage_limiter.get_user_tier(user_id)

    # In production, verify payment before upgrading
    # For now, allow direct upgrade for testing
    usage_limiter.set_user_tier(user_id, new_tier)

    logger.info(f"User {user_id} upgraded from {current_tier.value} to {new_tier.value}")

    config = get_tier_info(new_tier)
    return {
        "success": True,
        "previous_tier": current_tier.value,
        "new_tier": new_tier.value,
        "daily_limit": config.daily_limit,
        "monthly_limit": config.monthly_limit,
        "features_enabled": config.features_enabled,
        "message": f"Successfully upgraded to {config.name} tier",
    }


@router.get("/features")
async def get_user_features(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get the features available to the authenticated user based on their tier.

    Returns:
        List of enabled features and tier name.
    """
    tier = usage_limiter.get_user_tier(user_id)
    config = get_tier_info(tier)

    return {
        "tier": tier.value,
        "tier_name": config.name,
        "features_enabled": config.features_enabled,
        "bulk_generation_enabled": "bulk_generation" in config.features_enabled,
        "research_enabled": "research_mode" in config.features_enabled,
        "api_access_enabled": "api_access" in config.features_enabled,
    }


# =============================================================================
# New Quota-based Endpoints (using Supabase when available)
# =============================================================================


@router.get("/quota/stats")
async def get_quota_usage_stats(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get current usage statistics using the new quota system.

    Returns usage stats including:
    - Current usage count for the billing period
    - Monthly quota limit based on subscription tier
    - Remaining generations
    - Daily usage and limits
    - Period start/end dates
    - Percentage of quota used
    """
    logger.info(f"Quota stats requested by user: {user_id[:8]}...")

    try:
        stats = await get_quota_stats(user_id)

        return {
            "success": True,
            "user_id": user_id[:8] + "...",
            "tier": stats.tier.value,
            "tier_name": get_tier_config(stats.tier).name,
            "current_usage": stats.current_usage,
            "quota_limit": stats.quota_limit,
            "remaining": stats.remaining,
            "daily_usage": stats.daily_usage,
            "daily_limit": stats.daily_limit,
            "daily_remaining": stats.daily_remaining,
            "tokens_used": stats.tokens_used,
            "percentage_used": stats.percentage_used,
            "is_quota_exceeded": stats.is_quota_exceeded,
            "period_start": stats.period_start.isoformat(),
            "reset_date": stats.reset_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting quota stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics",
        )


@router.get("/quota/check")
async def check_quota_available(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Check if user has available quota for generation.

    Returns:
    - success: Whether the check succeeded
    - has_quota: Whether user can generate more content
    - remaining: Number of remaining generations
    - tier: Current subscription tier
    - reset_date: When quota resets

    If quota is exceeded, returns 429 with upgrade information.
    """
    try:
        quota_service = get_quota_service()
        await quota_service.check_quota(user_id)

        stats = await get_quota_stats(user_id)

        return {
            "success": True,
            "has_quota": True,
            "remaining": stats.remaining,
            "daily_remaining": stats.daily_remaining,
            "tier": stats.tier.value,
            "quota_limit": stats.quota_limit,
            "reset_date": stats.reset_date.isoformat(),
        }

    except QuotaExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "has_quota": False,
                "error": e.message,
                "error_code": "QUOTA_EXCEEDED",
                "tier": e.tier.value,
                "current_usage": e.current_usage,
                "quota_limit": e.quota_limit,
                "reset_date": e.reset_date.isoformat(),
                "upgrade_url": "/pricing",
            },
        )


@router.get("/quota/breakdown")
async def get_usage_breakdown(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get detailed usage breakdown by operation type.

    Returns counts for each type of generation:
    - blog: Blog post generations
    - book: Book generations
    - batch: Batch job items
    - remix: Content remix operations
    - tool: Individual tool uses
    - total: Total across all types
    """
    logger.info(f"Usage breakdown requested by user: {user_id[:8]}...")

    try:
        quota_service = get_quota_service()
        breakdown = await quota_service.get_usage_breakdown(user_id)
        stats = await get_quota_stats(user_id)

        return {
            "success": True,
            "user_id": user_id[:8] + "...",
            "tier": stats.tier.value,
            "period_start": stats.period_start.isoformat(),
            "period_end": stats.reset_date.isoformat(),
            "breakdown": breakdown,
            "quota_limit": stats.quota_limit,
            "remaining": stats.remaining,
        }

    except Exception as e:
        logger.error(f"Error getting usage breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage breakdown",
        )


@router.get("/quota/tiers")
async def get_subscription_tiers(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get all available subscription tiers with their limits.

    Returns configuration for each tier:
    - free: 5 generations/month
    - starter: 50 generations/month
    - pro: 200 generations/month
    - business: 1000 generations/month

    Includes features, pricing, and descriptions.
    """
    try:
        stats = await get_quota_stats(user_id)

        tiers = []
        for tier_config in get_all_tier_configs():
            tiers.append({
                "tier": tier_config.tier.value,
                "name": tier_config.name,
                "monthly_limit": tier_config.monthly_limit,
                "daily_limit": tier_config.daily_limit,
                "features": tier_config.features,
                "price_monthly": tier_config.price_monthly,
                "price_yearly": tier_config.price_yearly,
                "description": tier_config.description,
                "is_current": tier_config.tier == stats.tier,
            })

        return {
            "success": True,
            "current_tier": stats.tier.value,
            "tiers": tiers,
        }

    except Exception as e:
        logger.error(f"Error getting subscription tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription tiers",
        )


@router.post("/quota/upgrade")
async def upgrade_subscription_tier(
    request: UpgradeTierRequest,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Upgrade user to a new subscription tier.

    Note: In production, this would integrate with a payment system
    (e.g., Stripe). For now, it directly updates the tier for testing.

    Args:
        request: The upgrade request with target tier.

    Returns:
        Success status and new tier information.
    """
    # Map the legacy tier names to new subscription tiers
    tier_mapping = {
        "free": SubscriptionTier.FREE,
        "starter": SubscriptionTier.STARTER,
        "pro": SubscriptionTier.PRO,
        "business": SubscriptionTier.BUSINESS,
        # Legacy mappings
        "enterprise": SubscriptionTier.BUSINESS,
    }

    tier_str = request.tier.lower()
    if tier_str not in tier_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {request.tier}. Must be one of: free, starter, pro, business",
        )

    new_tier = tier_mapping[tier_str]

    try:
        quota_service = get_quota_service()
        current_stats = await get_quota_stats(user_id)
        current_tier = current_stats.tier

        # In production, verify payment before upgrading
        await quota_service.set_user_tier(user_id, new_tier)

        logger.info(f"User {user_id[:8]}... upgraded from {current_tier.value} to {new_tier.value}")

        new_config = get_tier_config(new_tier)

        return {
            "success": True,
            "previous_tier": current_tier.value,
            "new_tier": new_tier.value,
            "tier_name": new_config.name,
            "monthly_limit": new_config.monthly_limit,
            "daily_limit": new_config.daily_limit,
            "features": new_config.features,
            "message": f"Successfully upgraded to {new_config.name} tier",
        }

    except Exception as e:
        logger.error(f"Error upgrading tier: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade subscription tier",
        )
