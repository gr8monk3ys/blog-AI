"""
Tests for Stripe payment service integration.

This module tests the Stripe service including:
- Service configuration checks
- Webhook signature verification
- Tier mapping from price IDs
- Webhook event handling

These are P0 security tests - critical for production deployment.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from .stripe_mock import (
    MockSignatureVerificationError,
    MockStripeError,
    install_mock_stripe,
    mock_stripe,
)

install_mock_stripe()

# Now import the module after mocking stripe
from src.payments.stripe_service import (
    StripeService,
    SubscriptionTier,
    handle_webhook,
    stripe_service,
)


class TestStripeServiceConfiguration(unittest.TestCase):
    """Tests for Stripe service configuration."""

    def test_is_configured_false_without_key(self):
        """is_configured should return False when STRIPE_SECRET_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            service = StripeService()
            self.assertFalse(service.is_configured)

    def test_is_configured_true_with_key(self):
        """is_configured should return True when STRIPE_SECRET_KEY is set."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            service = StripeService()
            self.assertTrue(service.is_configured)

    def test_ensure_configured_raises_without_key(self):
        """_ensure_configured should raise ValueError without API key."""
        with patch.dict(os.environ, {}, clear=True):
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
            service = StripeService()

            self.assertEqual(
                service.get_price_id_for_tier(SubscriptionTier.STARTER),
                "price_starter_123"
            )
            self.assertEqual(
                service.get_price_id_for_tier(SubscriptionTier.PRO),
                "price_pro_456"
            )
            self.assertEqual(
                service.get_price_id_for_tier(SubscriptionTier.BUSINESS),
                "price_business_789"
            )


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
            service = StripeService()

            # Mock the Webhook.construct_event to return a valid event
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

            # Verify construct_event was called with correct args
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
            service = StripeService()

            # Mock construct_event to raise SignatureVerificationError
            mock_stripe.Webhook.construct_event.side_effect = MockSignatureVerificationError(
                "Invalid signature"
            )

            payload = b'{"test": "data"}'
            sig_header = "t=123,v1=invalid"

            with self.assertRaises(ValueError) as context:
                service.handle_webhook(payload, sig_header)

            self.assertIn("Invalid webhook signature", str(context.exception))

            # Reset the mock for other tests
            mock_stripe.Webhook.construct_event.side_effect = None

    def test_handle_webhook_raises_without_webhook_secret(self):
        """handle_webhook should raise ValueError without webhook secret."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            # No STRIPE_WEBHOOK_SECRET
        }, clear=True):
            service = StripeService()

            payload = b'{"test": "data"}'
            sig_header = "t=123,v1=abc123"

            with self.assertRaises(ValueError) as context:
                service.handle_webhook(payload, sig_header)

            self.assertIn("Webhook secret not configured", str(context.exception))


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
            service = StripeService()

            self.assertEqual(
                service.get_tier_for_price_id("price_starter_abc"),
                SubscriptionTier.STARTER
            )
            self.assertEqual(
                service.get_tier_for_price_id("price_pro_def"),
                SubscriptionTier.PRO
            )
            self.assertEqual(
                service.get_tier_for_price_id("price_business_ghi"),
                SubscriptionTier.BUSINESS
            )

    def test_get_tier_for_unknown_price_returns_free(self):
        """get_tier_for_price_id should return FREE for unknown price IDs."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_PRICE_ID_STARTER": "price_starter_abc",
            "STRIPE_PRICE_ID_PRO": "price_pro_def",
            "STRIPE_PRICE_ID_BUSINESS": "price_business_ghi",
        }, clear=True):
            service = StripeService()

            # Test with unknown price ID
            result = service.get_tier_for_price_id("price_unknown_xyz")
            self.assertEqual(result, SubscriptionTier.FREE)

    def test_get_tier_for_empty_price_returns_free(self):
        """get_tier_for_price_id should return FREE for empty string."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            service = StripeService()

            result = service.get_tier_for_price_id("")
            self.assertEqual(result, SubscriptionTier.FREE)

    def test_get_tier_for_none_price_returns_free(self):
        """get_tier_for_price_id should return FREE when price ID doesn't match."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
        }, clear=True):
            service = StripeService()

            # When no price IDs are configured
            result = service.get_tier_for_price_id("any_price_id")
            self.assertEqual(result, SubscriptionTier.FREE)


class TestWebhookEventHandling(unittest.TestCase):
    """Tests for handling specific webhook event types."""

    def setUp(self):
        """Reset mock before each test."""
        mock_stripe.Webhook.construct_event.side_effect = None
        mock_stripe.Webhook.construct_event.reset_mock()

    def _create_service_with_mock_event(self, event_data):
        """Helper to create service with mocked webhook event."""
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
                        "amount_paid": 4900,  # $49.00
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


class TestGlobalServiceInstance(unittest.TestCase):
    """Tests for the global stripe_service singleton."""

    def test_global_instance_is_created(self):
        """Module should export a global stripe_service instance."""
        self.assertIsNotNone(stripe_service)
        self.assertIsInstance(stripe_service, StripeService)

    def test_convenience_function_handle_webhook(self):
        """Convenience function handle_webhook should delegate to service."""
        with patch.dict(os.environ, {
            "STRIPE_SECRET_KEY": "sk_test_12345",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }, clear=True):
            mock_event = {
                "id": "evt_test",
                "type": "test.event",
                "data": {"object": {}}
            }
            mock_stripe.Webhook.construct_event.return_value = mock_event
            mock_stripe.Webhook.construct_event.side_effect = None

            # The global stripe_service was created at import time, so we need
            # to patch its internal state or create a new one
            with patch.object(stripe_service, '_api_key', 'sk_test_12345'):
                with patch.object(stripe_service, '_webhook_secret', 'whsec_test'):
                    result = handle_webhook(b"payload", "sig")
                    self.assertEqual(result["event_type"], "test.event")


if __name__ == "__main__":
    unittest.main()
