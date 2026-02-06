"""
Usage quota service for tracking and enforcing subscription-based limits.

This module provides Supabase-backed quota management with:
- check_quota: Verify if user has remaining quota
- increment_usage: Record usage after successful generation
- get_usage_stats: Get current period statistics
- reset_monthly_quotas: Scheduled job to reset quotas

Falls back to file-based storage when Supabase is not configured.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from src.types.usage import (
    QuotaExceededError,
    SubscriptionTier,
    TierConfig,
    UsageRecord,
    UsageStats,
    UserQuota,
    get_tier_config,
    TIER_CONFIGS,
)

logger = logging.getLogger(__name__)


class QuotaExceeded(Exception):
    """Exception raised when user quota is exceeded."""

    def __init__(
        self,
        message: str,
        tier: SubscriptionTier,
        current_usage: int,
        quota_limit: int,
        reset_date: datetime,
    ):
        self.message = message
        self.tier = tier
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.reset_date = reset_date
        super().__init__(self.message)

    def to_error_response(self) -> QuotaExceededError:
        """Convert to API error response."""
        return QuotaExceededError(
            error=self.message,
            tier=self.tier,
            current_usage=self.current_usage,
            quota_limit=self.quota_limit,
            reset_date=self.reset_date,
        )


class QuotaService:
    """
    Service for managing user quotas and usage tracking.

    Uses Supabase for persistent storage when available,
    falls back to the existing file-based limiter otherwise.
    """

    def __init__(self):
        """Initialize the quota service."""
        self._supabase_client = None
        self._use_supabase = False
        self._init_supabase()

    def _init_supabase(self) -> None:
        """Initialize Supabase client if configured."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            try:
                from supabase import create_client, Client
                self._supabase_client: Client = create_client(supabase_url, supabase_key)
                self._use_supabase = True
                logger.info("Quota service initialized with Supabase")
            except ImportError:
                logger.warning("Supabase package not installed, using file-based storage")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
        else:
            logger.info("Supabase not configured, using file-based storage")

    def _get_period_bounds(self, reference_date: Optional[datetime] = None) -> tuple[datetime, datetime]:
        """
        Get the start and end of the current billing period.

        Uses first of month to first of next month for simplicity.
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        period_start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate next month
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        return period_start, period_end

    def _get_day_bounds(self) -> tuple[datetime, datetime]:
        """Get the start and end of today (UTC)."""
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        return day_start, day_end

    async def _get_user_quota(self, user_id: str) -> UserQuota:
        """
        Get or create user quota record.

        Returns the user's quota configuration from the database,
        or creates a default FREE tier quota if not found.
        """
        period_start, period_end = self._get_period_bounds()

        if self._use_supabase and self._supabase_client:
            try:
                # Try to get existing quota (run sync Supabase call in thread pool)
                response = await asyncio.to_thread(
                    lambda: self._supabase_client.table("user_quotas").select("*").eq(
                        "user_id", user_id
                    ).execute()
                )

                if response.data and len(response.data) > 0:
                    row = response.data[0]
                    quota = UserQuota(
                        id=row["id"],
                        user_id=row["user_id"],
                        tier=SubscriptionTier(row["tier"]),
                        period_start=datetime.fromisoformat(row["period_start"].replace("Z", "+00:00")).replace(tzinfo=None),
                        period_end=datetime.fromisoformat(row["period_end"].replace("Z", "+00:00")).replace(tzinfo=None),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")).replace(tzinfo=None) if row.get("created_at") else None,
                        updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None) if row.get("updated_at") else None,
                    )

                    # Check if period needs reset
                    if datetime.utcnow() >= quota.period_end:
                        # Reset to new period (run sync Supabase call in thread pool)
                        new_start, new_end = self._get_period_bounds()
                        await asyncio.to_thread(
                            lambda: self._supabase_client.table("user_quotas").update({
                                "period_start": new_start.isoformat(),
                                "period_end": new_end.isoformat(),
                                "updated_at": datetime.utcnow().isoformat(),
                            }).eq("id", row["id"]).execute()
                        )
                        quota.period_start = new_start
                        quota.period_end = new_end

                    return quota

                # Create new quota for user (run sync Supabase call in thread pool)
                new_quota = {
                    "user_id": user_id,
                    "tier": SubscriptionTier.FREE.value,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                response = await asyncio.to_thread(
                    lambda: self._supabase_client.table("user_quotas").insert(new_quota).execute()
                )

                if response.data and len(response.data) > 0:
                    row = response.data[0]
                    return UserQuota(
                        id=row["id"],
                        user_id=user_id,
                        tier=SubscriptionTier.FREE,
                        period_start=period_start,
                        period_end=period_end,
                    )

            except Exception as e:
                logger.error(f"Supabase error getting user quota: {e}")

        # Fallback: return default FREE quota
        return UserQuota(
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            period_start=period_start,
            period_end=period_end,
        )

    async def _get_usage_count(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> tuple[int, int]:
        """
        Get usage count for a user in a period.

        Returns (count, tokens_used).
        """
        if self._use_supabase and self._supabase_client:
            try:
                # Query usage records (run sync Supabase call in thread pool)
                response = await asyncio.to_thread(
                    lambda: self._supabase_client.table("usage_records").select(
                        "id, tokens_used"
                    ).eq("user_id", user_id).gte(
                        "timestamp", period_start.isoformat()
                    ).lt(
                        "timestamp", period_end.isoformat()
                    ).execute()
                )

                if response.data:
                    count = len(response.data)
                    tokens = sum(row.get("tokens_used", 0) for row in response.data)
                    return count, tokens

                return 0, 0

            except Exception as e:
                logger.error(f"Supabase error getting usage count: {e}")
                return 0, 0

        # Fallback: use file-based limiter
        from src.usage.limiter import usage_limiter
        stats = usage_limiter.get_usage_stats(user_id)
        return stats.monthly_count, stats.tokens_used_month

    async def check_quota(self, user_id: str) -> bool:
        """
        Check if user has remaining quota.

        Args:
            user_id: The user identifier.

        Returns:
            True if user has remaining quota.

        Raises:
            QuotaExceeded: If monthly or daily quota is exceeded.
        """
        quota = await self._get_user_quota(user_id)
        tier_config = get_tier_config(quota.tier)

        # Get monthly usage
        monthly_count, _ = await self._get_usage_count(
            user_id, quota.period_start, quota.period_end
        )

        # Check monthly limit
        if tier_config.monthly_limit != -1 and monthly_count >= tier_config.monthly_limit:
            raise QuotaExceeded(
                message=f"Monthly quota of {tier_config.monthly_limit} generations exceeded. "
                        f"Upgrade to {self._get_next_tier_name(quota.tier)} for more generations.",
                tier=quota.tier,
                current_usage=monthly_count,
                quota_limit=tier_config.monthly_limit,
                reset_date=quota.period_end,
            )

        # Check daily limit if applicable
        if tier_config.daily_limit != -1:
            day_start, day_end = self._get_day_bounds()
            daily_count, _ = await self._get_usage_count(user_id, day_start, day_end)

            if daily_count >= tier_config.daily_limit:
                tomorrow = day_end
                raise QuotaExceeded(
                    message=f"Daily quota of {tier_config.daily_limit} generations exceeded. "
                            f"Try again tomorrow or upgrade for higher limits.",
                    tier=quota.tier,
                    current_usage=daily_count,
                    quota_limit=tier_config.daily_limit,
                    reset_date=tomorrow,
                )

        return True

    def _get_next_tier_name(self, current_tier: SubscriptionTier) -> str:
        """Get the name of the next tier for upgrade messaging."""
        tier_order = [
            SubscriptionTier.FREE,
            SubscriptionTier.STARTER,
            SubscriptionTier.PRO,
            SubscriptionTier.BUSINESS,
        ]
        try:
            idx = tier_order.index(current_tier)
            if idx < len(tier_order) - 1:
                next_tier = tier_order[idx + 1]
                return get_tier_config(next_tier).name
        except ValueError:
            pass
        return "Business"

    async def increment_usage(
        self,
        user_id: str,
        operation_type: str,
        tokens_used: int = 0,
        metadata: Optional[dict] = None,
    ) -> UsageStats:
        """
        Record a usage event after successful generation.

        Args:
            user_id: The user identifier.
            operation_type: Type of operation (blog, book, batch, remix, tool).
            tokens_used: Number of tokens consumed.
            metadata: Additional metadata about the operation.

        Returns:
            Updated usage statistics.
        """
        timestamp = datetime.utcnow()

        if self._use_supabase and self._supabase_client:
            try:
                record = {
                    "user_id": user_id,
                    "operation_type": operation_type,
                    "tokens_used": tokens_used,
                    "timestamp": timestamp.isoformat(),
                    "metadata": metadata,
                }
                # Insert usage record (run sync Supabase call in thread pool)
                await asyncio.to_thread(
                    lambda: self._supabase_client.table("usage_records").insert(record).execute()
                )
                logger.info(f"Usage recorded for user {user_id[:8]}...: {operation_type}")

            except Exception as e:
                logger.error(f"Supabase error recording usage: {e}")

        else:
            # Fallback: use file-based limiter
            from src.usage.limiter import usage_limiter
            usage_limiter.increment_usage(user_id, tokens_used, operation_type)

        return await self.get_usage_stats(user_id)

    async def get_usage_stats(self, user_id: str) -> UsageStats:
        """
        Get current usage statistics for a user.

        Args:
            user_id: The user identifier.

        Returns:
            UsageStats with current period usage information.
        """
        quota = await self._get_user_quota(user_id)
        tier_config = get_tier_config(quota.tier)

        # Get monthly usage
        monthly_count, tokens_used = await self._get_usage_count(
            user_id, quota.period_start, quota.period_end
        )

        # Get daily usage
        day_start, day_end = self._get_day_bounds()
        daily_count, _ = await self._get_usage_count(user_id, day_start, day_end)

        # Calculate remaining
        if tier_config.monthly_limit == -1:
            remaining = -1
            percentage = 0.0
        else:
            remaining = max(0, tier_config.monthly_limit - monthly_count)
            percentage = (monthly_count / tier_config.monthly_limit * 100) if tier_config.monthly_limit > 0 else 0.0

        if tier_config.daily_limit == -1:
            daily_remaining = -1
        else:
            daily_remaining = max(0, tier_config.daily_limit - daily_count)

        is_exceeded = (
            (tier_config.monthly_limit != -1 and monthly_count >= tier_config.monthly_limit) or
            (tier_config.daily_limit != -1 and daily_count >= tier_config.daily_limit)
        )

        return UsageStats(
            user_id=user_id,
            tier=quota.tier,
            current_usage=monthly_count,
            quota_limit=tier_config.monthly_limit,
            remaining=remaining,
            daily_usage=daily_count,
            daily_limit=tier_config.daily_limit,
            daily_remaining=daily_remaining,
            reset_date=quota.period_end,
            period_start=quota.period_start,
            tokens_used=tokens_used,
            percentage_used=round(percentage, 1),
            is_quota_exceeded=is_exceeded,
        )

    async def set_user_tier(self, user_id: str, tier: SubscriptionTier) -> UserQuota:
        """
        Set the subscription tier for a user.

        Args:
            user_id: The user identifier.
            tier: The new subscription tier.

        Returns:
            Updated UserQuota.
        """
        quota = await self._get_user_quota(user_id)

        if self._use_supabase and self._supabase_client:
            try:
                # Update user tier (run sync Supabase call in thread pool)
                await asyncio.to_thread(
                    lambda: self._supabase_client.table("user_quotas").update({
                        "tier": tier.value,
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("user_id", user_id).execute()
                )
                logger.info(f"Updated tier for user {user_id[:8]}... to {tier.value}")

            except Exception as e:
                logger.error(f"Supabase error updating tier: {e}")

        else:
            # Fallback: use file-based limiter
            from src.usage.limiter import usage_limiter, UsageTier
            # Map to legacy tier if possible
            tier_mapping = {
                SubscriptionTier.FREE: UsageTier.FREE,
                SubscriptionTier.STARTER: UsageTier.FREE,  # Map to closest
                SubscriptionTier.PRO: UsageTier.PRO,
                SubscriptionTier.BUSINESS: UsageTier.ENTERPRISE,
            }
            usage_limiter.set_user_tier(user_id, tier_mapping.get(tier, UsageTier.FREE))

        quota.tier = tier
        return quota

    async def reset_monthly_quotas(self) -> int:
        """
        Reset monthly quotas for all users.

        This should be called by a scheduled job at the start of each month.
        In practice, quotas are reset lazily when accessed after period_end.

        Returns:
            Number of quotas reset.
        """
        reset_count = 0

        if self._use_supabase and self._supabase_client:
            try:
                now = datetime.utcnow()
                new_start, new_end = self._get_period_bounds()

                # Find expired quotas (run sync Supabase call in thread pool)
                response = await asyncio.to_thread(
                    lambda: self._supabase_client.table("user_quotas").select(
                        "id"
                    ).lt("period_end", now.isoformat()).execute()
                )

                if response.data:
                    ids_to_reset = [row["id"] for row in response.data]

                    for quota_id in ids_to_reset:
                        # Update each expired quota (run sync Supabase call in thread pool)
                        await asyncio.to_thread(
                            lambda qid=quota_id: self._supabase_client.table("user_quotas").update({
                                "period_start": new_start.isoformat(),
                                "period_end": new_end.isoformat(),
                                "updated_at": now.isoformat(),
                            }).eq("id", qid).execute()
                        )
                        reset_count += 1

                logger.info(f"Reset {reset_count} user quotas for new period")

            except Exception as e:
                logger.error(f"Supabase error resetting quotas: {e}")

        return reset_count

    async def get_usage_breakdown(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> dict:
        """
        Get detailed usage breakdown by operation type.

        Args:
            user_id: The user identifier.
            period_start: Start of period (defaults to current period).
            period_end: End of period (defaults to current period).

        Returns:
            Dictionary with usage counts by operation type.
        """
        if period_start is None or period_end is None:
            quota = await self._get_user_quota(user_id)
            period_start = quota.period_start
            period_end = quota.period_end

        breakdown = {
            "blog": 0,
            "book": 0,
            "batch": 0,
            "remix": 0,
            "tool": 0,
            "other": 0,
            "total": 0,
        }

        if self._use_supabase and self._supabase_client:
            try:
                # Query usage breakdown (run sync Supabase call in thread pool)
                response = await asyncio.to_thread(
                    lambda: self._supabase_client.table("usage_records").select(
                        "operation_type"
                    ).eq("user_id", user_id).gte(
                        "timestamp", period_start.isoformat()
                    ).lt(
                        "timestamp", period_end.isoformat()
                    ).execute()
                )

                if response.data:
                    for row in response.data:
                        op_type = row.get("operation_type", "other")
                        if op_type in breakdown:
                            breakdown[op_type] += 1
                        else:
                            breakdown["other"] += 1
                        breakdown["total"] += 1

            except Exception as e:
                logger.error(f"Supabase error getting usage breakdown: {e}")

        return breakdown


# Singleton instance
_quota_service: Optional[QuotaService] = None


def get_quota_service() -> QuotaService:
    """Get the singleton quota service instance."""
    global _quota_service
    if _quota_service is None:
        _quota_service = QuotaService()
    return _quota_service


# Convenience functions for direct access
async def check_quota(user_id: str) -> bool:
    """Check if user has remaining quota."""
    return await get_quota_service().check_quota(user_id)


async def increment_usage(
    user_id: str,
    operation_type: str,
    tokens_used: int = 0,
    metadata: Optional[dict] = None,
) -> UsageStats:
    """Record a usage event."""
    return await get_quota_service().increment_usage(
        user_id, operation_type, tokens_used, metadata
    )


async def get_usage_stats(user_id: str) -> UsageStats:
    """Get current usage statistics."""
    return await get_quota_service().get_usage_stats(user_id)


async def reset_monthly_quotas() -> int:
    """Reset monthly quotas for all users."""
    return await get_quota_service().reset_monthly_quotas()
