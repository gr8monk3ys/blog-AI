"""
Comprehensive tests for quota enforcement.

This module tests:
- Usage tracking
- Quota limits by tier (FREE, STARTER, PRO, BUSINESS)
- Monthly and daily limit enforcement
- Quota exceeded behavior
- Usage reset at period boundaries
- Tier upgrades and downgrades

These are P0 tests - critical for revenue protection and fair usage.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock supabase module before imports
mock_supabase = MagicMock()
mock_supabase.create_client = MagicMock()
sys.modules["supabase"] = mock_supabase


def get_quota_module():
    """Get the quota_service module with fresh import for isolation."""
    modules_to_clear = [
        "src.usage.quota_service",
        "src.usage",
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    import src.usage.quota_service as quota_module
    quota_module._quota_service = None
    return quota_module


def get_usage_types():
    """Get the usage types module."""
    if "src.types.usage" in sys.modules:
        del sys.modules["src.types.usage"]
    from src.types import usage
    return usage


# =============================================================================
# Quota Check Allows Operations Tests
# =============================================================================


class TestQuotaCheckAllows(unittest.IsolatedAsyncioTestCase):
    """Tests for quota check allowing operations under limits."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_check_quota_allows_when_under_limit(self):
        """check_quota should return True when usage is under the limit."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # FREE tier has 5 monthly and 2 daily limit
            call_count = 0
            async def mock_usage(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (2, 100)  # Monthly usage: 2 (under 5)
                else:
                    return (1, 50)   # Daily usage: 1 (under 2)
            service._get_usage_count = mock_usage

            result = await service.check_quota("test-user")

            self.assertTrue(result)

    async def test_check_quota_allows_at_one_below_limit(self):
        """check_quota should allow when usage is one below the limit."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            call_count = 0
            async def mock_usage(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (4, 400)  # Monthly: 4 (one below 5)
                else:
                    return (1, 100)  # Daily: 1 (one below 2)
            service._get_usage_count = mock_usage

            result = await service.check_quota("test-user")

            self.assertTrue(result)

    async def test_check_quota_allows_zero_usage(self):
        """check_quota should allow when user has no usage."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="new-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(0, 0))

            result = await service.check_quota("new-user")

            self.assertTrue(result)


# =============================================================================
# Quota Check Raises Exception Tests
# =============================================================================


class TestQuotaCheckRaises(unittest.IsolatedAsyncioTestCase):
    """Tests for quota check raising exceptions when limits exceeded."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_check_quota_raises_when_monthly_limit_exceeded(self):
        """check_quota should raise QuotaExceeded when monthly limit is exceeded."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(5, 500))

            with self.assertRaises(quota_module.QuotaExceeded) as context:
                await service.check_quota("test-user")

            exception = context.exception
            self.assertEqual(exception.tier, usage_types.SubscriptionTier.FREE)
            self.assertEqual(exception.current_usage, 5)
            self.assertEqual(exception.quota_limit, 5)
            self.assertIn("exceeded", exception.message.lower())

    async def test_check_quota_raises_when_well_over_limit(self):
        """check_quota should raise QuotaExceeded when well over the limit."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.STARTER,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(100, 10000))

            with self.assertRaises(quota_module.QuotaExceeded) as context:
                await service.check_quota("test-user")

            exception = context.exception
            self.assertEqual(exception.current_usage, 100)
            self.assertEqual(exception.quota_limit, 50)

    async def test_check_quota_raises_when_daily_limit_exceeded(self):
        """check_quota should raise QuotaExceeded when daily limit is exceeded."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            call_count = 0
            async def mock_usage_count(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (2, 200)  # Monthly - under limit
                else:
                    return (2, 200)  # Daily - at limit (FREE has 2 daily)
            service._get_usage_count = mock_usage_count

            with self.assertRaises(quota_module.QuotaExceeded) as context:
                await service.check_quota("test-user")

            exception = context.exception
            self.assertEqual(exception.quota_limit, 2)
            self.assertIn("daily", exception.message.lower())


# =============================================================================
# Tier-Specific Limit Tests
# =============================================================================


class TestTierSpecificLimits(unittest.IsolatedAsyncioTestCase):
    """Tests for tier-specific quota limits."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_free_tier_limits(self):
        """Test FREE tier has 5 monthly, 2 daily limits."""
        with patch.dict(os.environ, {}, clear=True):
            usage_types = get_usage_types()

            config = usage_types.get_tier_config(usage_types.SubscriptionTier.FREE)

            self.assertEqual(config.monthly_limit, 5)
            self.assertEqual(config.daily_limit, 2)
            self.assertEqual(config.name, "Free")

    async def test_starter_tier_limits(self):
        """Test STARTER tier has 50 monthly, 10 daily limits."""
        with patch.dict(os.environ, {}, clear=True):
            usage_types = get_usage_types()

            config = usage_types.get_tier_config(usage_types.SubscriptionTier.STARTER)

            self.assertEqual(config.monthly_limit, 50)
            self.assertEqual(config.daily_limit, 10)
            self.assertEqual(config.name, "Starter")

    async def test_pro_tier_limits(self):
        """Test PRO tier has 200 monthly, 50 daily limits."""
        with patch.dict(os.environ, {}, clear=True):
            usage_types = get_usage_types()

            config = usage_types.get_tier_config(usage_types.SubscriptionTier.PRO)

            self.assertEqual(config.monthly_limit, 200)
            self.assertEqual(config.daily_limit, 50)
            self.assertEqual(config.name, "Pro")

    async def test_business_tier_unlimited_daily(self):
        """Test BUSINESS tier has 1000 monthly, unlimited daily."""
        with patch.dict(os.environ, {}, clear=True):
            usage_types = get_usage_types()

            config = usage_types.get_tier_config(usage_types.SubscriptionTier.BUSINESS)

            self.assertEqual(config.monthly_limit, 1000)
            self.assertEqual(config.daily_limit, -1)  # Unlimited
            self.assertEqual(config.name, "Business")


# =============================================================================
# Business Tier Unlimited Daily Tests
# =============================================================================


class TestBusinessTierUnlimitedDaily(unittest.IsolatedAsyncioTestCase):
    """Tests for Business tier unlimited daily access."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_business_tier_no_daily_limit(self):
        """Business tier should allow high daily usage."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="business-user",
                tier=usage_types.SubscriptionTier.BUSINESS,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # High daily usage but under monthly - should pass
            service._get_usage_count = AsyncMock(return_value=(100, 10000))

            result = await service.check_quota("business-user")

            self.assertTrue(result)

    async def test_business_tier_monthly_limit_still_enforced(self):
        """Business tier should still enforce monthly limit."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="business-user",
                tier=usage_types.SubscriptionTier.BUSINESS,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(1000, 100000))

            with self.assertRaises(quota_module.QuotaExceeded):
                await service.check_quota("business-user")


# =============================================================================
# Period Boundary Tests
# =============================================================================


class TestPeriodBounds(unittest.TestCase):
    """Tests for period boundary calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_period_bounds_returns_first_of_month(self):
        """_get_period_bounds should return first of month as period start."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            test_date = datetime(2024, 7, 15, 14, 30, 45)
            start, end = service._get_period_bounds(test_date)

            self.assertEqual(start.year, 2024)
            self.assertEqual(start.month, 7)
            self.assertEqual(start.day, 1)
            self.assertEqual(start.hour, 0)
            self.assertEqual(start.minute, 0)

            self.assertEqual(end.year, 2024)
            self.assertEqual(end.month, 8)
            self.assertEqual(end.day, 1)

    def test_period_bounds_handles_year_boundary(self):
        """_get_period_bounds should correctly handle December to January."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            test_date = datetime(2024, 12, 25, 10, 0, 0)
            start, end = service._get_period_bounds(test_date)

            self.assertEqual(start.year, 2024)
            self.assertEqual(start.month, 12)
            self.assertEqual(start.day, 1)

            self.assertEqual(end.year, 2025)
            self.assertEqual(end.month, 1)
            self.assertEqual(end.day, 1)

    def test_period_bounds_handles_first_of_month(self):
        """_get_period_bounds should work correctly on first of month."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            test_date = datetime(2024, 3, 1, 0, 0, 0)
            start, end = service._get_period_bounds(test_date)

            self.assertEqual(start.month, 3)
            self.assertEqual(start.day, 1)
            self.assertEqual(end.month, 4)
            self.assertEqual(end.day, 1)

    def test_period_bounds_defaults_to_now(self):
        """_get_period_bounds should default to current time if no date provided."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            start, end = service._get_period_bounds()
            now = datetime.utcnow()

            self.assertEqual(start.year, now.year)
            self.assertEqual(start.month, now.month)
            self.assertEqual(start.day, 1)


# =============================================================================
# Day Bounds Tests
# =============================================================================


class TestDayBounds(unittest.TestCase):
    """Tests for daily period boundary calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_day_bounds_returns_start_of_day(self):
        """_get_day_bounds should return midnight UTC as start."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            start, end = service._get_day_bounds()
            now = datetime.utcnow()

            self.assertEqual(start.year, now.year)
            self.assertEqual(start.month, now.month)
            self.assertEqual(start.day, now.day)
            self.assertEqual(start.hour, 0)
            self.assertEqual(start.minute, 0)
            self.assertEqual(start.second, 0)

            self.assertEqual(end, start + timedelta(days=1))


# =============================================================================
# Quota Exceeded Error Tests
# =============================================================================


class TestQuotaExceededError(unittest.TestCase):
    """Tests for QuotaExceeded exception."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_quota_exceeded_to_error_response(self):
        """QuotaExceeded should convert to QuotaExceededError response."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            reset_date = datetime(2024, 8, 1, 0, 0, 0)
            exception = quota_module.QuotaExceeded(
                message="Monthly quota exceeded",
                tier=usage_types.SubscriptionTier.FREE,
                current_usage=5,
                quota_limit=5,
                reset_date=reset_date,
            )

            error_response = exception.to_error_response()

            self.assertFalse(error_response.success)
            self.assertEqual(error_response.error, "Monthly quota exceeded")
            self.assertEqual(error_response.tier, usage_types.SubscriptionTier.FREE)
            self.assertEqual(error_response.current_usage, 5)
            self.assertEqual(error_response.quota_limit, 5)
            self.assertEqual(error_response.reset_date, reset_date)

    def test_quota_exceeded_includes_upgrade_suggestion(self):
        """QuotaExceeded message should suggest upgrade to next tier."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            self.assertEqual(
                service._get_next_tier_name(usage_types.SubscriptionTier.FREE),
                "Starter"
            )
            self.assertEqual(
                service._get_next_tier_name(usage_types.SubscriptionTier.STARTER),
                "Pro"
            )
            self.assertEqual(
                service._get_next_tier_name(usage_types.SubscriptionTier.PRO),
                "Business"
            )
            self.assertEqual(
                service._get_next_tier_name(usage_types.SubscriptionTier.BUSINESS),
                "Business"
            )


# =============================================================================
# Usage Tracking Tests
# =============================================================================


class TestUsageTracking(unittest.IsolatedAsyncioTestCase):
    """Tests for usage tracking and increment."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_increment_usage_returns_updated_stats(self):
        """increment_usage should return updated usage statistics."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()
            service._use_supabase = False

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.PRO,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(10, 1000))

            # Mock the file-based limiter
            with patch("src.usage.limiter.usage_limiter") as mock_limiter:
                mock_limiter.increment_usage = MagicMock()

                stats = await service.increment_usage(
                    user_id="test-user",
                    operation_type="blog",
                    tokens_used=100,
                )

                self.assertEqual(stats.user_id, "test-user")
                self.assertEqual(stats.tier, usage_types.SubscriptionTier.PRO)

    async def test_get_usage_stats(self):
        """get_usage_stats should return complete usage information."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.PRO,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(50, 5000))

            stats = await service.get_usage_stats("test-user")

            self.assertEqual(stats.user_id, "test-user")
            self.assertEqual(stats.tier, usage_types.SubscriptionTier.PRO)
            self.assertEqual(stats.current_usage, 50)
            self.assertEqual(stats.quota_limit, 200)
            self.assertEqual(stats.remaining, 150)


# =============================================================================
# Set User Tier Tests
# =============================================================================


class TestSetUserTier(unittest.IsolatedAsyncioTestCase):
    """Tests for setting user subscription tier."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_set_user_tier_updates_quota(self):
        """set_user_tier should update the user's tier."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "test-key",
        }, clear=True):
            mock_client = MagicMock()
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

            mock_supabase.create_client.return_value = mock_client

            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()
            service._supabase_client = mock_client

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            result = await service.set_user_tier(
                "test-user",
                usage_types.SubscriptionTier.PRO
            )

            self.assertEqual(result.tier, usage_types.SubscriptionTier.PRO)


# =============================================================================
# Singleton Tests
# =============================================================================


class TestGetQuotaServiceSingleton(unittest.TestCase):
    """Tests for the singleton pattern."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_get_quota_service_returns_singleton(self):
        """get_quota_service should return the same instance on subsequent calls."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()

            service1 = quota_module.get_quota_service()
            service2 = quota_module.get_quota_service()

            self.assertIs(service1, service2)


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions(unittest.IsolatedAsyncioTestCase):
    """Tests for module-level convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_check_quota_convenience_function(self):
        """check_quota module function should delegate to service."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.get_quota_service()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.PRO,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)
            service._get_usage_count = AsyncMock(return_value=(10, 1000))

            result = await quota_module.check_quota("test-user")

            self.assertTrue(result)


# =============================================================================
# Tier Configuration Tests
# =============================================================================


class TestTierConfigurations:
    """Tests for tier configuration data."""

    def test_all_tiers_have_config(self):
        """All subscription tiers should have configuration."""
        usage_types = get_usage_types()

        for tier in usage_types.SubscriptionTier:
            config = usage_types.get_tier_config(tier)
            assert config is not None
            assert config.tier == tier
            assert config.name is not None
            assert config.monthly_limit is not None

    def test_tier_configs_have_required_fields(self):
        """Tier configs should have all required fields."""
        usage_types = get_usage_types()

        for tier, config in usage_types.TIER_CONFIGS.items():
            assert config.name != ""
            assert config.monthly_limit >= -1  # -1 for unlimited
            assert config.daily_limit >= -1
            assert isinstance(config.features, list)
            assert config.price_monthly >= 0
            assert config.price_yearly >= 0

    def test_get_all_tiers(self):
        """get_all_tiers should return all tier configurations."""
        usage_types = get_usage_types()

        all_tiers = usage_types.get_all_tiers()

        assert len(all_tiers) == 4
        tier_names = [t.name for t in all_tiers]
        assert "Free" in tier_names
        assert "Starter" in tier_names
        assert "Pro" in tier_names
        assert "Business" in tier_names


# =============================================================================
# Usage Stats Model Tests
# =============================================================================


class TestUsageStatsModel:
    """Tests for UsageStats Pydantic model."""

    def test_usage_stats_defaults(self):
        """Test UsageStats default values."""
        usage_types = get_usage_types()

        now = datetime.utcnow()
        period_start = now.replace(day=1)
        period_end = period_start.replace(month=period_start.month + 1)

        stats = usage_types.UsageStats(
            user_id="test-user",
            tier=usage_types.SubscriptionTier.FREE,
            current_usage=3,
            quota_limit=5,
            remaining=2,
            reset_date=period_end,
            period_start=period_start,
        )

        assert stats.daily_usage == 0
        assert stats.daily_limit == -1
        assert stats.daily_remaining == -1
        assert stats.tokens_used == 0
        assert stats.percentage_used == 0.0
        assert stats.is_quota_exceeded is False

    def test_usage_stats_quota_exceeded_flag(self):
        """Test UsageStats with quota exceeded."""
        usage_types = get_usage_types()

        now = datetime.utcnow()
        period_start = now.replace(day=1)
        period_end = period_start.replace(month=period_start.month + 1)

        stats = usage_types.UsageStats(
            user_id="test-user",
            tier=usage_types.SubscriptionTier.FREE,
            current_usage=5,
            quota_limit=5,
            remaining=0,
            reset_date=period_end,
            period_start=period_start,
            is_quota_exceeded=True,
            percentage_used=100.0,
        )

        assert stats.is_quota_exceeded is True
        assert stats.remaining == 0
        assert stats.percentage_used == 100.0


# =============================================================================
# Usage Breakdown Tests
# =============================================================================


class TestUsageBreakdown(unittest.IsolatedAsyncioTestCase):
    """Tests for usage breakdown by operation type."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_get_usage_breakdown_returns_empty_on_no_data(self):
        """get_usage_breakdown should return zeros when no usage data."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()

            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            breakdown = await service.get_usage_breakdown("test-user")

            assert breakdown["blog"] == 0
            assert breakdown["book"] == 0
            assert breakdown["batch"] == 0
            assert breakdown["total"] == 0


# =============================================================================
# Reset Monthly Quotas Tests
# =============================================================================


class TestResetMonthlyQuotas(unittest.IsolatedAsyncioTestCase):
    """Tests for monthly quota reset functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_reset_monthly_quotas_returns_count(self):
        """reset_monthly_quotas should return count of reset quotas."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()

            service = quota_module.QuotaService()
            service._use_supabase = False

            result = await service.reset_monthly_quotas()

            # Without Supabase, should return 0
            assert result == 0


if __name__ == "__main__":
    unittest.main()
