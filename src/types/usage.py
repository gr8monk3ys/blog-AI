"""
Pydantic models for usage quota tracking and subscription tiers.

This module defines the data models for:
- Subscription tiers with quota limits
- Usage records for tracking generation counts
- Usage statistics for API responses
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SubscriptionTier(str, Enum):
    """
    Available subscription tiers with associated quota limits.

    Each tier defines monthly generation limits for content creation.
    """
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


class TierConfig(BaseModel):
    """Configuration for a subscription tier."""

    tier: SubscriptionTier
    name: str
    monthly_limit: int = Field(
        ...,
        description="Maximum generations allowed per month (-1 for unlimited)"
    )
    daily_limit: int = Field(
        default=-1,
        description="Maximum generations allowed per day (-1 for unlimited)"
    )
    features: List[str] = Field(
        default_factory=list,
        description="List of features enabled for this tier"
    )
    price_monthly: float = Field(
        default=0.0,
        description="Monthly price in USD"
    )
    price_yearly: float = Field(
        default=0.0,
        description="Yearly price in USD"
    )
    description: str = Field(
        default="",
        description="Human-readable tier description"
    )


# Tier configurations matching the SaaS pricing
TIER_CONFIGS: Dict[SubscriptionTier, TierConfig] = {
    SubscriptionTier.FREE: TierConfig(
        tier=SubscriptionTier.FREE,
        name="Free",
        monthly_limit=5,
        daily_limit=2,
        features=[
            "blog_generation",
            "basic_tools",
        ],
        price_monthly=0.0,
        price_yearly=0.0,
        description="Perfect for trying out Blog AI",
    ),
    SubscriptionTier.STARTER: TierConfig(
        tier=SubscriptionTier.STARTER,
        name="Starter",
        monthly_limit=50,
        daily_limit=10,
        features=[
            "blog_generation",
            "book_generation",
            "basic_tools",
            "export_formats",
        ],
        price_monthly=19.0,
        price_yearly=190.0,
        description="For individuals getting started with content creation",
    ),
    SubscriptionTier.PRO: TierConfig(
        tier=SubscriptionTier.PRO,
        name="Pro",
        monthly_limit=200,
        daily_limit=50,
        features=[
            "blog_generation",
            "book_generation",
            "bulk_generation",
            "all_tools",
            "research_mode",
            "brand_voice",
            "remix",
            "priority_support",
        ],
        price_monthly=49.0,
        price_yearly=490.0,
        description="For content creators and marketers",
    ),
    SubscriptionTier.BUSINESS: TierConfig(
        tier=SubscriptionTier.BUSINESS,
        name="Business",
        monthly_limit=1000,
        daily_limit=-1,  # Unlimited daily
        features=[
            "blog_generation",
            "book_generation",
            "bulk_generation",
            "batch_processing",
            "all_tools",
            "research_mode",
            "brand_voice",
            "remix",
            "api_access",
            "custom_integrations",
            "dedicated_support",
            "team_collaboration",
        ],
        price_monthly=149.0,
        price_yearly=1490.0,
        description="For teams and businesses",
    ),
}


class UsageRecord(BaseModel):
    """
    A single usage record tracking a generation operation.

    Stored in the database to track all generation activity.
    """

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the usage record (UUID)"
    )
    user_id: str = Field(
        ...,
        description="User identifier"
    )
    operation_type: str = Field(
        ...,
        description="Type of operation (blog, book, batch, remix, tool)"
    )
    tokens_used: int = Field(
        default=0,
        description="Number of tokens consumed"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the operation occurred"
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Additional metadata about the operation"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageStats(BaseModel):
    """
    Current usage statistics for a user.

    Returned by the usage stats API endpoint.
    """

    user_id: str = Field(
        ...,
        description="User identifier"
    )
    tier: SubscriptionTier = Field(
        ...,
        description="Current subscription tier"
    )
    current_usage: int = Field(
        ...,
        description="Number of generations used in current period"
    )
    quota_limit: int = Field(
        ...,
        description="Maximum generations allowed in current period"
    )
    remaining: int = Field(
        ...,
        description="Remaining generations in current period"
    )
    daily_usage: int = Field(
        default=0,
        description="Number of generations used today"
    )
    daily_limit: int = Field(
        default=-1,
        description="Daily generation limit (-1 for unlimited)"
    )
    daily_remaining: int = Field(
        default=-1,
        description="Remaining daily generations (-1 for unlimited)"
    )
    reset_date: datetime = Field(
        ...,
        description="When the monthly quota resets"
    )
    period_start: datetime = Field(
        ...,
        description="Start of the current billing period"
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens used in current period"
    )
    percentage_used: float = Field(
        default=0.0,
        description="Percentage of monthly quota used"
    )
    is_quota_exceeded: bool = Field(
        default=False,
        description="Whether the quota has been exceeded"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserQuota(BaseModel):
    """
    User quota configuration stored in the database.

    Tracks the user's subscription tier and billing period.
    """

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier (UUID)"
    )
    user_id: str = Field(
        ...,
        description="User identifier"
    )
    tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        description="Current subscription tier"
    )
    period_start: datetime = Field(
        default_factory=datetime.utcnow,
        description="Start of current billing period"
    )
    period_end: datetime = Field(
        ...,
        description="End of current billing period"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="When the quota record was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When the quota record was last updated"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuotaExceededError(BaseModel):
    """
    Error response when quota is exceeded.

    Returned with 429 Too Many Requests status.
    """

    success: bool = Field(default=False)
    error: str = Field(
        ...,
        description="Human-readable error message"
    )
    error_code: str = Field(
        default="QUOTA_EXCEEDED",
        description="Machine-readable error code"
    )
    tier: SubscriptionTier = Field(
        ...,
        description="Current subscription tier"
    )
    current_usage: int = Field(
        ...,
        description="Current usage count"
    )
    quota_limit: int = Field(
        ...,
        description="Monthly quota limit"
    )
    reset_date: datetime = Field(
        ...,
        description="When the quota resets"
    )
    upgrade_url: str = Field(
        default="/pricing",
        description="URL to upgrade subscription"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def get_tier_config(tier: SubscriptionTier) -> TierConfig:
    """
    Get the configuration for a subscription tier.

    Args:
        tier: The subscription tier.

    Returns:
        TierConfig with limits and features.
    """
    return TIER_CONFIGS.get(tier, TIER_CONFIGS[SubscriptionTier.FREE])


def get_all_tiers() -> List[TierConfig]:
    """
    Get all tier configurations.

    Returns:
        List of all TierConfig objects.
    """
    return list(TIER_CONFIGS.values())
