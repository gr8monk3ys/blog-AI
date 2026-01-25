"""
Tests for the subscription sync service.

This module tests the SubscriptionSyncService which handles syncing
Stripe webhook events to Supabase database state.
"""

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock stripe module before any imports that might use it
mock_stripe = MagicMock()
mock_stripe.api_key = None
mock_stripe.Customer = MagicMock()
mock_stripe.error = MagicMock()
mock_stripe.error.SignatureVerificationError = Exception
mock_stripe.error.StripeError = Exception
sys.modules["stripe"] = mock_stripe
sys.modules["stripe.error"] = mock_stripe.error

# Mock supabase module
mock_supabase = MagicMock()
mock_supabase.create_client = MagicMock()
sys.modules["supabase"] = mock_supabase

from src.types.payments import WebhookEventType
from src.types.usage import SubscriptionTier


def get_sync_module():
    """Get the subscription_sync module with proper cleanup."""
    # Clear any cached module to ensure fresh import
    if "src.payments.subscription_sync" in sys.modules:
        del sys.modules["src.payments.subscription_sync"]
    if "src.payments" in sys.modules:
        del sys.modules["src.payments"]

    import src.payments.subscription_sync as sync_module
    sync_module._sync_service = None
    return sync_module


class TestTierMapping(unittest.TestCase):
    """Tests for tier mapping between payments and usage types."""

    def test_map_valid_free_tier(self):
        """Valid 'free' tier string maps correctly."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("free")
        self.assertEqual(result, SubscriptionTier.FREE)

    def test_map_valid_starter_tier(self):
        """Valid 'starter' tier string maps correctly."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("starter")
        self.assertEqual(result, SubscriptionTier.STARTER)

    def test_map_valid_pro_tier(self):
        """Valid 'pro' tier string maps correctly."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("pro")
        self.assertEqual(result, SubscriptionTier.PRO)

    def test_map_valid_business_tier(self):
        """Valid 'business' tier string maps correctly."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("business")
        self.assertEqual(result, SubscriptionTier.BUSINESS)

    def test_map_unknown_tier_defaults_to_free(self):
        """Unknown tier string defaults to FREE."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("unknown_tier")
        self.assertEqual(result, SubscriptionTier.FREE)

    def test_map_empty_tier_defaults_to_free(self):
        """Empty tier string defaults to FREE."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("")
        self.assertEqual(result, SubscriptionTier.FREE)

    def test_map_uppercase_tier_defaults_to_free(self):
        """Uppercase tier string is not recognized (case-sensitive)."""
        sync_module = get_sync_module()
        result = sync_module._map_payments_tier_to_usage_tier("PRO")
        self.assertEqual(result, SubscriptionTier.FREE)


class TestSubscriptionSyncServiceInit(unittest.TestCase):
    """Tests for SubscriptionSyncService initialization."""

    def test_init_without_supabase_config(self):
        """Service initializes without Supabase when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            sync_module = get_sync_module()
            service = sync_module.SubscriptionSyncService()
            self.assertIsNone(service._supabase_client)

    def test_init_with_supabase_config(self):
        """Service initializes with Supabase when configured."""
        mock_client = MagicMock()
        mock_supabase.create_client.return_value = mock_client

        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "test-key"
        }, clear=True):
            sync_module = get_sync_module()
            service = sync_module.SubscriptionSyncService()
            self.assertEqual(service._supabase_client, mock_client)


class TestSyncWebhookEventRouting(unittest.IsolatedAsyncioTestCase):
    """Tests for webhook event routing in sync_webhook_event."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_route_checkout_completed(self, mock_get_quota):
        """Checkout completed event routes to correct handler."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_customer_mapping = AsyncMock()

        webhook_result = {
            "event_type": WebhookEventType.CHECKOUT_COMPLETED.value,
            "user_id": "user-123",
            "customer_id": "cus_test123",
            "subscription_id": "sub_test123",
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "checkout.session.completed")
        self.assertEqual(result["action"], "customer_mapping_stored")
        service._store_customer_mapping.assert_called_once_with("user-123", "cus_test123")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_route_subscription_created(self, mock_get_quota):
        """Subscription created event routes to correct handler."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_subscription_mapping = AsyncMock()

        webhook_result = {
            "event_type": WebhookEventType.SUBSCRIPTION_CREATED.value,
            "user_id": "user-123",
            "customer_id": "cus_test123",
            "subscription_id": "sub_test123",
            "tier": "pro",
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "customer.subscription.created")
        self.assertEqual(result["tier"], "pro")
        self.assertEqual(result["action"], "tier_activated")
        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.PRO
        )

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_route_subscription_updated(self, mock_get_quota):
        """Subscription updated event routes to correct handler."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "event_type": WebhookEventType.SUBSCRIPTION_UPDATED.value,
            "user_id": "user-123",
            "tier": "business",
            "status": "active",
            "cancel_at_period_end": False,
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "customer.subscription.updated")
        self.assertEqual(result["tier"], "business")
        self.assertEqual(result["action"], "tier_updated")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_route_subscription_deleted(self, mock_get_quota):
        """Subscription deleted event routes to correct handler."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._mark_subscription_cancelled = AsyncMock()

        webhook_result = {
            "event_type": WebhookEventType.SUBSCRIPTION_DELETED.value,
            "user_id": "user-123",
            "subscription_id": "sub_test123",
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "customer.subscription.deleted")
        self.assertEqual(result["tier"], "free")
        self.assertEqual(result["action"], "downgraded_to_free")
        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.FREE
        )

    async def test_route_invoice_paid(self):
        """Invoice paid event routes to correct handler."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment = AsyncMock()

        webhook_result = {
            "event_type": WebhookEventType.INVOICE_PAID.value,
            "user_id": "user-123",
            "subscription_id": "sub_test123",
            "amount_paid": 4900,
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "invoice.paid")
        self.assertEqual(result["amount_paid"], 4900)
        self.assertEqual(result["action"], "payment_recorded")
        service._record_payment.assert_called_once_with("user-123", "sub_test123", 4900)

    async def test_route_invoice_payment_failed(self):
        """Invoice payment failed event routes to correct handler."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment_failure = AsyncMock()

        webhook_result = {
            "event_type": WebhookEventType.INVOICE_PAYMENT_FAILED.value,
            "user_id": "user-123",
            "subscription_id": "sub_test123",
            "attempt_count": 2,
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "invoice.payment_failed")
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(result["action"], "payment_failure_recorded")
        service._record_payment_failure.assert_called_once_with(
            "user-123", "sub_test123", 2
        )

    async def test_route_unhandled_event_type(self):
        """Unhandled event type returns not synced."""
        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "event_type": "some.unknown.event",
            "user_id": "user-123",
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertFalse(result["synced"])
        self.assertEqual(result["reason"], "unhandled_event_type")
        self.assertEqual(result["event_type"], "some.unknown.event")


class TestNoUserIdFallback(unittest.IsolatedAsyncioTestCase):
    """Tests for fallback behavior when user_id is not in metadata."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_no_user_id_returns_not_synced(self):
        """Missing user_id with no customer_id returns not synced."""
        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "event_type": WebhookEventType.SUBSCRIPTION_CREATED.value,
        }

        result = await service.sync_webhook_event(webhook_result)

        self.assertFalse(result["synced"])
        self.assertEqual(result["reason"], "no_user_id")

    async def test_lookup_user_from_supabase_customer_mapping(self):
        """User ID is looked up from Supabase customer mapping."""
        service = self.sync_module.SubscriptionSyncService()

        # Mock Supabase client with customer mapping
        mock_response = MagicMock()
        mock_response.data = [{"user_id": "user-from-db"}]

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        service._supabase_client = mock_client

        result = await service._get_user_id_from_customer("cus_test123")

        self.assertEqual(result, "user-from-db")
        mock_client.table.assert_called_once_with("stripe_customers")

    async def test_lookup_user_from_stripe_when_no_db_mapping(self):
        """User ID falls back to Stripe customer metadata when no DB mapping."""
        service = self.sync_module.SubscriptionSyncService()

        # Mock Supabase returning no results
        mock_response = MagicMock()
        mock_response.data = []

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        service._supabase_client = mock_client

        # Mock Stripe customer lookup
        mock_customer = {"metadata": {"user_id": "user-from-stripe"}}
        mock_stripe.Customer.retrieve.return_value = mock_customer
        mock_stripe.api_key = "test_key"

        result = await service._get_user_id_from_customer("cus_test123")

        self.assertEqual(result, "user-from-stripe")

    async def test_no_supabase_client_falls_back_to_stripe(self):
        """Without Supabase client, falls back to Stripe lookup."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = None

        mock_customer = {"metadata": {"user_id": "user-from-stripe"}}
        mock_stripe.Customer.retrieve.return_value = mock_customer
        mock_stripe.api_key = "test_key"

        result = await service._get_user_id_from_customer("cus_test123")

        self.assertEqual(result, "user-from-stripe")

    async def test_returns_none_when_lookup_fails(self):
        """Returns None when all lookup methods fail."""
        service = self.sync_module.SubscriptionSyncService()

        # Mock Supabase raising exception
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        service._supabase_client = mock_client

        # Mock Stripe also failing
        mock_stripe.Customer.retrieve.side_effect = Exception("Stripe error")
        mock_stripe.api_key = "test_key"

        result = await service._get_user_id_from_customer("cus_test123")

        self.assertIsNone(result)


class TestCheckoutCompletedHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_checkout_completed method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_stores_customer_mapping(self):
        """Handler stores customer mapping in database."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_customer_mapping = AsyncMock()

        webhook_result = {
            "customer_id": "cus_test123",
            "subscription_id": "sub_test123",
        }

        result = await service._handle_checkout_completed("user-123", webhook_result)

        service._store_customer_mapping.assert_called_once_with("user-123", "cus_test123")
        self.assertTrue(result["synced"])
        self.assertEqual(result["user_id"], "user-123")

    async def test_skips_mapping_without_customer_id(self):
        """Handler skips mapping storage when customer_id is missing."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_customer_mapping = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        result = await service._handle_checkout_completed("user-123", webhook_result)

        service._store_customer_mapping.assert_not_called()
        self.assertTrue(result["synced"])

    async def test_skips_mapping_without_supabase(self):
        """Handler skips mapping storage when Supabase not configured."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = None
        service._store_customer_mapping = AsyncMock()

        webhook_result = {
            "customer_id": "cus_test123",
            "subscription_id": "sub_test123",
        }

        result = await service._handle_checkout_completed("user-123", webhook_result)

        service._store_customer_mapping.assert_not_called()
        self.assertTrue(result["synced"])


class TestSubscriptionCreatedHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_subscription_created method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_sets_user_tier(self, mock_get_quota):
        """Handler sets user tier via quota service."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_subscription_mapping = AsyncMock()

        webhook_result = {
            "tier": "starter",
            "subscription_id": "sub_test123",
            "customer_id": "cus_test123",
        }

        result = await service._handle_subscription_created("user-123", webhook_result)

        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.STARTER
        )
        self.assertEqual(result["tier"], "starter")
        self.assertEqual(result["action"], "tier_activated")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_defaults_to_free_tier(self, mock_get_quota):
        """Handler defaults to free tier when not specified."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = None

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        result = await service._handle_subscription_created("user-123", webhook_result)

        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.FREE
        )
        self.assertEqual(result["tier"], "free")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_stores_subscription_mapping(self, mock_get_quota):
        """Handler stores subscription mapping when Supabase configured."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._store_subscription_mapping = AsyncMock()

        webhook_result = {
            "tier": "pro",
            "subscription_id": "sub_test123",
            "customer_id": "cus_test123",
        }

        await service._handle_subscription_created("user-123", webhook_result)

        service._store_subscription_mapping.assert_called_once_with(
            "user-123", "sub_test123", "cus_test123", "pro"
        )


class TestSubscriptionUpdatedHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_subscription_updated method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_updates_tier_for_active_subscription(self, mock_get_quota):
        """Handler updates tier for active subscriptions."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "tier": "business",
            "status": "active",
            "cancel_at_period_end": False,
        }

        result = await service._handle_subscription_updated("user-123", webhook_result)

        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.BUSINESS
        )
        self.assertEqual(result["tier"], "business")
        self.assertEqual(result["action"], "tier_updated")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_updates_tier_for_trialing_subscription(self, mock_get_quota):
        """Handler updates tier for trialing subscriptions."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "tier": "pro",
            "status": "trialing",
            "cancel_at_period_end": False,
        }

        result = await service._handle_subscription_updated("user-123", webhook_result)

        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.PRO
        )
        self.assertEqual(result["action"], "tier_updated")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_handles_cancellation_scheduled(self, mock_get_quota):
        """Handler notes when cancellation is scheduled."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "tier": "pro",
            "status": "active",
            "cancel_at_period_end": True,
        }

        result = await service._handle_subscription_updated("user-123", webhook_result)

        self.assertEqual(result["action"], "tier_updated_cancellation_scheduled")
        self.assertTrue(result["cancel_at_period_end"])

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_does_not_update_tier_for_past_due(self, mock_get_quota):
        """Handler does not update tier via quota service for past_due status."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()

        webhook_result = {
            "tier": "pro",
            "status": "past_due",
            "cancel_at_period_end": False,
        }

        result = await service._handle_subscription_updated("user-123", webhook_result)

        # Should not call set_user_tier for non-active status
        mock_quota_service.set_user_tier.assert_not_called()
        self.assertEqual(result["action"], "subscription_status_past_due")


class TestSubscriptionDeletedHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_subscription_deleted method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_downgrades_to_free(self, mock_get_quota):
        """Handler downgrades user to free tier."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._mark_subscription_cancelled = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        result = await service._handle_subscription_deleted("user-123", webhook_result)

        mock_quota_service.set_user_tier.assert_called_once_with(
            "user-123", SubscriptionTier.FREE
        )
        self.assertEqual(result["tier"], "free")
        self.assertEqual(result["action"], "downgraded_to_free")

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_marks_subscription_cancelled(self, mock_get_quota):
        """Handler marks subscription as cancelled in database."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._mark_subscription_cancelled = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        await service._handle_subscription_deleted("user-123", webhook_result)

        service._mark_subscription_cancelled.assert_called_once_with("sub_test123")


class TestInvoicePaidHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_invoice_paid method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_records_payment(self):
        """Handler records payment in database."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
            "amount_paid": 4900,
        }

        result = await service._handle_invoice_paid("user-123", webhook_result)

        service._record_payment.assert_called_once_with("user-123", "sub_test123", 4900)
        self.assertEqual(result["amount_paid"], 4900)
        self.assertEqual(result["action"], "payment_recorded")

    async def test_defaults_amount_to_zero(self):
        """Handler defaults amount_paid to zero when not provided."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        result = await service._handle_invoice_paid("user-123", webhook_result)

        service._record_payment.assert_called_once_with("user-123", "sub_test123", 0)
        self.assertEqual(result["amount_paid"], 0)


class TestInvoicePaymentFailedHandler(unittest.IsolatedAsyncioTestCase):
    """Tests for _handle_invoice_payment_failed method."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_records_payment_failure(self):
        """Handler records payment failure in database."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment_failure = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
            "attempt_count": 3,
        }

        result = await service._handle_invoice_payment_failed("user-123", webhook_result)

        service._record_payment_failure.assert_called_once_with(
            "user-123", "sub_test123", 3
        )
        self.assertEqual(result["attempt_count"], 3)
        self.assertEqual(result["action"], "payment_failure_recorded")

    async def test_defaults_attempt_count_to_one(self):
        """Handler defaults attempt_count to 1 when not provided."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = MagicMock()
        service._record_payment_failure = AsyncMock()

        webhook_result = {
            "subscription_id": "sub_test123",
        }

        result = await service._handle_invoice_payment_failed("user-123", webhook_result)

        service._record_payment_failure.assert_called_once_with(
            "user-123", "sub_test123", 1
        )
        self.assertEqual(result["attempt_count"], 1)


class TestDatabaseOperations(unittest.IsolatedAsyncioTestCase):
    """Tests for database storage operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_store_customer_mapping_upserts(self):
        """_store_customer_mapping uses upsert to handle existing mappings."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        service._supabase_client = mock_client

        await service._store_customer_mapping("user-123", "cus_test123")

        mock_client.table.assert_called_once_with("stripe_customers")
        call_args = mock_client.table.return_value.upsert.call_args
        self.assertEqual(call_args[0][0]["user_id"], "user-123")
        self.assertEqual(call_args[0][0]["customer_id"], "cus_test123")
        self.assertIn("updated_at", call_args[0][0])
        self.assertEqual(call_args[1]["on_conflict"], "user_id")

    async def test_store_customer_mapping_handles_error(self):
        """_store_customer_mapping handles database errors gracefully."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception("DB error")
        service._supabase_client = mock_client

        # Should not raise
        await service._store_customer_mapping("user-123", "cus_test123")

    async def test_store_customer_mapping_skips_without_client(self):
        """_store_customer_mapping does nothing without Supabase client."""
        service = self.sync_module.SubscriptionSyncService()
        service._supabase_client = None

        # Should not raise
        await service._store_customer_mapping("user-123", "cus_test123")

    async def test_store_subscription_mapping_upserts(self):
        """_store_subscription_mapping uses upsert for subscriptions."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        service._supabase_client = mock_client

        await service._store_subscription_mapping(
            "user-123", "sub_test123", "cus_test123", "pro"
        )

        mock_client.table.assert_called_once_with("stripe_subscriptions")
        call_args = mock_client.table.return_value.upsert.call_args
        self.assertEqual(call_args[0][0]["subscription_id"], "sub_test123")
        self.assertEqual(call_args[0][0]["user_id"], "user-123")
        self.assertEqual(call_args[0][0]["customer_id"], "cus_test123")
        self.assertEqual(call_args[0][0]["tier"], "pro")
        self.assertEqual(call_args[0][0]["status"], "active")
        self.assertEqual(call_args[1]["on_conflict"], "subscription_id")

    async def test_mark_subscription_cancelled_updates_status(self):
        """_mark_subscription_cancelled updates subscription status."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        service._supabase_client = mock_client

        await service._mark_subscription_cancelled("sub_test123")

        mock_client.table.assert_called_once_with("stripe_subscriptions")
        call_args = mock_client.table.return_value.update.call_args
        self.assertEqual(call_args[0][0]["status"], "cancelled")
        self.assertIn("cancelled_at", call_args[0][0])
        self.assertIn("updated_at", call_args[0][0])

    async def test_record_payment_inserts_payment(self):
        """_record_payment inserts payment record."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        service._supabase_client = mock_client

        await service._record_payment("user-123", "sub_test123", 4900)

        mock_client.table.assert_called_once_with("payments")
        call_args = mock_client.table.return_value.insert.call_args
        self.assertEqual(call_args[0][0]["user_id"], "user-123")
        self.assertEqual(call_args[0][0]["subscription_id"], "sub_test123")
        self.assertEqual(call_args[0][0]["amount_cents"], 4900)
        self.assertEqual(call_args[0][0]["status"], "paid")
        self.assertIn("paid_at", call_args[0][0])

    async def test_record_payment_failure_inserts_failure(self):
        """_record_payment_failure inserts failure record."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        service._supabase_client = mock_client

        await service._record_payment_failure("user-123", "sub_test123", 2)

        mock_client.table.assert_called_once_with("payment_failures")
        call_args = mock_client.table.return_value.insert.call_args
        self.assertEqual(call_args[0][0]["user_id"], "user-123")
        self.assertEqual(call_args[0][0]["subscription_id"], "sub_test123")
        self.assertEqual(call_args[0][0]["attempt_count"], 2)
        self.assertIn("failed_at", call_args[0][0])


class TestDatabaseUnavailable(unittest.IsolatedAsyncioTestCase):
    """Tests for error handling when database is unavailable."""

    def setUp(self):
        """Set up test fixtures."""
        self.sync_module = get_sync_module()

    async def test_store_customer_mapping_logs_error(self):
        """Database error during customer mapping storage is logged."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception("Connection failed")
        service._supabase_client = mock_client

        with patch.object(self.sync_module, "logger") as mock_logger:
            await service._store_customer_mapping("user-123", "cus_test123")
            mock_logger.error.assert_called_once()
            self.assertIn("Failed to store customer mapping", mock_logger.error.call_args[0][0])

    async def test_store_subscription_mapping_logs_error(self):
        """Database error during subscription mapping storage is logged."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception("Connection failed")
        service._supabase_client = mock_client

        with patch.object(self.sync_module, "logger") as mock_logger:
            await service._store_subscription_mapping("user-123", "sub_test", "cus_test", "pro")
            mock_logger.error.assert_called_once()
            self.assertIn("Failed to store subscription mapping", mock_logger.error.call_args[0][0])

    async def test_mark_subscription_cancelled_logs_error(self):
        """Database error during subscription cancellation is logged."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Connection failed")
        service._supabase_client = mock_client

        with patch.object(self.sync_module, "logger") as mock_logger:
            await service._mark_subscription_cancelled("sub_test123")
            mock_logger.error.assert_called_once()
            self.assertIn("Failed to mark subscription cancelled", mock_logger.error.call_args[0][0])

    async def test_record_payment_logs_error(self):
        """Database error during payment recording is logged."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Connection failed")
        service._supabase_client = mock_client

        with patch.object(self.sync_module, "logger") as mock_logger:
            await service._record_payment("user-123", "sub_test123", 4900)
            mock_logger.error.assert_called_once()
            self.assertIn("Failed to record payment", mock_logger.error.call_args[0][0])

    async def test_record_payment_failure_logs_error(self):
        """Database error during payment failure recording is logged."""
        service = self.sync_module.SubscriptionSyncService()

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Connection failed")
        service._supabase_client = mock_client

        with patch.object(self.sync_module, "logger") as mock_logger:
            await service._record_payment_failure("user-123", "sub_test123", 2)
            mock_logger.error.assert_called_once()
            self.assertIn("Failed to record payment failure", mock_logger.error.call_args[0][0])


class TestSingletonAndConvenienceFunctions(unittest.IsolatedAsyncioTestCase):
    """Tests for singleton pattern and convenience functions."""

    def setUp(self):
        """Reset singleton before each test."""
        self.sync_module = get_sync_module()

    def test_get_sync_service_returns_singleton(self):
        """get_sync_service returns the same instance on subsequent calls."""
        service1 = self.sync_module.get_sync_service()
        service2 = self.sync_module.get_sync_service()

        self.assertIs(service1, service2)

    @patch("src.payments.subscription_sync.get_quota_service")
    async def test_sync_webhook_event_convenience_function(self, mock_get_quota):
        """sync_webhook_event convenience function delegates to service."""
        mock_quota_service = AsyncMock()
        mock_get_quota.return_value = mock_quota_service

        webhook_result = {
            "event_type": WebhookEventType.SUBSCRIPTION_DELETED.value,
            "user_id": "user-123",
        }

        result = await self.sync_module.sync_webhook_event(webhook_result)

        self.assertTrue(result["synced"])
        self.assertEqual(result["event_type"], "customer.subscription.deleted")


if __name__ == "__main__":
    unittest.main()
