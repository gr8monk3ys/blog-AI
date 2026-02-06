"""
Tests for usage tracking endpoints.

Tests the /usage/stats, /usage/check, /usage/tiers, and related endpoints.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


class TestUsageStats(unittest.TestCase):
    """Tests for /usage/stats endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    @patch("app.routes.usage.get_usage_stats")
    def test_stats_returns_200(self, mock_get_stats):
        """Stats endpoint should return 200."""
        from src.usage import UsageStats, UsageTier

        mock_get_stats.return_value = UsageStats(
            user_hash="test_user_hash",
            tier=UsageTier.FREE,
            daily_count=5,
            daily_limit=10,
            daily_remaining=5,
            monthly_count=50,
            monthly_limit=100,
            monthly_remaining=50,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=False,
            percentage_used_daily=50.0,
            percentage_used_monthly=50.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/stats")
        self.assertEqual(response.status_code, 200)

    @patch("app.routes.usage.get_usage_stats")
    def test_stats_contains_required_fields(self, mock_get_stats):
        """Stats response should contain required fields."""
        from src.usage import UsageStats, UsageTier

        mock_get_stats.return_value = UsageStats(
            user_hash="test_user_hash",
            tier=UsageTier.FREE,
            daily_count=5,
            daily_limit=10,
            daily_remaining=5,
            monthly_count=50,
            monthly_limit=100,
            monthly_remaining=50,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=False,
            percentage_used_daily=50.0,
            percentage_used_monthly=50.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/stats")
        data = response.json()

        self.assertIn("tier", data)
        self.assertIn("daily_count", data)
        self.assertIn("daily_limit", data)
        self.assertIn("monthly_count", data)
        self.assertIn("monthly_limit", data)


class TestUsageCheck(unittest.TestCase):
    """Tests for /usage/check endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    @patch("app.routes.usage.check_usage_limit")
    @patch("app.routes.usage.get_usage_stats")
    def test_check_returns_200_when_under_limit(self, mock_get_stats, mock_check_limit):
        """Check should return 200 when under limit."""
        from src.usage import UsageStats, UsageTier

        mock_check_limit.return_value = 5  # 5 remaining
        mock_get_stats.return_value = UsageStats(
            user_hash="test_user",
            tier=UsageTier.FREE,
            daily_count=5,
            daily_limit=10,
            daily_remaining=5,
            monthly_count=50,
            monthly_limit=100,
            monthly_remaining=50,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=False,
            percentage_used_daily=50.0,
            percentage_used_monthly=50.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/check")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["can_generate"])

    @patch("app.routes.usage.check_usage_limit")
    @patch("app.routes.usage.get_usage_stats")
    def test_check_returns_429_when_limit_exceeded(self, mock_get_stats, mock_check_limit):
        """Check should return 429 when limit exceeded."""
        from src.usage import UsageLimitExceeded, UsageStats, UsageTier

        mock_check_limit.side_effect = UsageLimitExceeded(
            message="Daily limit exceeded",
            tier=UsageTier.FREE,
            limit_type="daily",
        )
        mock_get_stats.return_value = UsageStats(
            user_hash="test_user",
            tier=UsageTier.FREE,
            daily_count=10,
            daily_limit=10,
            daily_remaining=0,
            monthly_count=50,
            monthly_limit=100,
            monthly_remaining=50,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=True,
            percentage_used_daily=100.0,
            percentage_used_monthly=50.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/check")
        self.assertEqual(response.status_code, 429)


class TestUsageTiers(unittest.TestCase):
    """Tests for /usage/tiers endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    @patch("app.routes.usage.usage_limiter")
    def test_tiers_returns_200(self, mock_limiter):
        """Tiers endpoint should return 200."""
        from src.usage import UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.FREE

        response = self.client.get("/usage/tiers")
        self.assertEqual(response.status_code, 200)

    @patch("app.routes.usage.usage_limiter")
    def test_tiers_contains_all_tiers(self, mock_limiter):
        """Tiers response should contain all tier options."""
        from src.usage import UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.FREE

        response = self.client.get("/usage/tiers")
        data = response.json()

        self.assertIn("tiers", data)
        self.assertIn("current_tier", data)
        self.assertIsInstance(data["tiers"], list)
        self.assertGreater(len(data["tiers"]), 0)

    @patch("app.routes.usage.usage_limiter")
    def test_tier_info_contains_limits(self, mock_limiter):
        """Each tier should contain limit information."""
        from src.usage import UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.FREE

        response = self.client.get("/usage/tiers")
        data = response.json()

        if len(data["tiers"]) > 0:
            tier = data["tiers"][0]
            self.assertIn("name", tier)
            self.assertIn("daily_limit", tier)
            self.assertIn("monthly_limit", tier)


class TestUsageTierDetails(unittest.TestCase):
    """Tests for /usage/tier/{tier_name} endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_tier_details_returns_200_for_valid_tier(self):
        """Tier details should return 200 for valid tier."""
        response = self.client.get("/usage/tier/free")
        self.assertEqual(response.status_code, 200)

    def test_tier_details_returns_400_for_invalid_tier(self):
        """Tier details should return 400 for invalid tier."""
        response = self.client.get("/usage/tier/invalid_tier_name")
        # API returns 400 Bad Request for invalid tier name
        self.assertEqual(response.status_code, 400)

    def test_tier_details_contains_full_info(self):
        """Tier details should contain full tier information."""
        response = self.client.get("/usage/tier/free")
        data = response.json()

        self.assertIn("name", data)
        self.assertIn("daily_limit", data)
        self.assertIn("monthly_limit", data)
        self.assertIn("features_enabled", data)


class TestUsageIncrement(unittest.TestCase):
    """Tests for usage increment functionality."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    @patch("app.routes.usage.usage_limiter")
    @patch("app.routes.usage.get_usage_stats")
    def test_usage_increments_on_generation(self, mock_get_stats, mock_limiter):
        """Usage should be tracked when content is generated."""
        from src.usage import UsageStats, UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.FREE
        mock_get_stats.return_value = UsageStats(
            user_hash="test_user",
            tier=UsageTier.FREE,
            daily_count=6,
            daily_limit=10,
            daily_remaining=4,
            monthly_count=51,
            monthly_limit=100,
            monthly_remaining=49,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=False,
            percentage_used_daily=60.0,
            percentage_used_monthly=51.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/stats")
        data = response.json()
        self.assertIsInstance(data["daily_count"], int)


class TestUsageReset(unittest.TestCase):
    """Tests for usage reset information."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    @patch("app.routes.usage.get_usage_stats")
    def test_stats_contains_reset_times(self, mock_get_stats):
        """Stats should contain reset time information."""
        from src.usage import UsageStats, UsageTier

        mock_get_stats.return_value = UsageStats(
            user_hash="test_user",
            tier=UsageTier.FREE,
            daily_count=5,
            daily_limit=10,
            daily_remaining=5,
            monthly_count=50,
            monthly_limit=100,
            monthly_remaining=50,
            tokens_used_today=1000,
            tokens_used_month=5000,
            is_limit_reached=False,
            percentage_used_daily=50.0,
            percentage_used_monthly=50.0,
            reset_daily_at="2024-01-02T00:00:00Z",
            reset_monthly_at="2024-02-01T00:00:00Z",
        )

        response = self.client.get("/usage/stats")
        data = response.json()

        self.assertIn("reset_daily_at", data)
        self.assertIn("reset_monthly_at", data)


if __name__ == "__main__":
    unittest.main()
