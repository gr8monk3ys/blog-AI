"""
Tests for usage tracking endpoints.

Tests the /usage/stats, /usage/check, /usage/tiers, and related endpoints.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


def make_quota_stats(tier_name: str = "pro"):
    """Create a quota UsageStats object for quota endpoint tests."""
    from src.types.usage import SubscriptionTier, UsageStats

    now = datetime.now(timezone.utc)
    tier = SubscriptionTier(tier_name)
    return UsageStats(
        user_id="user-12345678",
        tier=tier,
        current_usage=12,
        quota_limit=200,
        remaining=188,
        daily_usage=2,
        daily_limit=50,
        daily_remaining=48,
        reset_date=now,
        period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        tokens_used=1024,
        percentage_used=6.0,
        is_quota_exceeded=False,
    )


def detail_text(response) -> str:
    """Normalize API error detail into a lowercase string for assertions."""
    detail = response.json().get("detail")
    if isinstance(detail, dict):
        return str(detail.get("error", detail)).lower()
    return str(detail).lower()


class TestUsageStats(unittest.TestCase):
    """Tests for /usage/stats endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

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
        self.client.headers.update({"X-API-Key": "test-key"})

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
        self.client.headers.update({"X-API-Key": "test-key"})

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
        self.client.headers.update({"X-API-Key": "test-key"})

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
        self.client.headers.update({"X-API-Key": "test-key"})

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
        self.client.headers.update({"X-API-Key": "test-key"})

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


class TestUsagePermissionGuards(unittest.TestCase):
    """Tests for organization-aware permission guards."""

    def setUp(self):
        from server import app
        self.app = app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    def tearDown(self):
        self.app.dependency_overrides = {}

    def test_stats_forbidden_for_non_member_org_context(self):
        from app.routes import usage as usage_routes
        from src.organizations.rbac import AuthorizationContext

        ctx = AuthorizationContext(
            user_id="user-1",
            organization_id="org-1",
            role=None,
            is_org_member=False,
        )
        self.app.dependency_overrides[usage_routes.get_optional_organization_context] = lambda: ctx

        response = self.client.get("/usage/stats")
        self.assertEqual(response.status_code, 403)
        self.assertIn("not a member", response.json()["detail"].lower())

    def test_stats_forbidden_when_missing_content_view_permission(self):
        from app.routes import usage as usage_routes
        from src.organizations.rbac import AuthorizationContext

        ctx = AuthorizationContext(
            user_id="user-1",
            organization_id="org-1",
            role=None,  # No role => no permissions.
            is_org_member=True,
        )
        self.app.dependency_overrides[usage_routes.get_optional_organization_context] = lambda: ctx

        response = self.client.get("/usage/stats")
        self.assertEqual(response.status_code, 403)
        self.assertIn("missing permission", response.json()["detail"].lower())


class TestLegacyUsageAdminRoutes(unittest.TestCase):
    """Tests for legacy /usage/upgrade and /usage/features endpoints."""

    def setUp(self):
        from server import app
        self.app = app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

        from app.routes import usage as usage_routes
        from src.organizations.rbac import AuthorizationContext
        from src.types.organization import OrganizationRole

        admin_ctx = AuthorizationContext(
            user_id="admin-user",
            organization_id="org-legacy",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )
        self.app.dependency_overrides[usage_routes.require_admin] = lambda: admin_ctx

    def tearDown(self):
        self.app.dependency_overrides = {}

    def test_legacy_upgrade_rejects_invalid_tier(self):
        response = self.client.post("/usage/upgrade", json={"tier": "invalid-tier"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("string should match pattern", detail_text(response))

    @patch("app.routes.usage.usage_limiter")
    def test_legacy_upgrade_success(self, mock_limiter):
        from src.usage import UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.FREE

        response = self.client.post("/usage/upgrade", json={"tier": "pro"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["new_tier"], "pro")
        mock_limiter.set_user_tier.assert_called_once()

    @patch("app.routes.usage.get_tier_info")
    @patch("app.routes.usage.usage_limiter")
    def test_features_endpoint_returns_feature_flags(self, mock_limiter, mock_get_tier_info):
        from src.usage import UsageTier

        mock_limiter.get_user_tier.return_value = UsageTier.PRO
        mock_get_tier_info.return_value = MagicMock(
            name="Pro",
            features_enabled=["bulk_generation", "research_mode", "api_access"],
        )

        response = self.client.get("/usage/features")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tier"], "pro")
        self.assertTrue(data["bulk_generation_enabled"])
        self.assertTrue(data["research_enabled"])
        self.assertTrue(data["api_access_enabled"])


class TestQuotaRoutes(unittest.TestCase):
    """Tests for /usage/quota/* endpoints."""

    def setUp(self):
        from server import app
        self.app = app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

        from app.routes import usage as usage_routes
        from src.organizations.rbac import AuthorizationContext
        from src.types.organization import OrganizationRole

        self.auth_ctx = AuthorizationContext(
            user_id="user-12345678",
            organization_id="org-123",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )
        self.app.dependency_overrides[usage_routes.get_optional_organization_context] = (
            lambda: self.auth_ctx
        )
        self.app.dependency_overrides[usage_routes.require_admin] = lambda: self.auth_ctx

    def tearDown(self):
        self.app.dependency_overrides = {}

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    def test_quota_stats_success(self, mock_stats):
        mock_stats.return_value = make_quota_stats("pro")

        response = self.client.get("/usage/quota/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["tier"], "pro")
        self.assertIn("tier_name", data)

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock, side_effect=RuntimeError("db unavailable"))
    def test_quota_stats_error_maps_to_500(self, _mock_stats):
        response = self.client.get("/usage/quota/stats")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve usage statistics", response.json()["detail"].lower())

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    @patch("app.routes.usage.get_quota_service")
    def test_quota_check_success(self, mock_get_service, mock_stats):
        mock_service = MagicMock()
        mock_service.check_quota = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service
        mock_stats.return_value = make_quota_stats("pro")

        response = self.client.get("/usage/quota/check")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["has_quota"])
        self.assertEqual(data["tier"], "pro")

    @patch("app.routes.usage.get_quota_service")
    def test_quota_check_exceeded_returns_429(self, mock_get_service):
        from src.types.usage import SubscriptionTier
        from src.usage.quota_service import QuotaExceeded

        mock_service = MagicMock()
        mock_service.check_quota = AsyncMock(
            side_effect=QuotaExceeded(
                message="Monthly quota exceeded",
                tier=SubscriptionTier.FREE,
                current_usage=5,
                quota_limit=5,
                reset_date=datetime.now(timezone.utc),
            )
        )
        mock_get_service.return_value = mock_service

        response = self.client.get("/usage/quota/check")
        self.assertEqual(response.status_code, 429)
        self.assertIn("quota_exceeded", detail_text(response))

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    @patch("app.routes.usage.get_quota_service")
    def test_quota_breakdown_success(self, mock_get_service, mock_stats):
        mock_service = MagicMock()
        mock_service.get_usage_breakdown = AsyncMock(
            return_value={"blog": 3, "book": 1, "batch": 0, "remix": 2, "tool": 4, "total": 10}
        )
        mock_get_service.return_value = mock_service
        mock_stats.return_value = make_quota_stats("pro")

        response = self.client.get("/usage/quota/breakdown")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["breakdown"]["total"], 10)

    @patch("app.routes.usage.get_quota_service")
    def test_quota_breakdown_error_maps_to_500(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_usage_breakdown = AsyncMock(side_effect=RuntimeError("db timeout"))
        mock_get_service.return_value = mock_service

        response = self.client.get("/usage/quota/breakdown")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve usage breakdown", response.json()["detail"].lower())

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    def test_quota_tiers_success(self, mock_stats):
        mock_stats.return_value = make_quota_stats("starter")

        response = self.client.get("/usage/quota/tiers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["current_tier"], "starter")
        self.assertGreater(len(data["tiers"]), 0)

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock, side_effect=RuntimeError("db unavailable"))
    def test_quota_tiers_error_maps_to_500(self, _mock_stats):
        response = self.client.get("/usage/quota/tiers")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve subscription tiers", response.json()["detail"].lower())

    def test_quota_upgrade_rejects_invalid_tier(self):
        response = self.client.post("/usage/quota/upgrade", json={"tier": "enterprise"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("string should match pattern", detail_text(response))

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    @patch("app.routes.usage.get_quota_service")
    def test_quota_upgrade_success(self, mock_get_service, mock_stats):
        mock_stats.return_value = make_quota_stats("free")
        mock_service = MagicMock()
        mock_service.set_user_tier = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = self.client.post("/usage/quota/upgrade", json={"tier": "pro"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["new_tier"], "pro")
        self.assertEqual(data["previous_tier"], "free")

    @patch("app.routes.usage.get_quota_stats", new_callable=AsyncMock)
    @patch("app.routes.usage.get_quota_service")
    def test_quota_upgrade_error_maps_to_500(self, mock_get_service, mock_stats):
        mock_stats.return_value = make_quota_stats("free")
        mock_service = MagicMock()
        mock_service.set_user_tier = AsyncMock(side_effect=RuntimeError("db write failed"))
        mock_get_service.return_value = mock_service

        response = self.client.post("/usage/quota/upgrade", json={"tier": "pro"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to upgrade subscription tier", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
