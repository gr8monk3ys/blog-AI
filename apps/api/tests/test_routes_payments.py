"""
Route-level tests for payment and subscription endpoints.

These tests exercise API behavior (status codes + payloads) for:
- checkout session creation
- Stripe webhook handling
- customer portal session creation
- subscription status retrieval
- public pricing endpoint
"""

import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

# Set environment before imports
os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.types.payments import SubscriptionStatus, SubscriptionTier


CHECKOUT_PAYLOAD = {
    "price_id": "price_pro_month",
    "success_url": "https://app.example.com/success",
    "cancel_url": "https://app.example.com/cancel",
}

PORTAL_PAYLOAD = {
    "return_url": "https://app.example.com/settings/billing"
}


def detail_text(response) -> str:
    """Normalize API error detail into a lowercase string for assertions."""
    detail = response.json().get("detail")
    if isinstance(detail, dict):
        return str(detail.get("error", detail)).lower()
    return str(detail).lower()


class TestPaymentCheckoutRoute(unittest.TestCase):
    """Tests for POST /api/payments/create-checkout-session."""

    def setUp(self):
        from server import app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    @patch("app.routes.payments.stripe_service._api_key", None)
    def test_checkout_returns_400_when_stripe_not_configured(self):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("not configured", detail_text(response))

    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=False)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_rejects_unconfigured_price_id(self, _mock_price):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid price_id", detail_text(response))

    @patch("app.routes.payments.stripe_service.get_tier_for_price_id", return_value=SubscriptionTier.FREE)
    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=True)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_rejects_free_tier_price(self, _mock_price, _mock_tier):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid price_id", detail_text(response))

    @patch("app.routes.payments.stripe_service.get_tier_for_price_id", return_value=SubscriptionTier.BUSINESS)
    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=True)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_rejects_business_when_flag_disabled(self, _mock_price, _mock_tier):
        with patch.dict(os.environ, {"ENABLE_BUSINESS_TIER": "false"}, clear=False):
            response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("business tier", detail_text(response))

    @patch(
        "app.routes.payments.stripe_service.create_checkout_session",
        new_callable=AsyncMock,
        return_value={"session_id": "cs_test_123", "url": "https://checkout.stripe.test/cs_test_123"},
    )
    @patch("app.routes.payments.stripe_service.get_tier_for_price_id", return_value=SubscriptionTier.PRO)
    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=True)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_success(self, mock_create, _mock_price, _mock_tier):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["session_id"], "cs_test_123")
        self.assertIn("checkout.stripe.test", data["url"])
        mock_create.assert_called_once()

    @patch(
        "app.routes.payments.stripe_service.create_checkout_session",
        new_callable=AsyncMock,
        side_effect=ValueError("invalid Stripe configuration"),
    )
    @patch("app.routes.payments.stripe_service.get_tier_for_price_id", return_value=SubscriptionTier.PRO)
    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=True)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_value_error_maps_to_400(self, _mock_create, _mock_price, _mock_tier):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("configuration", detail_text(response))

    @patch(
        "app.routes.payments.stripe_service.create_checkout_session",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    )
    @patch("app.routes.payments.stripe_service.get_tier_for_price_id", return_value=SubscriptionTier.PRO)
    @patch("app.routes.payments.stripe_service.is_configured_price_id", return_value=True)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_checkout_unexpected_error_maps_to_500(self, _mock_create, _mock_price, _mock_tier):
        response = self.client.post("/api/payments/create-checkout-session", json=CHECKOUT_PAYLOAD)
        self.assertEqual(response.status_code, 500)
        self.assertIn("error occurred", detail_text(response))


class TestPaymentWebhookRoute(unittest.TestCase):
    """Tests for POST /api/payments/webhook."""

    def setUp(self):
        from server import app
        self.client = TestClient(app)

    def test_webhook_rejects_missing_signature_header(self):
        response = self.client.post("/api/payments/webhook", json={"x": 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn("stripe-signature", detail_text(response))

    @patch("app.routes.payments.sync_webhook_event", new_callable=AsyncMock, return_value={"synced": True, "action": "upsert", "user_id": "user_12345678"})
    @patch(
        "app.routes.payments.stripe_service.handle_webhook",
        return_value={"event_type": "invoice.paid", "event_id": "evt_1", "user_id": "user_12345678"},
    )
    def test_webhook_success_when_synced(self, _mock_handle, _mock_sync):
        response = self.client.post(
            "/api/payments/webhook",
            content=b'{"id":"evt_1"}',
            headers={
                "Stripe-Signature": "t=1,v1=sig",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("invoice.paid", response.json()["message"])

    @patch("app.routes.payments.sync_webhook_event", new_callable=AsyncMock, return_value={"synced": False, "reason": "not-relevant"})
    @patch(
        "app.routes.payments.stripe_service.handle_webhook",
        return_value={"event_type": "customer.subscription.updated", "event_id": "evt_2"},
    )
    def test_webhook_success_when_not_synced(self, _mock_handle, _mock_sync):
        response = self.client.post(
            "/api/payments/webhook",
            content=b'{"id":"evt_2"}',
            headers={
                "Stripe-Signature": "t=1,v1=sig",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("customer.subscription.updated", response.json()["message"])

    @patch(
        "app.routes.payments.stripe_service.handle_webhook",
        side_effect=ValueError("Invalid webhook signature"),
    )
    def test_webhook_value_error_maps_to_400(self, _mock_handle):
        response = self.client.post(
            "/api/payments/webhook",
            content=b'{"id":"evt_bad"}',
            headers={
                "Stripe-Signature": "t=1,v1=bad",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid webhook signature", detail_text(response))

    @patch("app.routes.payments.sync_webhook_event", new_callable=AsyncMock, side_effect=RuntimeError("db down"))
    @patch(
        "app.routes.payments.stripe_service.handle_webhook",
        return_value={"event_type": "invoice.payment_failed", "event_id": "evt_3"},
    )
    def test_webhook_unexpected_error_maps_to_500(self, _mock_handle, _mock_sync):
        response = self.client.post(
            "/api/payments/webhook",
            content=b'{"id":"evt_3"}',
            headers={
                "Stripe-Signature": "t=1,v1=sig",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to process webhook", detail_text(response))


class TestPaymentPortalRoute(unittest.TestCase):
    """Tests for POST /api/payments/create-portal-session."""

    def setUp(self):
        from server import app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    @patch("app.routes.payments.stripe_service._api_key", None)
    def test_portal_returns_400_when_stripe_not_configured(self):
        response = self.client.post("/api/payments/create-portal-session", json=PORTAL_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("not configured", detail_text(response))

    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_portal_requires_existing_customer(self, _mock_customer):
        response = self.client.post("/api/payments/create-portal-session", json=PORTAL_PAYLOAD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("subscribe first", detail_text(response))

    @patch("app.routes.payments.stripe_service.create_customer_portal_session", new_callable=AsyncMock, return_value="https://billing.stripe.test/portal")
    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, return_value="cus_123")
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_portal_success(self, _mock_customer, _mock_portal):
        response = self.client.post("/api/payments/create-portal-session", json=PORTAL_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("billing.stripe.test", response.json()["url"])

    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, side_effect=ValueError("bad setup"))
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_portal_value_error_maps_to_400(self, _mock_customer):
        response = self.client.post("/api/payments/create-portal-session", json=PORTAL_PAYLOAD)
        self.assertEqual(response.status_code, 400)

    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, side_effect=RuntimeError("boom"))
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_portal_unexpected_error_maps_to_500(self, _mock_customer):
        response = self.client.post("/api/payments/create-portal-session", json=PORTAL_PAYLOAD)
        self.assertEqual(response.status_code, 500)
        self.assertIn("error occurred", detail_text(response))


class TestPaymentStatusAndPricingRoutes(unittest.TestCase):
    """Tests for GET /api/payments/subscription-status and /pricing."""

    def setUp(self):
        from server import app
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    @patch("app.routes.payments.stripe_service._api_key", None)
    def test_subscription_status_returns_free_when_unconfigured(self):
        response = self.client.get("/api/payments/subscription-status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["has_subscription"])
        self.assertEqual(data["tier"], "free")

    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_subscription_status_returns_free_without_customer(self, _mock_customer):
        response = self.client.get("/api/payments/subscription-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tier"], "free")

    @patch(
        "app.routes.payments.stripe_service.get_subscription_status",
        new_callable=AsyncMock,
        return_value=SubscriptionStatus(
            has_subscription=True,
            tier=SubscriptionTier.PRO,
            status="active",
            customer_id="cus_123",
            generations_limit=200,
        ),
    )
    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, return_value="cus_123")
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_subscription_status_returns_active_subscription(self, _mock_customer, _mock_status):
        response = self.client.get("/api/payments/subscription-status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["has_subscription"])
        self.assertEqual(data["tier"], "pro")

    @patch("app.routes.payments.stripe_service.get_customer_id_for_user", new_callable=AsyncMock, side_effect=RuntimeError("db down"))
    @patch("app.routes.payments.stripe_service._api_key", "sk_test_123")
    def test_subscription_status_unexpected_error_maps_to_500(self, _mock_customer):
        response = self.client.get("/api/payments/subscription-status")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve subscription status", detail_text(response))

    @patch("app.routes.payments.stripe_service.get_price_ids_for_tier")
    def test_pricing_hides_business_price_ids_when_flag_disabled(self, mock_price_ids):
        mock_price_ids.return_value = {"month": "price_m", "year": "price_y"}
        with patch.dict(os.environ, {"ENABLE_BUSINESS_TIER": "false"}, clear=False):
            response = self.client.get("/api/payments/pricing")
        self.assertEqual(response.status_code, 200)
        tiers = response.json()["tiers"]
        business = next(t for t in tiers if t["id"] == "business")
        self.assertNotIn("stripe_price_id_monthly", business)
        self.assertNotIn("stripe_price_id_yearly", business)

    @patch("app.routes.payments.stripe_service.get_price_ids_for_tier")
    def test_pricing_includes_business_price_ids_when_enabled(self, mock_price_ids):
        mock_price_ids.return_value = {"month": "price_m", "year": "price_y"}
        with patch.dict(os.environ, {"ENABLE_BUSINESS_TIER": "true"}, clear=False):
            response = self.client.get("/api/payments/pricing")
        self.assertEqual(response.status_code, 200)
        tiers = response.json()["tiers"]
        business = next(t for t in tiers if t["id"] == "business")
        self.assertEqual(business.get("stripe_price_id_monthly"), "price_m")
        self.assertEqual(business.get("stripe_price_id_yearly"), "price_y")

    @patch("app.routes.payments.get_tier_config", side_effect=RuntimeError("config unavailable"))
    @patch("app.routes.payments.stripe_service.get_price_ids_for_tier", return_value={"month": None, "year": None})
    def test_pricing_falls_back_when_usage_tier_lookup_fails(self, _mock_price_ids, _mock_tier):
        response = self.client.get("/api/payments/pricing")
        self.assertEqual(response.status_code, 200)
        tiers = response.json()["tiers"]
        self.assertTrue(all("daily_limit" not in tier for tier in tiers))
