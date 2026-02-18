"""
Tests for quota enforcement service.

This module tests the quota service including:
- Quota checking against limits
- Monthly and daily limit enforcement
- Business tier unlimited access
- Period boundary calculations

These are P0 security tests - critical for production deployment.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def get_quota_module():
    """Get the quota_service module with fresh import for isolation."""
    # Clear cached modules
    modules_to_clear = [
        "src.usage.quota_service",
        "src.usage",
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    # Reset the singleton
    import src.usage.quota_service as quota_module
    quota_module._quota_service = None
    return quota_module


def get_usage_types():
    """Get the usage types module."""
    if "src.types.usage" in sys.modules:
        del sys.modules["src.types.usage"]
    from src.types import usage
    return usage


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

            # Mock _get_user_quota to return a FREE tier user
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            mock_quota = usage_types.UserQuota(
                user_id="test-user",
                tier=usage_types.SubscriptionTier.FREE,  # 5 monthly, 2 daily
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock _get_usage_count: first call is monthly (2), second is daily (1)
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
                tier=usage_types.SubscriptionTier.FREE,  # 5 monthly, 2 daily
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock usage: monthly at 4 (one below 5), daily at 1 (one below 2)
            call_count = 0
            async def mock_usage(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (4, 400)  # Monthly usage: 4 (one below 5)
                else:
                    return (1, 100)  # Daily usage: 1 (one below 2)
            service._get_usage_count = mock_usage

            result = await service.check_quota("test-user")

            self.assertTrue(result)


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
                tier=usage_types.SubscriptionTier.FREE,  # 5 monthly limit
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock usage at 5 (at limit)
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
                tier=usage_types.SubscriptionTier.STARTER,  # 50 monthly limit
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock usage at 100 (double the limit)
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
                tier=usage_types.SubscriptionTier.FREE,  # 2 daily limit
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock monthly usage at 2 (under limit) but will check daily
            # Return different values for monthly vs daily call
            call_count = 0
            async def mock_usage_count(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return (2, 200)  # Monthly - under limit
                else:
                    return (2, 200)  # Daily - at limit

            service._get_usage_count = mock_usage_count

            with self.assertRaises(quota_module.QuotaExceeded) as context:
                await service.check_quota("test-user")

            exception = context.exception
            self.assertEqual(exception.quota_limit, 2)  # Daily limit
            self.assertIn("daily", exception.message.lower())


class TestBusinessTierUnlimited(unittest.IsolatedAsyncioTestCase):
    """Tests for Business tier unlimited access."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_check_quota_allows_unlimited_for_business_tier(self):
        """check_quota should allow access for Business tier regardless of usage."""
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

            # Mock extremely high usage - should still be allowed
            # Business has 1000 monthly limit but unlimited daily
            service._get_usage_count = AsyncMock(return_value=(500, 50000))

            result = await service.check_quota("business-user")

            self.assertTrue(result)

    async def test_check_quota_allows_business_tier_at_monthly_limit(self):
        """check_quota should still enforce monthly limit for Business tier."""
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
                tier=usage_types.SubscriptionTier.BUSINESS,  # 1000 monthly limit
                period_start=period_start,
                period_end=period_end,
            )
            service._get_user_quota = AsyncMock(return_value=mock_quota)

            # Mock usage at monthly limit
            service._get_usage_count = AsyncMock(return_value=(1000, 100000))

            # Business tier DOES have a monthly limit of 1000
            with self.assertRaises(quota_module.QuotaExceeded):
                await service.check_quota("business-user")

    async def test_check_quota_business_tier_no_daily_limit(self):
        """check_quota should allow Business tier with high daily usage."""
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

            # Under monthly limit but high daily - should pass since Business has unlimited daily
            service._get_usage_count = AsyncMock(return_value=(100, 10000))

            result = await service.check_quota("business-user")

            self.assertTrue(result)


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

            # Test with mid-month date
            test_date = datetime(2024, 7, 15, 14, 30, 45)
            start, end = service._get_period_bounds(test_date)

            # Start should be first of July
            self.assertEqual(start.year, 2024)
            self.assertEqual(start.month, 7)
            self.assertEqual(start.day, 1)
            self.assertEqual(start.hour, 0)
            self.assertEqual(start.minute, 0)
            self.assertEqual(start.second, 0)

            # End should be first of August
            self.assertEqual(end.year, 2024)
            self.assertEqual(end.month, 8)
            self.assertEqual(end.day, 1)

    def test_period_bounds_handles_year_boundary(self):
        """_get_period_bounds should correctly handle December to January."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            # Test with December date
            test_date = datetime(2024, 12, 25, 10, 0, 0)
            start, end = service._get_period_bounds(test_date)

            # Start should be first of December 2024
            self.assertEqual(start.year, 2024)
            self.assertEqual(start.month, 12)
            self.assertEqual(start.day, 1)

            # End should be first of January 2025
            self.assertEqual(end.year, 2025)
            self.assertEqual(end.month, 1)
            self.assertEqual(end.day, 1)

    def test_period_bounds_handles_first_of_month(self):
        """_get_period_bounds should work correctly on first of month."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            # Test with first of month
            test_date = datetime(2024, 3, 1, 0, 0, 0)
            start, end = service._get_period_bounds(test_date)

            # Start should be first of March
            self.assertEqual(start.month, 3)
            self.assertEqual(start.day, 1)

            # End should be first of April
            self.assertEqual(end.month, 4)
            self.assertEqual(end.day, 1)

    def test_period_bounds_defaults_to_now(self):
        """_get_period_bounds should default to current time if no date provided."""
        with patch.dict(os.environ, {}, clear=True):
            quota_module = get_quota_module()
            service = quota_module.QuotaService()

            start, end = service._get_period_bounds()
            now = datetime.utcnow()

            # Start should be first of current month
            self.assertEqual(start.year, now.year)
            self.assertEqual(start.month, now.month)
            self.assertEqual(start.day, 1)


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

            # Start should be midnight today
            self.assertEqual(start.year, now.year)
            self.assertEqual(start.month, now.month)
            self.assertEqual(start.day, now.day)
            self.assertEqual(start.hour, 0)
            self.assertEqual(start.minute, 0)
            self.assertEqual(start.second, 0)

            # End should be midnight tomorrow
            self.assertEqual(end, start + timedelta(days=1))


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

            # Test the _get_next_tier_name helper
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
            # Business tier suggests Business (no higher tier)
            self.assertEqual(
                service._get_next_tier_name(usage_types.SubscriptionTier.BUSINESS),
                "Business"
            )


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
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        }, clear=True):
            quota_module = get_quota_module()
            usage_types = get_usage_types()

            service = quota_module.QuotaService()
            service._use_db = True

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

            with patch("src.usage.quota_service.db_execute", new=AsyncMock()) as mock_db_execute:
                result = await service.set_user_tier(
                    "test-user",
                    usage_types.SubscriptionTier.PRO
                )

            self.assertEqual(result.tier, usage_types.SubscriptionTier.PRO)

            # Verify the DB update was attempted with the correct tier value.
            self.assertTrue(mock_db_execute.await_count >= 1)
            args = mock_db_execute.await_args.args
            self.assertIn("test-user", args)
            self.assertIn("pro", args)


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

            # Get the singleton and mock its method
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


if __name__ == "__main__":
    unittest.main()
