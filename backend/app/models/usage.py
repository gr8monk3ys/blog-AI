"""
Pydantic models for usage tracking and tier management.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""

    user_hash: str
    tier: str
    daily_count: int
    daily_limit: int
    daily_remaining: int
    monthly_count: int
    monthly_limit: int
    monthly_remaining: int
    tokens_used_today: int
    tokens_used_month: int
    is_limit_reached: bool
    percentage_used_daily: float
    percentage_used_monthly: float
    reset_daily_at: str
    reset_monthly_at: str


class TierInfoResponse(BaseModel):
    """Response model for tier information."""

    name: str
    daily_limit: int
    monthly_limit: int
    features_enabled: List[str]
    price_monthly: float
    price_yearly: float
    description: str


class AllTiersResponse(BaseModel):
    """Response model for all tier information."""

    tiers: List[TierInfoResponse]
    current_tier: str


class UpgradeTierRequest(BaseModel):
    """Request model for upgrading user tier."""

    tier: str = Field(..., pattern=r"^(free|pro|enterprise)$")


class UsageLimitErrorResponse(BaseModel):
    """Response model for usage limit errors."""

    success: bool = False
    error: str
    tier: str
    limit_type: str  # "daily" or "monthly"
    upgrade_url: str = "/pricing"
    daily_limit: int
    daily_remaining: int
    monthly_limit: int
    monthly_remaining: int
