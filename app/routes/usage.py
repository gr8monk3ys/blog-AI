"""
Usage tracking and tier management endpoints.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

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

from ..auth import verify_api_key
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
                error=str(e),
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
