"""
Tests for the subscription status/reconcile endpoints (app/routes/subscription.py).

These are money-critical, customer-facing endpoints (the source of truth for
access control) that previously had only incidental coverage (~33%). Covers the
free-user shape, DB enrichment for paid users, error handling, and the
business-tier-gated reconcile delegation.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


def make_stats(tier_name: str = "pro"):
    from src.types.usage import SubscriptionTier, UsageStats

    now = datetime.now(timezone.utc)
    return UsageStats(
        user_id="user-12345678",
        tier=SubscriptionTier(tier_name),
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


def _quota_patch(stats):
    svc = MagicMock()
    svc.get_usage_stats = AsyncMock(return_value=stats)
    return patch("app.routes.subscription.get_quota_service", return_value=svc)


class TestSubscriptionStatus(unittest.TestCase):
    def setUp(self):
        from server import app

        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    def test_free_user_without_db_returns_base_shape(self):
        with (
            _quota_patch(make_stats("free")),
            patch("app.routes.subscription.is_database_configured", return_value=False),
        ):
            resp = self.client.get("/api/subscription/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["plan"] == "free"
        assert data["status"] == "none"
        assert data["payment_status"] == "current"
        assert data["renewal_date"] is None
        assert data["cancel_at_period_end"] is False
        assert data["usage"]["limit"] == 200
        assert data["usage"]["remaining"] == 188

    def test_paid_user_enriched_from_database(self):
        period_end = datetime(2030, 1, 1, tzinfo=timezone.utc)
        sub_row = {
            "status": "active",
            "current_period_end": period_end,
            "cancel_at_period_end": True,
            "payment_status": "current",
            "tier": "pro",
        }
        with (
            _quota_patch(make_stats("pro")),
            patch("app.routes.subscription.is_database_configured", return_value=True),
            patch(
                "app.routes.subscription.db_fetchrow",
                new=AsyncMock(return_value=sub_row),
            ),
        ):
            resp = self.client.get("/api/subscription/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"
        assert data["cancel_at_period_end"] is True
        assert data["renewal_date"] is not None
        assert data["renewal_date"].startswith("2030-01-01")

    def test_paid_user_no_active_row_keeps_defaults(self):
        with (
            _quota_patch(make_stats("pro")),
            patch("app.routes.subscription.is_database_configured", return_value=True),
            patch(
                "app.routes.subscription.db_fetchrow", new=AsyncMock(return_value=None)
            ),
        ):
            resp = self.client.get("/api/subscription/status")

        assert resp.status_code == 200
        assert resp.json()["status"] == "none"

    def test_quota_failure_returns_500(self):
        with patch(
            "app.routes.subscription.get_quota_service",
            side_effect=RuntimeError("boom"),
        ):
            resp = self.client.get("/api/subscription/status")

        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert "Failed to retrieve subscription status" in body["error"]


class TestSubscriptionReconcile(unittest.TestCase):
    def setUp(self):
        from app.middleware.quota_check import require_business_tier
        from server import app

        self.app = app
        self.dep = require_business_tier
        # Bypass the business-tier gate so we can exercise the handler itself.
        app.dependency_overrides[require_business_tier] = lambda: "admin-user"
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    def tearDown(self):
        self.app.dependency_overrides.pop(self.dep, None)

    def test_reconcile_delegates_to_sync_service(self):
        sync = MagicMock()
        sync.reconcile_subscriptions = AsyncMock(
            return_value={"checked": 5, "fixed": 1, "dry_run": False}
        )
        with patch(
            "src.payments.subscription_sync.get_sync_service", return_value=sync
        ):
            resp = self.client.post("/api/subscription/reconcile")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["checked"] == 5
        assert data["fixed"] == 1
        sync.reconcile_subscriptions.assert_awaited_once()

    def test_reconcile_passes_query_params(self):
        sync = MagicMock()
        sync.reconcile_subscriptions = AsyncMock(return_value={"checked": 0})
        with patch(
            "src.payments.subscription_sync.get_sync_service", return_value=sync
        ):
            resp = self.client.post(
                "/api/subscription/reconcile?dry_run=true&skip_manual_overrides=false"
            )

        assert resp.status_code == 200
        _, kwargs = sync.reconcile_subscriptions.call_args
        assert kwargs["dry_run"] is True
        assert kwargs["skip_manual_overrides"] is False


if __name__ == "__main__":
    unittest.main()
