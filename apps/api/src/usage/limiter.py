"""
Usage limiter module for tracking and enforcing usage limits.

This module provides functionality for:
- Tracking user generation counts and token usage
- Enforcing tier-based daily and monthly limits
- Retrieving usage statistics
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UsageTier(str, Enum):
    """Available usage tiers (aligned with subscription tiers)."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


@dataclass
class TierConfig:
    """Configuration for a usage tier."""
    name: str
    daily_limit: int
    monthly_limit: int
    features_enabled: List[str]
    price_monthly: float
    price_yearly: float
    description: str


# Tier configurations
TIER_CONFIGS: Dict[UsageTier, TierConfig] = {
    UsageTier.FREE: TierConfig(
        name="Free",
        daily_limit=2,
        monthly_limit=5,
        features_enabled=[
            "blog_generation",
            "basic_tools",
        ],
        price_monthly=0.0,
        price_yearly=0.0,
        description="Perfect for trying out Blog AI",
    ),
    UsageTier.STARTER: TierConfig(
        name="Starter",
        daily_limit=10,
        monthly_limit=50,
        features_enabled=[
            "blog_generation",
            "book_generation",
            "basic_tools",
            "export_formats",
        ],
        price_monthly=19.0,
        price_yearly=190.0,
        description="For individuals getting started with content creation",
    ),
    UsageTier.PRO: TierConfig(
        name="Pro",
        daily_limit=50,
        monthly_limit=200,
        features_enabled=[
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
        description="For content creators and marketers and serious writers",
    ),
    UsageTier.BUSINESS: TierConfig(
        name="Business",
        daily_limit=-1,  # Unlimited daily
        monthly_limit=1000,
        features_enabled=[
            "blog_generation",
            "book_generation",
            "bulk_generation",
            "batch_processing",
            "all_tools",
            "research_mode",
            "priority_support",
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


@dataclass
class UsageRecord:
    """A single usage record for tracking."""
    user_hash: str
    date: str
    generation_count: int = 0
    tokens_used: int = 0
    tool_usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class UsageStats:
    """Usage statistics for a user."""
    user_hash: str
    tier: UsageTier
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


class UsageLimitExceeded(Exception):
    """Exception raised when usage limit is exceeded."""

    def __init__(self, message: str, tier: UsageTier, limit_type: str):
        self.message = message
        self.tier = tier
        self.limit_type = limit_type
        super().__init__(self.message)


class UsageLimiter:
    """
    File-based usage tracking and limiting system.

    Tracks user usage per day and month, enforces tier-based limits,
    and provides usage statistics.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the usage limiter.

        Args:
            storage_dir: Directory for storing usage data.
                        Defaults to USAGE_STORAGE_DIR env var or ./data/usage
        """
        self.storage_dir = Path(
            storage_dir
            or os.environ.get("USAGE_STORAGE_DIR", "./data/usage")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, UsageRecord]] = {}
        self._user_tiers: Dict[str, UsageTier] = {}
        self._load_user_tiers()
        logger.info(f"Usage limiter initialized at: {self.storage_dir}")

    def _get_usage_file_path(self, user_hash: str, year_month: str) -> Path:
        """Get the file path for a user's monthly usage data."""
        safe_hash = "".join(c for c in user_hash if c.isalnum() or c in "_-")
        return self.storage_dir / f"{safe_hash}_{year_month}.json"

    def _get_tiers_file_path(self) -> Path:
        """Get the file path for user tier assignments."""
        return self.storage_dir / "user_tiers.json"

    def _load_user_tiers(self) -> None:
        """Load user tier assignments from disk."""
        tiers_file = self._get_tiers_file_path()
        if tiers_file.exists():
            try:
                with open(tiers_file, "r") as f:
                    data = json.load(f)
                    self._user_tiers = {k: self._parse_tier(v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._user_tiers)} user tier assignments")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading user tiers: {e}")
                self._user_tiers = {}
        else:
            self._user_tiers = {}

    @staticmethod
    def _parse_tier(value: Any) -> UsageTier:
        """
        Parse a stored tier value into the canonical UsageTier.

        Supports legacy values (e.g. "enterprise") by mapping them to the
        closest supported tier ("business").
        """
        if value is None:
            return UsageTier.FREE
        raw = str(value).lower().strip()
        if raw == "enterprise":
            return UsageTier.BUSINESS
        try:
            return UsageTier(raw)
        except ValueError:
            return UsageTier.FREE

    def _save_user_tiers(self) -> None:
        """Save user tier assignments to disk."""
        tiers_file = self._get_tiers_file_path()
        try:
            with open(tiers_file, "w") as f:
                json.dump({k: v.value for k, v in self._user_tiers.items()}, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving user tiers: {e}")

    def _get_current_date(self) -> str:
        """Get current date string."""
        return date.today().isoformat()

    def _get_current_year_month(self) -> str:
        """Get current year-month string."""
        return date.today().strftime("%Y-%m")

    def _load_monthly_usage(self, user_hash: str, year_month: str) -> Dict[str, UsageRecord]:
        """Load monthly usage data for a user."""
        cache_key = f"{user_hash}_{year_month}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        file_path = self._get_usage_file_path(user_hash, year_month)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    records = {}
                    for date_str, record_data in data.items():
                        records[date_str] = UsageRecord(
                            user_hash=record_data.get("user_hash", user_hash),
                            date=date_str,
                            generation_count=record_data.get("generation_count", 0),
                            tokens_used=record_data.get("tokens_used", 0),
                            tool_usage=record_data.get("tool_usage", {}),
                        )
                    self._cache[cache_key] = records
                    return records
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading usage data for {user_hash}: {e}")

        self._cache[cache_key] = {}
        return self._cache[cache_key]

    def _save_monthly_usage(self, user_hash: str, year_month: str) -> None:
        """Save monthly usage data for a user."""
        cache_key = f"{user_hash}_{year_month}"
        if cache_key not in self._cache:
            return

        file_path = self._get_usage_file_path(user_hash, year_month)
        try:
            data = {}
            for date_str, record in self._cache[cache_key].items():
                data[date_str] = {
                    "user_hash": record.user_hash,
                    "date": record.date,
                    "generation_count": record.generation_count,
                    "tokens_used": record.tokens_used,
                    "tool_usage": record.tool_usage,
                }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving usage data for {user_hash}: {e}")

    def get_user_tier(self, user_hash: str) -> UsageTier:
        """
        Get the tier for a user.

        Args:
            user_hash: User identifier hash.

        Returns:
            The user's tier (defaults to FREE if not set).
        """
        return self._user_tiers.get(user_hash, UsageTier.FREE)

    def set_user_tier(self, user_hash: str, tier: UsageTier) -> None:
        """
        Set the tier for a user.

        Args:
            user_hash: User identifier hash.
            tier: The tier to assign.
        """
        self._user_tiers[user_hash] = tier
        self._save_user_tiers()
        logger.info(f"Set tier for user {user_hash[:8]}... to {tier.value}")

    def check_usage_limit(self, user_hash: str) -> int:
        """
        Check if user has remaining usage and return remaining count.

        Args:
            user_hash: User identifier hash.

        Returns:
            Number of remaining generations for today.

        Raises:
            UsageLimitExceeded: If daily or monthly limit is reached.
        """
        tier = self.get_user_tier(user_hash)
        config = TIER_CONFIGS[tier]
        daily_unlimited = config.daily_limit == -1

        today = self._get_current_date()
        year_month = self._get_current_year_month()
        monthly_usage = self._load_monthly_usage(user_hash, year_month)

        # Calculate daily usage
        daily_record = monthly_usage.get(today)
        daily_count = daily_record.generation_count if daily_record else 0

        # Calculate monthly usage
        monthly_count = sum(r.generation_count for r in monthly_usage.values())

        # Check daily limit
        if not daily_unlimited and daily_count >= config.daily_limit:
            raise UsageLimitExceeded(
                f"Daily limit of {config.daily_limit} generations reached. "
                "Upgrade your plan for higher limits.",
                tier,
                "daily"
            )

        # Check monthly limit
        if config.monthly_limit != -1 and monthly_count >= config.monthly_limit:
            raise UsageLimitExceeded(
                f"Monthly limit of {config.monthly_limit} generations reached. "
                "Upgrade your plan for higher limits.",
                tier,
                "monthly"
            )

        return -1 if daily_unlimited else (config.daily_limit - daily_count)

    def increment_usage(
        self,
        user_hash: str,
        tokens_used: int = 0,
        tool_id: Optional[str] = None
    ) -> UsageStats:
        """
        Increment usage count for a user.

        Args:
            user_hash: User identifier hash.
            tokens_used: Number of tokens used in this generation.
            tool_id: Optional tool identifier for tracking tool-specific usage.

        Returns:
            Updated usage statistics.
        """
        today = self._get_current_date()
        year_month = self._get_current_year_month()
        monthly_usage = self._load_monthly_usage(user_hash, year_month)

        # Get or create today's record
        if today not in monthly_usage:
            monthly_usage[today] = UsageRecord(
                user_hash=user_hash,
                date=today,
            )

        record = monthly_usage[today]
        record.generation_count += 1
        record.tokens_used += tokens_used

        if tool_id:
            record.tool_usage[tool_id] = record.tool_usage.get(tool_id, 0) + 1

        # Save updated usage
        self._save_monthly_usage(user_hash, year_month)

        logger.info(
            f"Usage incremented for user {user_hash[:8]}...: "
            f"daily={record.generation_count}, tokens={tokens_used}"
        )

        return self.get_usage_stats(user_hash)

    def get_usage_stats(self, user_hash: str) -> UsageStats:
        """
        Get usage statistics for a user.

        Args:
            user_hash: User identifier hash.

        Returns:
            UsageStats object with current usage information.
        """
        tier = self.get_user_tier(user_hash)
        config = TIER_CONFIGS[tier]

        today = self._get_current_date()
        year_month = self._get_current_year_month()
        monthly_usage = self._load_monthly_usage(user_hash, year_month)

        # Calculate daily usage
        daily_record = monthly_usage.get(today)
        daily_count = daily_record.generation_count if daily_record else 0
        tokens_today = daily_record.tokens_used if daily_record else 0

        # Calculate monthly usage
        monthly_count = sum(r.generation_count for r in monthly_usage.values())
        tokens_month = sum(r.tokens_used for r in monthly_usage.values())

        # Calculate remaining (handle unlimited)
        if config.daily_limit == -1:
            daily_remaining = -1
            daily_percentage = 0.0
        else:
            daily_remaining = max(0, config.daily_limit - daily_count)
            daily_percentage = (daily_count / config.daily_limit * 100) if config.daily_limit > 0 else 0

        if config.monthly_limit == -1:
            monthly_remaining = -1
            monthly_percentage = 0.0
        else:
            monthly_remaining = max(0, config.monthly_limit - monthly_count)
            monthly_percentage = (monthly_count / config.monthly_limit * 100) if config.monthly_limit > 0 else 0

        # Determine if limit is reached
        is_limit_reached = (
            (config.daily_limit != -1 and daily_count >= config.daily_limit) or
            (config.monthly_limit != -1 and monthly_count >= config.monthly_limit)
        )

        # Calculate reset times
        tomorrow = date.today() + timedelta(days=1)
        reset_daily = f"{tomorrow.year}-{tomorrow.month:02d}-{tomorrow.day:02d}T00:00:00Z"

        first_of_this_month = date.today().replace(day=1)
        first_of_next_month = (first_of_this_month + timedelta(days=32)).replace(day=1)
        reset_monthly = f"{first_of_next_month.year}-{first_of_next_month.month:02d}-01T00:00:00Z"

        return UsageStats(
            user_hash=user_hash,
            tier=tier,
            daily_count=daily_count,
            daily_limit=config.daily_limit,
            daily_remaining=daily_remaining,
            monthly_count=monthly_count,
            monthly_limit=config.monthly_limit,
            monthly_remaining=monthly_remaining,
            tokens_used_today=tokens_today,
            tokens_used_month=tokens_month,
            is_limit_reached=is_limit_reached,
            percentage_used_daily=round(daily_percentage, 1),
            percentage_used_monthly=round(monthly_percentage, 1),
            reset_daily_at=reset_daily,
            reset_monthly_at=reset_monthly,
        )


# Initialize usage limiter singleton
usage_limiter = UsageLimiter()


def check_usage_limit(user_hash: str) -> int:
    """
    Check if user has remaining usage.

    Args:
        user_hash: User identifier hash.

    Returns:
        Number of remaining generations for today (-1 for unlimited).

    Raises:
        UsageLimitExceeded: If daily or monthly limit is reached.
    """
    return usage_limiter.check_usage_limit(user_hash)


def increment_usage(
    user_hash: str,
    tokens_used: int = 0,
    tool_id: Optional[str] = None
) -> UsageStats:
    """
    Increment usage count for a user.

    Args:
        user_hash: User identifier hash.
        tokens_used: Number of tokens used.
        tool_id: Optional tool identifier.

    Returns:
        Updated usage statistics.
    """
    return usage_limiter.increment_usage(user_hash, tokens_used, tool_id)


def get_usage_stats(user_hash: str) -> UsageStats:
    """
    Get usage statistics for a user.

    Args:
        user_hash: User identifier hash.

    Returns:
        UsageStats object with current usage information.
    """
    return usage_limiter.get_usage_stats(user_hash)


def get_tier_info(tier: UsageTier) -> TierConfig:
    """
    Get configuration for a specific tier.

    Args:
        tier: The usage tier.

    Returns:
        TierConfig with tier details.
    """
    return TIER_CONFIGS[tier]
