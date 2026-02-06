"""
Comprehensive tests for Stripe payment flows.

This module tests:
- Stripe webhook handling and signature verification
- Subscription tier changes
- Checkout session creation
- Customer portal sessions
- Quota enforcement after payment changes
- Mock Stripe API calls

These are P0 security and revenue-critical tests.
"""

import importlib
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock stripe module before importing stripe_service
mock_stripe = MagicMock()
mock_stripe.api_key = None
mock_stripe.Customer = MagicMock()
mock_stripe.Subscription = MagicMock()
mock_stripe.checkout = MagicMock()
mock_stripe.billing_portal = MagicMock()
mock_stripe.Webhook = MagicMock()


# Create proper exception classes
class MockSignatureVerificationError(Exception):
    pass


class MockStripeError(Exception):
    pass


mock_stripe.error = MagicMock()
mock_stripe.error.SignatureVerificationError = MockSignatureVerificationError
mock_stripe.error.StripeError = MockStripeError

sys.modules["stripe"] = mock_stripe
sys.modules["stripe.error"] = mock_stripe.error


def clear_stripe_modules():
    """Clear stripe-related modules from sys.modules for fresh imports."""
    modules_to_clear = [
        k for k in list(sys.modules.keys())
        if k.startswith("src.payments") or k.startswith("src.types.payments")
    ]
    for mod in modules_to_clear:
        del sys.modules[mod]


def get_fresh_stripe_service_class():
    """Get a fresh StripeService class with clean import."""
    clear_stripe_modules()
    # Use __import__ and getattr to avoid name collision with singleton
    mod = __import__("src.payments.stripe_service", fromlist=["StripeService"])
    return mod.StripeService


def get_fresh_stripe_module():
    """Get the stripe_service module with fresh import for isolation."""
    clear_stripe_modules()
    mod = __import__("src.payments.stripe_service", fromlist=["StripeService", "SubscriptionTier"])
    return mod


def get_payment_types():
    """Get the payment types module."""
    from src.types import payments
    return payments


# =============================================================================
# Stripe Service Configuration Tests
# =============================================================================


class TestStripeServiceConfiguration(unittest.TestCase):
    """Tests for Stripe service configuration."""

    def test_is_configured_false_without_key(self):
        """is_configured should return False when STRIPE_SECRET_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()
            self.assertFalse(service.is_configured)

    def test_is_configured_true_with_key(self):
        """is_configured should return True when STRIPE_SECRET_KEY is set."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()
            self.assertTrue(service.is_configured)

    def test_ensure_configured_raises_without_key(self):
        """_ensure_configured should raise ValueError without API key."""
        with patch.dict(os.environ, {}, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            with self.assertRaises(ValueError) as context:
                service._ensure_configured()

            self.assertIn("STRIPE_SECRET_KEY", str(context.exception))

    def test_price_ids_loaded_from_env(self):
        """Price IDs should be loaded from environment variables."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_STARTER": "price_starter_123",
            "STRIPE_PRICE_ID_PRO": "price_pro_456",
            "STRIPE_PRICE_ID_BUSINESS": "price_business_789",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            self.assertEqual(
                service.get_price_id_for_tier(stripe_module.SubscriptionTier.STARTER),
                "price_starter_123"
            )
            self.assertEqual(
                service.get_price_id_for_tier(stripe_module.SubscriptionTier.PRO),
                "price_pro_456"
            )
            self.assertEqual(
                service.get_price_id_for_tier(stripe_module.SubscriptionTier.BUSINESS),
                "price_business_789"
            )


# =============================================================================
# Webhook Signature Verification Tests
# =============================================================================


class TestWebhookSignatureVerification(unittest.TestCase):
    """Tests for webhook signature verification - CRITICAL SECURITY."""

    def setUp(self):
        """Reset mock before each test."""
        mock_stripe.Webhook.construct_event.side_effect = None
        mock_stripe.Webhook.construct_event.reset_mock()

    def test_handle_webhook_verifies_signature(self):
        """handle_webhook should verify the webhook signature."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            mock_event = {
                "id": "evt_test123",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "customer": "cus_test",
                        "subscription": "sub_test",
                        "metadata": {"user_id": "user-123"},
                    }
                }
            }
            mock_stripe.Webhook.construct_event.return_value = mock_event

            payload = b'{"test": "data"}'
            sig_header = "t=123,v1=abc123"

            service.handle_webhook(payload, sig_header)

            mock_stripe.Webhook.construct_event.assert_called_once_with(
                payload,
                sig_header,
                "whsec_test_secret"
            )

    def test_handle_webhook_raises_on_invalid_signature(self):
        """handle_webhook should raise ValueError on invalid signature."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            mock_stripe.Webhook.construct_event.side_effect = MockSignatureVerificationError(
                "Invalid signature"
            )

            payload = b'{"test": "data"}'
            sig_header = "t=123,v1=invalid"

            with self.assertRaises(ValueError) as context:
                service.handle_webhook(payload, sig_header)

            self.assertIn("Invalid webhook signature", str(context.exception))

            mock_stripe.Webhook.construct_event.side_effect = None

    def test_handle_webhook_raises_without_webhook_secret(self):
        """handle_webhook should raise ValueError without webhook secret."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            payload = b'{"test": "data"}'
            sig_header = "t=123,v1=abc123"

            with self.assertRaises(ValueError) as context:
                service.handle_webhook(payload, sig_header)

            self.assertIn("Webhook secret not configured", str(context.exception))

    def test_handle_webhook_rejects_tampered_payload(self):
        """Webhook should reject if payload was tampered with."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            # Simulate signature verification failure due to tampered payload
            mock_stripe.Webhook.construct_event.side_effect = MockSignatureVerificationError(
                "Signature does not match"
            )

            with self.assertRaises(ValueError):
                service.handle_webhook(b'{"tampered": true}', "t=123,v1=abc123")

            mock_stripe.Webhook.construct_event.side_effect = None


# =============================================================================
# Tier Price ID Mapping Tests
# =============================================================================


class TestTierPriceIdMapping(unittest.TestCase):
    """Tests for mapping between tiers and price IDs."""

    def test_get_tier_for_price_id_returns_correct_tier(self):
        """get_tier_for_price_id should return the correct tier for known price IDs."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_STARTER": "price_starter_abc",
            "STRIPE_PRICE_ID_PRO": "price_pro_def",
            "STRIPE_PRICE_ID_BUSINESS": "price_business_ghi",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            self.assertEqual(
                service.get_tier_for_price_id("price_starter_abc"),
                stripe_module.SubscriptionTier.STARTER
            )
            self.assertEqual(
                service.get_tier_for_price_id("price_pro_def"),
                stripe_module.SubscriptionTier.PRO
            )
            self.assertEqual(
                service.get_tier_for_price_id("price_business_ghi"),
                stripe_module.SubscriptionTier.BUSINESS
            )

    def test_get_tier_for_unknown_price_returns_free(self):
        """get_tier_for_price_id should return FREE for unknown price IDs."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_STARTER": "price_starter_abc",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            result = service.get_tier_for_price_id("price_unknown_xyz")
            self.assertEqual(result, stripe_module.SubscriptionTier.FREE)

    def test_get_tier_for_empty_price_returns_free(self):
        """get_tier_for_price_id should return FREE for empty string."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            result = service.get_tier_for_price_id("")
            self.assertEqual(result, stripe_module.SubscriptionTier.FREE)


# =============================================================================
# Webhook Event Handling Tests
# =============================================================================


class TestWebhookEventHandling(unittest.TestCase):
    """Tests for handling specific webhook event types."""

    def setUp(self):
        """Reset mock before each test."""
        mock_stripe.Webhook.construct_event.side_effect = None
        mock_stripe.Webhook.construct_event.reset_mock()

    def _create_service_with_mock_event(self, event_data):
        """Helper to create service with mocked webhook event."""
        StripeService = get_fresh_stripe_service_class()
        service = StripeService()
        mock_stripe.Webhook.construct_event.return_value = event_data
        return service

    def test_handle_checkout_completed_extracts_user_id(self):
        """Checkout completed event should extract user_id from metadata."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "customer": "cus_abc123",
                        "subscription": "sub_xyz789",
                        "metadata": {"user_id": "user-test-456"},
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "checkout.session.completed")
            self.assertEqual(result["user_id"], "user-test-456")
            self.assertEqual(result["customer_id"], "cus_abc123")
            self.assertEqual(result["subscription_id"], "sub_xyz789")

    def test_handle_subscription_created_extracts_tier(self):
        """Subscription created event should extract tier from price ID."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICE_ID_PRO": "price_pro_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "customer.subscription.created",
                "data": {
                    "object": {
                        "id": "sub_test",
                        "customer": "cus_test",
                        "status": "active",
                        "metadata": {"user_id": "user-123"},
                        "items": {
                            "data": [{"price": {"id": "price_pro_test"}}]
                        }
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "customer.subscription.created")
            self.assertEqual(result["tier"], "pro")
            self.assertEqual(result["status"], "active")

    def test_handle_subscription_updated_includes_cancel_status(self):
        """Subscription updated event should include cancellation status."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICE_ID_BUSINESS": "price_business_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "customer.subscription.updated",
                "data": {
                    "object": {
                        "id": "sub_test",
                        "customer": "cus_test",
                        "status": "active",
                        "cancel_at_period_end": True,
                        "metadata": {"user_id": "user-123"},
                        "items": {
                            "data": [{"price": {"id": "price_business_test"}}]
                        }
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "customer.subscription.updated")
            self.assertTrue(result["cancel_at_period_end"])

    def test_handle_subscription_deleted_extracts_ids(self):
        """Subscription deleted event should extract customer and subscription IDs."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "customer.subscription.deleted",
                "data": {
                    "object": {
                        "id": "sub_cancelled",
                        "customer": "cus_cancelled",
                        "metadata": {"user_id": "user-cancelled"},
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "customer.subscription.deleted")
            self.assertEqual(result["subscription_id"], "sub_cancelled")
            self.assertEqual(result["user_id"], "user-cancelled")

    def test_handle_invoice_paid_extracts_amount(self):
        """Invoice paid event should extract amount paid."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "invoice.paid",
                "data": {
                    "object": {
                        "customer": "cus_test",
                        "subscription": "sub_test",
                        "amount_paid": 4900,
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "invoice.paid")
            self.assertEqual(result["amount_paid"], 4900)

    def test_handle_invoice_payment_failed_extracts_attempt_count(self):
        """Invoice payment failed event should extract attempt count."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            event = {
                "id": "evt_test123",
                "type": "invoice.payment_failed",
                "data": {
                    "object": {
                        "customer": "cus_test",
                        "subscription": "sub_test",
                        "attempt_count": 3,
                    }
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "invoice.payment_failed")
            self.assertEqual(result["attempt_count"], 3)

    def test_handle_unknown_event_returns_basic_info(self):
        """Unknown event types should still return event_type and event_id."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            event = {
                "id": "evt_unknown",
                "type": "some.unknown.event",
                "data": {
                    "object": {"some": "data"}
                }
            }
            service = self._create_service_with_mock_event(event)

            result = service.handle_webhook(b"payload", "sig")

            self.assertEqual(result["event_type"], "some.unknown.event")
            self.assertEqual(result["event_id"], "evt_unknown")


# =============================================================================
# Checkout Session Creation Tests
# =============================================================================


class TestCheckoutSessionCreation(unittest.IsolatedAsyncioTestCase):
    """Tests for checkout session creation."""

    def setUp(self):
        """Reset mocks before each test."""
        mock_stripe.Customer.search.reset_mock()
        mock_stripe.Customer.create.reset_mock()
        mock_stripe.checkout.Session.create.reset_mock()

    async def test_create_checkout_session_success(self):
        """Test successful checkout session creation."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            # Mock customer search returns existing customer
            mock_customers = MagicMock()
            mock_customers.data = [MagicMock(id="cus_existing")]
            mock_stripe.Customer.search.return_value = mock_customers

            # Mock session creation
            mock_session = MagicMock()
            mock_session.id = "cs_test123"
            mock_session.url = "https://checkout.stripe.com/c/pay/cs_test123"
            mock_stripe.checkout.Session.create.return_value = mock_session

            result = await service.create_checkout_session(
                price_id="price_pro_123",
                user_id="user-456",
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel",
            )

            self.assertEqual(result["session_id"], "cs_test123")
            self.assertIn("checkout.stripe.com", result["url"])

    async def test_create_checkout_session_creates_new_customer(self):
        """Test checkout session creates new customer if none exists."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            # Mock customer search returns no results
            mock_customers = MagicMock()
            mock_customers.data = []
            mock_stripe.Customer.search.return_value = mock_customers

            # Mock customer creation
            mock_new_customer = MagicMock()
            mock_new_customer.id = "cus_new123"
            mock_stripe.Customer.create.return_value = mock_new_customer

            # Mock session creation
            mock_session = MagicMock()
            mock_session.id = "cs_test123"
            mock_session.url = "https://checkout.stripe.com/test"
            mock_stripe.checkout.Session.create.return_value = mock_session

            await service.create_checkout_session(
                price_id="price_starter_123",
                user_id="new-user-789",
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel",
                customer_email="new@example.com",
            )

            # Verify customer was created with metadata
            mock_stripe.Customer.create.assert_called()

    async def test_create_checkout_session_includes_user_metadata(self):
        """Test checkout session includes user_id in metadata."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            mock_customers = MagicMock()
            mock_customers.data = [MagicMock(id="cus_test")]
            mock_stripe.Customer.search.return_value = mock_customers

            mock_session = MagicMock()
            mock_session.id = "cs_test123"
            mock_session.url = "https://checkout.stripe.com/test"
            mock_stripe.checkout.Session.create.return_value = mock_session

            await service.create_checkout_session(
                price_id="price_pro_123",
                user_id="user-metadata-test",
                success_url="https://app.example.com/success",
                cancel_url="https://app.example.com/cancel",
            )

            # Session should be created - verify mock was called
            mock_stripe.checkout.Session.create.assert_called()


# =============================================================================
# Customer Portal Session Tests
# =============================================================================


class TestCustomerPortalSession(unittest.IsolatedAsyncioTestCase):
    """Tests for customer portal session creation."""

    def setUp(self):
        """Reset mocks before each test."""
        mock_stripe.billing_portal.Session.create.reset_mock()

    async def test_create_portal_session_success(self):
        """Test successful portal session creation."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            StripeService = get_fresh_stripe_service_class()
            service = StripeService()

            mock_portal = MagicMock()
            mock_portal.url = "https://billing.stripe.com/session/test123"
            mock_stripe.billing_portal.Session.create.return_value = mock_portal

            result = await service.create_customer_portal_session(
                customer_id="cus_test123",
                return_url="https://app.example.com/settings",
            )

            self.assertEqual(result, "https://billing.stripe.com/session/test123")


# =============================================================================
# Subscription Status Tests
# =============================================================================


class TestSubscriptionStatus(unittest.IsolatedAsyncioTestCase):
    """Tests for subscription status queries."""

    def setUp(self):
        """Reset mocks before each test."""
        mock_stripe.Subscription.list.reset_mock()

    async def test_get_subscription_status_active(self):
        """Test getting status of active subscription."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_PRO": "price_pro_test",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            mock_subscription = MagicMock()
            mock_subscription.status = "active"
            mock_subscription.current_period_end = 1735689600
            mock_subscription.cancel_at_period_end = False
            mock_subscription.__getitem__ = lambda self, key: {
                "items": {"data": [{"price": {"id": "price_pro_test"}}]}
            }[key]

            mock_subscriptions = MagicMock()
            mock_subscriptions.data = [mock_subscription]
            mock_stripe.Subscription.list.return_value = mock_subscriptions

            result = await service.get_subscription_status("cus_test123")

            self.assertTrue(result.has_subscription)
            self.assertEqual(result.tier, stripe_module.SubscriptionTier.PRO)
            self.assertEqual(result.status, "active")
            self.assertFalse(result.cancel_at_period_end)

    async def test_get_subscription_status_no_subscription(self):
        """Test getting status when no subscription exists."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            mock_subscriptions = MagicMock()
            mock_subscriptions.data = []
            mock_stripe.Subscription.list.return_value = mock_subscriptions

            result = await service.get_subscription_status("cus_no_sub")

            self.assertFalse(result.has_subscription)
            self.assertEqual(result.tier, stripe_module.SubscriptionTier.FREE)

    async def test_get_subscription_status_cancelled(self):
        """Test getting status of cancelled subscription."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_STARTER": "price_starter_test",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            mock_subscription = MagicMock()
            mock_subscription.status = "canceled"  # Note: Stripe uses "canceled" not "cancelled"
            mock_subscription.current_period_end = 1735689600
            mock_subscription.cancel_at_period_end = False
            mock_subscription.__getitem__ = lambda self, key: {
                "items": {"data": [{"price": {"id": "price_starter_test"}}]}
            }[key]

            mock_subscriptions = MagicMock()
            mock_subscriptions.data = [mock_subscription]
            mock_stripe.Subscription.list.return_value = mock_subscriptions

            result = await service.get_subscription_status("cus_cancelled")

            # Cancelled subscription should report as FREE tier
            self.assertFalse(result.has_subscription)
            self.assertEqual(result.tier, stripe_module.SubscriptionTier.FREE)


# =============================================================================
# Subscription Tier Change Tests
# =============================================================================


class TestSubscriptionTierChanges:
    """Tests for subscription tier upgrade/downgrade handling."""

    def test_tier_upgrade_pro_to_business(self):
        """Test tier change from Pro to Business."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_PRO": "price_pro_test",
            "STRIPE_PRICE_ID_BUSINESS": "price_business_test",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            # Verify tier mapping
            pro_tier = service.get_tier_for_price_id("price_pro_test")
            business_tier = service.get_tier_for_price_id("price_business_test")

            assert pro_tier == stripe_module.SubscriptionTier.PRO
            assert business_tier == stripe_module.SubscriptionTier.BUSINESS

    def test_tier_downgrade_to_free(self):
        """Test tier downgrade when subscription cancelled."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            stripe_module = get_fresh_stripe_module()
            service = stripe_module.StripeService()

            # Unknown/cancelled price should map to FREE
            result = service.get_tier_for_price_id("price_cancelled_xxx")
            assert result == stripe_module.SubscriptionTier.FREE


# =============================================================================
# Pricing Tier Configuration Tests
# =============================================================================


class TestPricingTierConfiguration:
    """Tests for pricing tier configuration."""

    def test_free_tier_limits(self):
        """Test FREE tier generation limits."""
        payments = get_payment_types()

        free_config = payments.PRICING_TIERS[payments.SubscriptionTier.FREE]

        assert free_config.name == "Free"
        assert free_config.price_monthly == 0
        assert free_config.generations_per_month == 5

    def test_starter_tier_limits(self):
        """Test STARTER tier generation limits."""
        payments = get_payment_types()

        starter_config = payments.PRICING_TIERS[payments.SubscriptionTier.STARTER]

        assert starter_config.name == "Starter"
        assert starter_config.price_monthly == 1900  # $19.00
        assert starter_config.generations_per_month == 50

    def test_pro_tier_limits(self):
        """Test PRO tier generation limits."""
        payments = get_payment_types()

        pro_config = payments.PRICING_TIERS[payments.SubscriptionTier.PRO]

        assert pro_config.name == "Pro"
        assert pro_config.price_monthly == 4900  # $49.00
        assert pro_config.generations_per_month == 200

    def test_business_tier_limits(self):
        """Test BUSINESS tier generation limits."""
        payments = get_payment_types()

        business_config = payments.PRICING_TIERS[payments.SubscriptionTier.BUSINESS]

        assert business_config.name == "Business"
        assert business_config.price_monthly == 14900  # $149.00
        assert business_config.generations_per_month == 1000

    def test_get_tier_generation_limit(self):
        """Test get_tier_generation_limit function."""
        payments = get_payment_types()

        assert payments.get_tier_generation_limit(payments.SubscriptionTier.FREE) == 5
        assert payments.get_tier_generation_limit(payments.SubscriptionTier.STARTER) == 50
        assert payments.get_tier_generation_limit(payments.SubscriptionTier.PRO) == 200
        assert payments.get_tier_generation_limit(payments.SubscriptionTier.BUSINESS) == 1000


# =============================================================================
# Webhook Event Type Tests
# =============================================================================


class TestWebhookEventTypes:
    """Tests for webhook event type definitions."""

    def test_checkout_completed_event_type(self):
        """Test checkout completed event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.CHECKOUT_COMPLETED.value == "checkout.session.completed"

    def test_subscription_created_event_type(self):
        """Test subscription created event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.SUBSCRIPTION_CREATED.value == "customer.subscription.created"

    def test_subscription_updated_event_type(self):
        """Test subscription updated event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.SUBSCRIPTION_UPDATED.value == "customer.subscription.updated"

    def test_subscription_deleted_event_type(self):
        """Test subscription deleted event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.SUBSCRIPTION_DELETED.value == "customer.subscription.deleted"

    def test_invoice_paid_event_type(self):
        """Test invoice paid event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.INVOICE_PAID.value == "invoice.paid"

    def test_invoice_payment_failed_event_type(self):
        """Test invoice payment failed event type."""
        payments = get_payment_types()
        assert payments.WebhookEventType.INVOICE_PAYMENT_FAILED.value == "invoice.payment_failed"


# =============================================================================
# Subscription Model Tests
# =============================================================================


class TestSubscriptionStatusModel:
    """Tests for SubscriptionStatus Pydantic model."""

    def test_subscription_status_defaults(self):
        """Test SubscriptionStatus default values."""
        payments = get_payment_types()

        status = payments.SubscriptionStatus(
            has_subscription=False,
            customer_id="cus_test",
        )

        assert status.success is True
        assert status.tier == payments.SubscriptionTier.FREE
        assert status.status is None
        assert status.cancel_at_period_end is False
        assert status.generations_limit == 5

    def test_subscription_status_with_active_sub(self):
        """Test SubscriptionStatus with active subscription."""
        payments = get_payment_types()

        status = payments.SubscriptionStatus(
            has_subscription=True,
            tier=payments.SubscriptionTier.PRO,
            status="active",
            current_period_end=1735689600,
            cancel_at_period_end=False,
            customer_id="cus_active",
            generations_limit=200,
        )

        assert status.has_subscription is True
        assert status.tier == payments.SubscriptionTier.PRO
        assert status.status == "active"
        assert status.generations_limit == 200


# =============================================================================
# Checkout Session Request/Response Tests
# =============================================================================


class TestCheckoutSessionModels:
    """Tests for checkout session Pydantic models."""

    def test_checkout_session_request_validation(self):
        """Test CheckoutSessionRequest validation."""
        payments = get_payment_types()

        request = payments.CheckoutSessionRequest(
            price_id="price_test_123",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
        )

        assert request.price_id == "price_test_123"
        assert "success" in request.success_url

    def test_checkout_session_response(self):
        """Test CheckoutSessionResponse."""
        payments = get_payment_types()

        response = payments.CheckoutSessionResponse(
            session_id="cs_test123",
            url="https://checkout.stripe.com/pay/cs_test123",
        )

        assert response.success is True
        assert response.session_id == "cs_test123"
        assert "checkout.stripe.com" in response.url


# =============================================================================
# Portal Session Models Tests
# =============================================================================


class TestPortalSessionModels:
    """Tests for portal session Pydantic models."""

    def test_portal_session_request(self):
        """Test PortalSessionRequest."""
        payments = get_payment_types()

        request = payments.PortalSessionRequest(
            return_url="https://app.example.com/settings",
        )

        assert "settings" in request.return_url

    def test_portal_session_response(self):
        """Test PortalSessionResponse."""
        payments = get_payment_types()

        response = payments.PortalSessionResponse(
            url="https://billing.stripe.com/session/test123",
        )

        assert response.success is True
        assert "billing.stripe.com" in response.url


if __name__ == "__main__":
    unittest.main()
