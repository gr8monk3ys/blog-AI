"""
Subscription sync service for synchronizing Stripe webhook events to Postgres.

This module bridges Stripe payment events to database state:
- Checkout completed → Activate subscription tier
- Subscription updated → Update tier based on price change
- Subscription deleted → Downgrade to free tier
- Invoice payment failed → Log warning (don't immediately downgrade)
"""

import logging
from datetime import datetime
from typing import Optional

from src.types.payments import SubscriptionTier as PaymentsTier, WebhookEventType
from src.types.usage import SubscriptionTier as UsageTier
from src.usage.quota_service import get_quota_service
from src.db import execute as db_execute, fetchrow as db_fetchrow, is_database_configured

logger = logging.getLogger(__name__)


def _map_payments_tier_to_usage_tier(tier_value: str) -> UsageTier:
    """
    Map a tier string value to the usage SubscriptionTier enum.

    Both enums have identical values, but are separate types.
    """
    try:
        return UsageTier(tier_value)
    except ValueError:
        logger.warning(f"Unknown tier value '{tier_value}', defaulting to FREE")
        return UsageTier.FREE


class SubscriptionSyncService:
    """
    Service for syncing Stripe subscription events to the database.

    Handles all webhook events that affect user subscription state.
    """

    def __init__(self):
        """Initialize the sync service."""
        self._use_db = is_database_configured()
        if self._use_db:
            logger.info("Subscription sync service initialized with Postgres")
        else:
            logger.info("DATABASE_URL not configured - subscription sync will be limited")

    async def sync_webhook_event(self, webhook_result: dict) -> dict:
        """
        Sync a Stripe webhook event to the database.

        Args:
            webhook_result: Result dict from stripe_service.handle_webhook()

        Returns:
            Dict with sync status and details.
        """
        event_type = webhook_result.get("event_type")
        user_id = webhook_result.get("user_id")

        if not user_id:
            # Try to look up user_id from customer_id if not in metadata
            customer_id = webhook_result.get("customer_id")
            if customer_id:
                user_id = await self._get_user_id_from_customer(customer_id)

            if not user_id:
                logger.warning(
                    f"Cannot sync webhook {event_type}: no user_id found "
                    f"(customer_id: {webhook_result.get('customer_id')})"
                )
                return {
                    "synced": False,
                    "reason": "no_user_id",
                    "event_type": event_type,
                }

        # Route to appropriate handler
        if event_type == WebhookEventType.CHECKOUT_COMPLETED.value:
            return await self._handle_checkout_completed(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_CREATED.value:
            return await self._handle_subscription_created(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_UPDATED.value:
            return await self._handle_subscription_updated(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_DELETED.value:
            return await self._handle_subscription_deleted(user_id, webhook_result)

        elif event_type == WebhookEventType.INVOICE_PAID.value:
            return await self._handle_invoice_paid(user_id, webhook_result)

        elif event_type == WebhookEventType.INVOICE_PAYMENT_FAILED.value:
            return await self._handle_invoice_payment_failed(user_id, webhook_result)

        else:
            logger.debug(f"Unhandled webhook event type: {event_type}")
            return {
                "synced": False,
                "reason": "unhandled_event_type",
                "event_type": event_type,
            }

    async def _get_user_id_from_customer(self, customer_id: str) -> Optional[str]:
        """
        Look up user_id from Stripe customer_id.

        First checks local mapping, then queries Stripe API if available.
        """
        if self._use_db:
            try:
                row = await db_fetchrow(
                    "SELECT user_id FROM stripe_customers WHERE customer_id = $1 LIMIT 1",
                    customer_id,
                )
                if row:
                    return str(row["user_id"])
            except Exception as e:
                logger.debug(f"Could not lookup customer mapping: {e}")

        # Fallback: query Stripe customer metadata
        try:
            import stripe
            if stripe.api_key:
                customer = stripe.Customer.retrieve(customer_id)
                return customer.get("metadata", {}).get("user_id")
        except Exception as e:
            logger.debug(f"Could not retrieve customer from Stripe: {e}")

        return None

    async def _handle_checkout_completed(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle checkout.session.completed event.

        This is triggered when a user completes the Stripe checkout flow.
        The subscription tier should already be set by subscription.created,
        but we record the customer mapping here.
        """
        customer_id = webhook_result.get("customer_id")
        subscription_id = webhook_result.get("subscription_id")

        # Store customer mapping for future lookups
        if customer_id and self._use_db:
            await self._store_customer_mapping(user_id, customer_id)

        logger.info(
            f"Checkout completed for user {user_id[:8]}... "
            f"(customer: {customer_id}, subscription: {subscription_id})"
        )

        return {
            "synced": True,
            "event_type": "checkout.session.completed",
            "user_id": user_id,
            "action": "customer_mapping_stored",
        }

    async def _handle_subscription_created(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle customer.subscription.created event.

        Set the user's tier based on the new subscription.
        """
        tier_value = webhook_result.get("tier", "free")
        new_tier = _map_payments_tier_to_usage_tier(tier_value)

        # Update user tier in quota service (which handles Supabase)
        quota_service = get_quota_service()
        await quota_service.set_user_tier(user_id, new_tier)

        # Store subscription mapping
        subscription_id = webhook_result.get("subscription_id")
        customer_id = webhook_result.get("customer_id")
        if subscription_id and self._use_db:
            await self._store_subscription_mapping(
                user_id, subscription_id, customer_id, new_tier.value
            )

        logger.info(
            f"Subscription created for user {user_id[:8]}...: {new_tier.value}"
        )

        return {
            "synced": True,
            "event_type": "customer.subscription.created",
            "user_id": user_id,
            "tier": new_tier.value,
            "action": "tier_activated",
        }

    async def _handle_subscription_updated(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle customer.subscription.updated event.

        Update tier if price changed, handle cancellation scheduling.
        """
        tier_value = webhook_result.get("tier", "free")
        status = webhook_result.get("status")
        cancel_at_period_end = webhook_result.get("cancel_at_period_end", False)

        # Only update tier if subscription is active
        if status in ["active", "trialing"]:
            new_tier = _map_payments_tier_to_usage_tier(tier_value)
            quota_service = get_quota_service()
            await quota_service.set_user_tier(user_id, new_tier)

            action = "tier_updated"
            if cancel_at_period_end:
                action = "tier_updated_cancellation_scheduled"
                logger.info(
                    f"Subscription will cancel at period end for user {user_id[:8]}..."
                )
        else:
            new_tier = _map_payments_tier_to_usage_tier(tier_value)
            action = f"subscription_status_{status}"

        logger.info(
            f"Subscription updated for user {user_id[:8]}...: "
            f"tier={new_tier.value}, status={status}"
        )

        return {
            "synced": True,
            "event_type": "customer.subscription.updated",
            "user_id": user_id,
            "tier": new_tier.value,
            "status": status,
            "cancel_at_period_end": cancel_at_period_end,
            "action": action,
        }

    async def _handle_subscription_deleted(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle customer.subscription.deleted event.

        Downgrade user to free tier.
        """
        quota_service = get_quota_service()
        await quota_service.set_user_tier(user_id, UsageTier.FREE)

        # Update subscription mapping if we have one
        subscription_id = webhook_result.get("subscription_id")
        if subscription_id and self._use_db:
            await self._mark_subscription_cancelled(subscription_id)

        logger.info(f"Subscription deleted for user {user_id[:8]}... - downgraded to FREE")

        return {
            "synced": True,
            "event_type": "customer.subscription.deleted",
            "user_id": user_id,
            "tier": UsageTier.FREE.value,
            "action": "downgraded_to_free",
        }

    async def _handle_invoice_paid(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle invoice.paid event.

        This confirms payment was successful. Useful for tracking payments
        but doesn't change subscription state (that's handled by subscription events).
        """
        amount_paid = webhook_result.get("amount_paid", 0)
        subscription_id = webhook_result.get("subscription_id")

        # Log payment for analytics (could store in a payments table)
        if self._use_db:
            await self._record_payment(
                user_id,
                subscription_id,
                amount_paid,
            )

        logger.info(
            f"Invoice paid for user {user_id[:8]}...: "
            f"${amount_paid / 100:.2f}"
        )

        return {
            "synced": True,
            "event_type": "invoice.paid",
            "user_id": user_id,
            "amount_paid": amount_paid,
            "action": "payment_recorded",
        }

    async def _handle_invoice_payment_failed(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle invoice.payment_failed event.

        Log the failure but don't immediately downgrade - Stripe will retry
        and send subscription.deleted if all retries fail.
        """
        attempt_count = webhook_result.get("attempt_count", 1)
        subscription_id = webhook_result.get("subscription_id")

        # Log the failure (could trigger notification to user)
        logger.warning(
            f"Invoice payment failed for user {user_id[:8]}... "
            f"(attempt {attempt_count})"
        )

        # Record payment failure for tracking
        if self._use_db:
            await self._record_payment_failure(
                user_id,
                subscription_id,
                attempt_count,
            )

        return {
            "synced": True,
            "event_type": "invoice.payment_failed",
            "user_id": user_id,
            "attempt_count": attempt_count,
            "action": "payment_failure_recorded",
        }

    async def _store_customer_mapping(self, user_id: str, customer_id: str) -> None:
        """Store mapping between user_id and Stripe customer_id."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                INSERT INTO stripe_customers (user_id, customer_id, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    customer_id = EXCLUDED.customer_id,
                    updated_at = NOW()
                """,
                user_id,
                customer_id,
            )
        except Exception as e:
            logger.error(f"Failed to store customer mapping: {e}")

    async def _store_subscription_mapping(
        self,
        user_id: str,
        subscription_id: str,
        customer_id: Optional[str],
        tier: str,
    ) -> None:
        """Store subscription details for tracking."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                INSERT INTO stripe_subscriptions (
                    subscription_id,
                    user_id,
                    customer_id,
                    tier,
                    status,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, 'active', NOW(), NOW())
                ON CONFLICT (subscription_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    customer_id = EXCLUDED.customer_id,
                    tier = EXCLUDED.tier,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """,
                subscription_id,
                user_id,
                customer_id,
                tier,
            )
        except Exception as e:
            logger.error(f"Failed to store subscription mapping: {e}")

    async def _mark_subscription_cancelled(self, subscription_id: str) -> None:
        """Mark a subscription as cancelled in the database."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                UPDATE stripe_subscriptions
                SET status = 'cancelled',
                    cancelled_at = NOW(),
                    updated_at = NOW()
                WHERE subscription_id = $1
                """,
                subscription_id,
            )
        except Exception as e:
            logger.error(f"Failed to mark subscription cancelled: {e}")

    async def _record_payment(
        self,
        user_id: str,
        subscription_id: Optional[str],
        amount_cents: int,
    ) -> None:
        """Record a successful payment."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                INSERT INTO payments (
                    user_id,
                    subscription_id,
                    amount_cents,
                    status,
                    paid_at,
                    created_at
                ) VALUES ($1, $2, $3, 'paid', NOW(), NOW())
                """,
                user_id,
                subscription_id,
                int(amount_cents or 0),
            )
        except Exception as e:
            logger.error(f"Failed to record payment: {e}")

    async def _record_payment_failure(
        self,
        user_id: str,
        subscription_id: Optional[str],
        attempt_count: int,
    ) -> None:
        """Record a payment failure for tracking."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                INSERT INTO payment_failures (
                    user_id,
                    subscription_id,
                    attempt_count,
                    failed_at,
                    created_at
                ) VALUES ($1, $2, $3, NOW(), NOW())
                """,
                user_id,
                subscription_id,
                int(attempt_count or 1),
            )
        except Exception as e:
            logger.error(f"Failed to record payment failure: {e}")


# Singleton instance
_sync_service: Optional[SubscriptionSyncService] = None


def get_sync_service() -> SubscriptionSyncService:
    """Get the singleton subscription sync service instance."""
    global _sync_service
    if _sync_service is None:
        _sync_service = SubscriptionSyncService()
    return _sync_service


async def sync_webhook_event(webhook_result: dict) -> dict:
    """Sync a Stripe webhook event to the database."""
    return await get_sync_service().sync_webhook_event(webhook_result)
