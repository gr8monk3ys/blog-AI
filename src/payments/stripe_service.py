"""
Stripe payment service for subscription management.

This module provides functions for:
- Creating checkout sessions for new subscriptions
- Managing customer portal sessions
- Handling Stripe webhooks
- Querying subscription status
"""

import asyncio
import logging
import os
from functools import partial
from typing import Optional

import stripe
from stripe import Webhook
from stripe.error import SignatureVerificationError, StripeError

from src.types.payments import (
    PRICING_TIERS,
    SubscriptionStatus,
    SubscriptionTier,
    WebhookEventType,
    get_tier_generation_limit,
)

logger = logging.getLogger(__name__)


class StripeService:
    """
    Service class for Stripe payment operations.

    Handles subscription management, checkout sessions, and webhook processing.
    """

    def __init__(self) -> None:
        """Initialize Stripe with API key from environment."""
        self._api_key = os.environ.get("STRIPE_SECRET_KEY")
        self._webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        self._price_ids = {
            SubscriptionTier.STARTER: os.environ.get("STRIPE_PRICE_ID_STARTER"),
            SubscriptionTier.PRO: os.environ.get("STRIPE_PRICE_ID_PRO"),
            SubscriptionTier.BUSINESS: os.environ.get("STRIPE_PRICE_ID_BUSINESS"),
        }

        if self._api_key:
            stripe.api_key = self._api_key
            logger.info("Stripe initialized successfully")
        else:
            logger.warning("STRIPE_SECRET_KEY not configured - payment features disabled")

    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self._api_key)

    def _ensure_configured(self) -> None:
        """Raise an error if Stripe is not configured."""
        if not self.is_configured:
            raise ValueError(
                "Stripe is not configured. Set STRIPE_SECRET_KEY environment variable."
            )

    def get_price_id_for_tier(self, tier: SubscriptionTier) -> Optional[str]:
        """Get the Stripe price ID for a subscription tier."""
        return self._price_ids.get(tier)

    def get_tier_for_price_id(self, price_id: str) -> SubscriptionTier:
        """Get the subscription tier for a Stripe price ID."""
        for tier, pid in self._price_ids.items():
            if pid == price_id:
                return tier
        return SubscriptionTier.FREE

    async def get_or_create_customer(
        self,
        user_id: str,
        email: Optional[str] = None,
    ) -> str:
        """
        Get existing Stripe customer or create a new one.

        Args:
            user_id: Internal user identifier
            email: User's email address (optional)

        Returns:
            Stripe customer ID
        """
        self._ensure_configured()

        # Search for existing customer by metadata (run sync Stripe call in thread pool)
        try:
            customers = await asyncio.to_thread(
                stripe.Customer.search,
                query=f'metadata["user_id"]:"{user_id}"',
            )
            if customers.data:
                return customers.data[0].id
        except StripeError as e:
            logger.warning(f"Error searching for customer: {e}")

        # Create new customer (run sync Stripe call in thread pool)
        try:
            customer = await asyncio.to_thread(
                partial(
                    stripe.Customer.create,
                    email=email,
                    metadata={"user_id": user_id},
                )
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
        except StripeError as e:
            logger.error(f"Error creating customer: {e}")
            raise

    async def create_checkout_session(
        self,
        price_id: str,
        user_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> dict:
        """
        Create a Stripe checkout session for subscription.

        Args:
            price_id: Stripe price ID for the subscription
            user_id: Internal user identifier
            success_url: URL to redirect on successful checkout
            cancel_url: URL to redirect on cancelled checkout
            customer_email: Optional customer email for prefill

        Returns:
            Dictionary with session_id and url
        """
        self._ensure_configured()

        try:
            # Get or create customer
            customer_id = await self.get_or_create_customer(user_id, customer_email)

            # Create checkout session (run sync Stripe call in thread pool)
            session = await asyncio.to_thread(
                partial(
                    stripe.checkout.Session.create,
                    customer=customer_id,
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price": price_id,
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        "user_id": user_id,
                    },
                    subscription_data={
                        "metadata": {
                            "user_id": user_id,
                        },
                    },
                    allow_promotion_codes=True,
                )
            )

            logger.info(
                f"Created checkout session {session.id} for user {user_id}"
            )

            return {
                "session_id": session.id,
                "url": session.url,
            }

        except StripeError as e:
            logger.error(f"Error creating checkout session: {e}")
            raise

    async def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """
        Create a Stripe customer portal session.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to redirect when exiting portal

        Returns:
            Portal session URL
        """
        self._ensure_configured()

        try:
            # Create portal session (run sync Stripe call in thread pool)
            session = await asyncio.to_thread(
                partial(
                    stripe.billing_portal.Session.create,
                    customer=customer_id,
                    return_url=return_url,
                )
            )

            logger.info(f"Created portal session for customer {customer_id}")
            return session.url

        except StripeError as e:
            logger.error(f"Error creating portal session: {e}")
            raise

    async def get_subscription_status(
        self,
        customer_id: str,
    ) -> SubscriptionStatus:
        """
        Get the current subscription status for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            SubscriptionStatus with current tier and details
        """
        self._ensure_configured()

        try:
            # List subscriptions (run sync Stripe call in thread pool)
            subscriptions = await asyncio.to_thread(
                partial(
                    stripe.Subscription.list,
                    customer=customer_id,
                    status="all",
                    limit=1,
                )
            )

            if not subscriptions.data:
                return SubscriptionStatus(
                    has_subscription=False,
                    tier=SubscriptionTier.FREE,
                    customer_id=customer_id,
                    generations_limit=get_tier_generation_limit(SubscriptionTier.FREE),
                )

            subscription = subscriptions.data[0]
            price_id = subscription["items"]["data"][0]["price"]["id"]
            tier = self.get_tier_for_price_id(price_id)

            # Check if subscription is in an active state
            active_statuses = ["active", "trialing"]
            is_active = subscription.status in active_statuses

            return SubscriptionStatus(
                has_subscription=is_active,
                tier=tier if is_active else SubscriptionTier.FREE,
                status=subscription.status,
                current_period_end=subscription.current_period_end,
                cancel_at_period_end=subscription.cancel_at_period_end,
                customer_id=customer_id,
                generations_limit=get_tier_generation_limit(
                    tier if is_active else SubscriptionTier.FREE
                ),
            )

        except StripeError as e:
            logger.error(f"Error getting subscription status: {e}")
            raise

    async def get_customer_id_for_user(self, user_id: str) -> Optional[str]:
        """
        Get the Stripe customer ID for an internal user ID.

        Args:
            user_id: Internal user identifier

        Returns:
            Stripe customer ID or None if not found
        """
        self._ensure_configured()

        try:
            # Search for customer (run sync Stripe call in thread pool)
            customers = await asyncio.to_thread(
                stripe.Customer.search,
                query=f'metadata["user_id"]:"{user_id}"',
            )
            if customers.data:
                return customers.data[0].id
            return None
        except StripeError as e:
            logger.error(f"Error searching for customer: {e}")
            return None

    def handle_webhook(
        self,
        payload: bytes,
        sig_header: str,
    ) -> dict:
        """
        Handle incoming Stripe webhook events.

        Args:
            payload: Raw request body bytes
            sig_header: Stripe signature header value

        Returns:
            Dictionary with event type and relevant data
        """
        self._ensure_configured()

        if not self._webhook_secret:
            raise ValueError(
                "Webhook secret not configured. Set STRIPE_WEBHOOK_SECRET."
            )

        try:
            event = Webhook.construct_event(
                payload,
                sig_header,
                self._webhook_secret,
            )
        except SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid webhook signature")

        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Processing webhook event: {event_type}")

        result = {
            "event_type": event_type,
            "event_id": event["id"],
        }

        # Handle specific event types
        if event_type == WebhookEventType.CHECKOUT_COMPLETED.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["user_id"] = data.get("metadata", {}).get("user_id")
            logger.info(
                f"Checkout completed for user {result.get('user_id')}"
            )

        elif event_type == WebhookEventType.SUBSCRIPTION_CREATED.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("id")
            result["status"] = data.get("status")
            result["user_id"] = data.get("metadata", {}).get("user_id")
            price_id = data["items"]["data"][0]["price"]["id"]
            result["tier"] = self.get_tier_for_price_id(price_id).value
            logger.info(
                f"Subscription created for user {result.get('user_id')}: {result.get('tier')}"
            )

        elif event_type == WebhookEventType.SUBSCRIPTION_UPDATED.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("id")
            result["status"] = data.get("status")
            result["cancel_at_period_end"] = data.get("cancel_at_period_end")
            result["user_id"] = data.get("metadata", {}).get("user_id")
            price_id = data["items"]["data"][0]["price"]["id"]
            result["tier"] = self.get_tier_for_price_id(price_id).value
            logger.info(
                f"Subscription updated for user {result.get('user_id')}: {result.get('status')}"
            )

        elif event_type == WebhookEventType.SUBSCRIPTION_DELETED.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("id")
            result["user_id"] = data.get("metadata", {}).get("user_id")
            logger.info(
                f"Subscription deleted for user {result.get('user_id')}"
            )

        elif event_type == WebhookEventType.INVOICE_PAID.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["amount_paid"] = data.get("amount_paid")
            logger.info(
                f"Invoice paid for customer {result.get('customer_id')}"
            )

        elif event_type == WebhookEventType.INVOICE_PAYMENT_FAILED.value:
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["attempt_count"] = data.get("attempt_count")
            logger.warning(
                f"Invoice payment failed for customer {result.get('customer_id')}"
            )

        return result


# Global service instance
stripe_service = StripeService()


# Convenience functions that use the global instance
async def create_checkout_session(
    price_id: str,
    user_id: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None,
) -> dict:
    """Create a Stripe checkout session. See StripeService.create_checkout_session."""
    return await stripe_service.create_checkout_session(
        price_id, user_id, success_url, cancel_url, customer_email
    )


async def create_customer_portal_session(
    customer_id: str,
    return_url: str,
) -> str:
    """Create a customer portal session. See StripeService.create_customer_portal_session."""
    return await stripe_service.create_customer_portal_session(customer_id, return_url)


async def get_subscription_status(customer_id: str) -> SubscriptionStatus:
    """Get subscription status. See StripeService.get_subscription_status."""
    return await stripe_service.get_subscription_status(customer_id)


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Handle webhook event. See StripeService.handle_webhook."""
    return stripe_service.handle_webhook(payload, sig_header)
