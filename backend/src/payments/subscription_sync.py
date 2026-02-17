"""
Subscription sync service for synchronizing Stripe webhook events to Postgres.

This module bridges Stripe payment events to database state:
- Checkout completed -> Activate subscription tier (resolve from Stripe if needed)
- Subscription created -> Set tier based on price
- Subscription updated -> Update tier based on price change, downgrade on inactive
- Subscription deleted -> Downgrade to free tier
- Invoice payment failed -> Flag account with grace period

IMPORTANT: All sync operations are idempotent. Duplicate Stripe events
(same event_id delivered multiple times) are detected and skipped.
"""

import logging
from typing import Optional

from src.types.payments import WebhookEventType
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
    All operations are idempotent -- duplicate event IDs are safely skipped.
    """

    def __init__(self):
        """Initialize the sync service."""
        self._use_db = is_database_configured()
        if self._use_db:
            logger.info("Subscription sync service initialized with Postgres")
        else:
            logger.info("DATABASE_URL not configured - subscription sync will be limited")

    async def _is_event_already_processed(self, event_id: str) -> bool:
        """
        Check if a Stripe event has already been processed (idempotency guard).

        Returns True if the event_id exists in the webhook event log.
        """
        if not self._use_db or not event_id:
            return False

        try:
            row = await db_fetchrow(
                "SELECT 1 FROM stripe_webhook_events WHERE event_id = $1 LIMIT 1",
                event_id,
            )
            return row is not None
        except Exception as e:
            logger.debug(f"Could not check event idempotency: {e}")
            return False

    async def _record_processed_event(
        self,
        event_id: str,
        event_type: str,
        user_id: Optional[str],
        customer_id: Optional[str],
        subscription_id: Optional[str],
        sync_result: dict,
    ) -> None:
        """
        Record a processed webhook event for idempotency and auditing.
        """
        if not self._use_db or not event_id:
            return

        try:
            import json

            await db_execute(
                """
                INSERT INTO stripe_webhook_events (
                    event_id, event_type, user_id, customer_id,
                    subscription_id, sync_result, processed_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                ON CONFLICT (event_id) DO NOTHING
                """,
                event_id,
                event_type,
                user_id,
                customer_id,
                subscription_id,
                json.dumps(sync_result),
            )
        except Exception as e:
            # Non-fatal: idempotency is best-effort, don't fail the webhook
            logger.warning(f"Failed to record webhook event {event_id}: {e}")

    async def sync_webhook_event(self, webhook_result: dict) -> dict:
        """
        Sync a Stripe webhook event to the database.

        Args:
            webhook_result: Result dict from stripe_service.handle_webhook()

        Returns:
            Dict with sync status and details.
        """
        event_type = webhook_result.get("event_type")
        event_id = webhook_result.get("event_id")
        user_id = webhook_result.get("user_id")

        # Idempotency check: skip if we already processed this event
        if event_id and await self._is_event_already_processed(event_id):
            logger.info(
                f"Skipping duplicate webhook event {event_id} ({event_type})"
            )
            return {
                "synced": False,
                "reason": "duplicate_event",
                "event_type": event_type,
                "event_id": event_id,
            }

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
                result = {
                    "synced": False,
                    "reason": "no_user_id",
                    "event_type": event_type,
                }
                # Still record the event so we don't retry it indefinitely
                await self._record_processed_event(
                    event_id, event_type, None,
                    webhook_result.get("customer_id"),
                    webhook_result.get("subscription_id"),
                    result,
                )
                return result

        # Route to appropriate handler
        if event_type == WebhookEventType.CHECKOUT_COMPLETED.value:
            sync_result = await self._handle_checkout_completed(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_CREATED.value:
            sync_result = await self._handle_subscription_created(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_UPDATED.value:
            sync_result = await self._handle_subscription_updated(user_id, webhook_result)

        elif event_type == WebhookEventType.SUBSCRIPTION_DELETED.value:
            sync_result = await self._handle_subscription_deleted(user_id, webhook_result)

        elif event_type == WebhookEventType.INVOICE_PAID.value:
            sync_result = await self._handle_invoice_paid(user_id, webhook_result)

        elif event_type == WebhookEventType.INVOICE_PAYMENT_FAILED.value:
            sync_result = await self._handle_invoice_payment_failed(user_id, webhook_result)

        else:
            logger.debug(f"Unhandled webhook event type: {event_type}")
            sync_result = {
                "synced": False,
                "reason": "unhandled_event_type",
                "event_type": event_type,
            }

        # Record the event for idempotency and auditing
        await self._record_processed_event(
            event_id, event_type, user_id,
            webhook_result.get("customer_id"),
            webhook_result.get("subscription_id"),
            sync_result,
        )

        return sync_result

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

    async def _resolve_tier_from_subscription(self, subscription_id: str) -> Optional[str]:
        """
        Resolve the subscription tier by fetching the subscription from Stripe.

        Used when checkout.session.completed fires before subscription.created
        and we need to determine the tier from the subscription's price ID.
        """
        try:
            import stripe
            from src.payments.stripe_service import stripe_service

            if not stripe.api_key:
                return None

            import asyncio
            subscription = await asyncio.to_thread(
                stripe.Subscription.retrieve, subscription_id
            )
            if subscription and subscription.get("items", {}).get("data"):
                price_id = subscription["items"]["data"][0]["price"]["id"]
                tier = stripe_service.get_tier_for_price_id(price_id)
                return tier.value
        except Exception as e:
            logger.warning(f"Could not resolve tier from subscription {subscription_id}: {e}")

        return None

    async def _handle_checkout_completed(self, user_id: str, webhook_result: dict) -> dict:
        """
        Handle checkout.session.completed event.

        This fires when a user completes the Stripe checkout flow. We must:
        1. Store the customer mapping for future lookups.
        2. Resolve and activate the subscription tier. This is critical because
           checkout.session.completed may arrive before subscription.created,
           and we cannot leave the user on the free tier after they have paid.
        """
        customer_id = webhook_result.get("customer_id")
        subscription_id = webhook_result.get("subscription_id")

        # Store customer mapping for future lookups
        if customer_id and self._use_db:
            await self._store_customer_mapping(user_id, customer_id)

        # Resolve the tier from the subscription and activate it.
        # This ensures the user gets upgraded even if subscription.created
        # arrives later or is lost.
        tier_value = None
        if subscription_id:
            tier_value = await self._resolve_tier_from_subscription(subscription_id)

        if tier_value and tier_value != "free":
            new_tier = _map_payments_tier_to_usage_tier(tier_value)
            quota_service = get_quota_service()
            await quota_service.set_user_tier(user_id, new_tier)

            # Also store/update subscription mapping
            if subscription_id and self._use_db:
                await self._store_subscription_mapping(
                    user_id, subscription_id, customer_id, new_tier.value
                )

            logger.info(
                f"Checkout completed for user {user_id[:8]}... - "
                f"tier activated: {new_tier.value} "
                f"(customer: {customer_id}, subscription: {subscription_id})"
            )

            return {
                "synced": True,
                "event_type": "checkout.session.completed",
                "user_id": user_id,
                "tier": new_tier.value,
                "action": "tier_activated_from_checkout",
            }

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
        CRITICAL: When the subscription is no longer active, downgrade to free.
        This prevents users from keeping Pro access after cancellation takes effect.
        """
        tier_value = webhook_result.get("tier", "free")
        status = webhook_result.get("status")
        cancel_at_period_end = webhook_result.get("cancel_at_period_end", False)

        quota_service = get_quota_service()

        if status in ("active", "trialing"):
            # Subscription is active -- sync the tier from the price
            new_tier = _map_payments_tier_to_usage_tier(tier_value)
            await quota_service.set_user_tier(user_id, new_tier)

            action = "tier_updated"
            if cancel_at_period_end:
                action = "tier_updated_cancellation_scheduled"
                logger.info(
                    f"Subscription will cancel at period end for user {user_id[:8]}..."
                )
        elif status == "past_due":
            # Payment failed but Stripe is still retrying.
            # Keep current tier but flag the account for grace period.
            new_tier = _map_payments_tier_to_usage_tier(tier_value)
            # Do NOT downgrade yet -- Stripe will send subscription.deleted
            # if all retries fail. But flag the subscription.
            if self._use_db:
                subscription_id = webhook_result.get("subscription_id")
                if subscription_id:
                    await self._update_subscription_payment_status(
                        subscription_id, "grace_period"
                    )
            action = "grace_period_started"
            logger.warning(
                f"Subscription past_due for user {user_id[:8]}... - grace period active"
            )
        else:
            # Subscription is no longer active (canceled, incomplete_expired, unpaid, etc.)
            # CRITICAL FIX: Downgrade to free tier immediately.
            new_tier = UsageTier.FREE
            await quota_service.set_user_tier(user_id, new_tier)
            action = f"downgraded_to_free_status_{status}"
            logger.info(
                f"Subscription status changed to '{status}' for user {user_id[:8]}... "
                f"- downgraded to FREE"
            )

        # Update subscription record in database
        subscription_id = webhook_result.get("subscription_id")
        if subscription_id and self._use_db:
            await self._update_subscription_record(
                subscription_id, new_tier.value, status, cancel_at_period_end
            )

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

        Downgrade user to free tier. This is the definitive signal that the
        subscription has ended (after all retry attempts or immediate cancellation).
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

        Confirms payment was successful. Clear any grace period flags and
        ensure the user's tier is correct.
        """
        amount_paid = webhook_result.get("amount_paid", 0)
        subscription_id = webhook_result.get("subscription_id")

        # Clear grace period flag if subscription had one
        if subscription_id and self._use_db:
            await self._update_subscription_payment_status(subscription_id, "current")

        # Log payment for analytics
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

        Log the failure and flag the account. Do NOT immediately downgrade --
        Stripe will retry and send subscription.updated (past_due) or
        subscription.deleted if all retries fail.
        """
        attempt_count = webhook_result.get("attempt_count", 1)
        subscription_id = webhook_result.get("subscription_id")

        logger.warning(
            f"Invoice payment failed for user {user_id[:8]}... "
            f"(attempt {attempt_count}, subscription: {subscription_id})"
        )

        # Flag the subscription for grace period tracking
        if subscription_id and self._use_db:
            await self._update_subscription_payment_status(
                subscription_id, "payment_failed"
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
                    payment_status,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, 'active', 'current', NOW(), NOW())
                ON CONFLICT (subscription_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    customer_id = EXCLUDED.customer_id,
                    tier = EXCLUDED.tier,
                    status = EXCLUDED.status,
                    payment_status = EXCLUDED.payment_status,
                    updated_at = NOW()
                """,
                subscription_id,
                user_id,
                customer_id,
                tier,
            )
        except Exception as e:
            logger.error(f"Failed to store subscription mapping: {e}")

    async def _update_subscription_record(
        self,
        subscription_id: str,
        tier: str,
        status: Optional[str],
        cancel_at_period_end: bool,
    ) -> None:
        """Update subscription record with latest state from Stripe."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                UPDATE stripe_subscriptions
                SET tier = $2,
                    status = $3,
                    cancel_at_period_end = $4,
                    updated_at = NOW()
                WHERE subscription_id = $1
                """,
                subscription_id,
                tier,
                status or "unknown",
                cancel_at_period_end,
            )
        except Exception as e:
            logger.error(f"Failed to update subscription record: {e}")

    async def _update_subscription_payment_status(
        self,
        subscription_id: str,
        payment_status: str,
    ) -> None:
        """Update the payment_status flag on a subscription."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                UPDATE stripe_subscriptions
                SET payment_status = $2,
                    updated_at = NOW()
                WHERE subscription_id = $1
                """,
                subscription_id,
                payment_status,
            )
        except Exception as e:
            logger.error(f"Failed to update subscription payment status: {e}")

    async def _mark_subscription_cancelled(self, subscription_id: str) -> None:
        """Mark a subscription as cancelled in the database."""
        if not self._use_db:
            return

        try:
            await db_execute(
                """
                UPDATE stripe_subscriptions
                SET status = 'cancelled',
                    payment_status = 'current',
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
