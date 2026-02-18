"""
Payment and subscription management endpoints.

Provides API endpoints for:
- Creating Stripe checkout sessions
- Managing customer portal access
- Handling Stripe webhooks
- Querying subscription status
"""

import logging
import os
from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.payments import stripe_service
from src.payments.subscription_sync import sync_webhook_event
from src.types.payments import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PRICING_TIERS,
    PortalSessionRequest,
    PortalSessionResponse,
    SubscriptionStatus,
    SubscriptionTier,
    WebhookResponse,
)
from src.types.usage import SubscriptionTier as UsageSubscriptionTier, get_tier_config

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])

def _business_tier_enabled() -> bool:
    return os.environ.get("ENABLE_BUSINESS_TIER", "").strip().lower() in ("1", "true", "yes", "on")


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    responses={
        400: {"description": "Invalid request or Stripe not configured"},
        500: {"description": "Stripe API error"},
    },
)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_id: str = Depends(verify_api_key),
) -> CheckoutSessionResponse:
    """
    Create a Stripe checkout session for subscription purchase.

    The user will be redirected to Stripe's hosted checkout page.
    After completing (or cancelling) the checkout, they will be
    redirected to the provided success_url or cancel_url.

    Args:
        request: Checkout session parameters including price_id and URLs
        user_id: Authenticated user ID from API key

    Returns:
        CheckoutSessionResponse with session ID and checkout URL
    """
    if not stripe_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Payment processing is not configured",
                "success": False,
            },
        )

    # SECURITY: only allow checkout for configured plan price IDs.
    if not stripe_service.is_configured_price_id(request.price_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid price_id", "success": False},
        )

    tier = stripe_service.get_tier_for_price_id(request.price_id)
    if tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid price_id", "success": False},
        )

    # Don't sell the Business/Agency tier until team features exist.
    if tier == SubscriptionTier.BUSINESS and not _business_tier_enabled():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Business tier is not available", "success": False},
        )

    try:
        result = await stripe_service.create_checkout_session(
            price_id=request.price_id,
            user_id=user_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        logger.info(f"Checkout session created for user {user_id}")

        return CheckoutSessionResponse(
            success=True,
            session_id=result["session_id"],
            url=result["url"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": sanitize_error_message(str(e)), "success": False},
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create checkout session", "success": False},
        )


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    responses={
        400: {"description": "Invalid webhook signature or payload"},
    },
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
) -> WebhookResponse:
    """
    Handle incoming Stripe webhook events.

    This endpoint receives events from Stripe for subscription lifecycle
    changes, payment successes/failures, and other billing events.

    Note: This endpoint does not require API key authentication as it
    is called directly by Stripe. Security is ensured via webhook
    signature verification.

    Args:
        request: Raw request containing webhook payload
        stripe_signature: Stripe signature header for verification

    Returns:
        WebhookResponse confirming successful processing
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Missing Stripe-Signature header", "success": False},
        )

    try:
        payload = await request.body()
        result = stripe_service.handle_webhook(payload, stripe_signature)

        logger.info(
            f"Webhook processed: {result.get('event_type')} "
            f"(event_id: {result.get('event_id')})"
        )

        # Sync webhook event to database (update subscription tiers, etc.)
        sync_result = await sync_webhook_event(result)

        if sync_result.get("synced"):
            logger.info(
                f"Webhook synced to database: {sync_result.get('action')} "
                f"(user: {sync_result.get('user_id', 'unknown')[:8]}...)"
            )
        else:
            logger.debug(
                f"Webhook not synced: {sync_result.get('reason')} "
                f"({result.get('event_type')})"
            )

        return WebhookResponse(
            success=True,
            message=f"Processed {result.get('event_type')}",
        )

    except ValueError as e:
        logger.error(f"Webhook validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": sanitize_error_message(str(e)), "success": False},
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process webhook", "success": False},
        )


@router.post(
    "/create-portal-session",
    response_model=PortalSessionResponse,
    responses={
        400: {"description": "Stripe not configured or no customer found"},
        500: {"description": "Stripe API error"},
    },
)
async def create_portal_session(
    request: PortalSessionRequest,
    user_id: str = Depends(verify_api_key),
) -> PortalSessionResponse:
    """
    Create a Stripe customer portal session.

    The customer portal allows users to:
    - View and update payment methods
    - View billing history and invoices
    - Cancel or modify their subscription
    - Update billing information

    Args:
        request: Portal session parameters including return_url
        user_id: Authenticated user ID from API key

    Returns:
        PortalSessionResponse with portal URL
    """
    if not stripe_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Payment processing is not configured",
                "success": False,
            },
        )

    try:
        # Get customer ID for user
        customer_id = await stripe_service.get_customer_id_for_user(user_id)

        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "No billing account found. Please subscribe first.",
                    "success": False,
                },
            )

        url = await stripe_service.create_customer_portal_session(
            customer_id=customer_id,
            return_url=request.return_url,
        )

        logger.info(f"Portal session created for user {user_id}")

        return PortalSessionResponse(success=True, url=url)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error creating portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": sanitize_error_message(str(e)), "success": False},
        )
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create portal session", "success": False},
        )


@router.get(
    "/subscription-status",
    response_model=SubscriptionStatus,
    responses={
        400: {"description": "Stripe not configured"},
        500: {"description": "Stripe API error"},
    },
)
async def get_subscription_status(
    user_id: str = Depends(verify_api_key),
) -> SubscriptionStatus:
    """
    Get the current subscription status for the authenticated user.

    Returns information about:
    - Current subscription tier
    - Subscription status (active, past_due, canceled, etc.)
    - Current billing period end date
    - Whether subscription will cancel at period end
    - Monthly generation limit based on tier

    Args:
        user_id: Authenticated user ID from API key

    Returns:
        SubscriptionStatus with current tier and subscription details
    """
    if not stripe_service.is_configured:
        # Return free tier status if Stripe not configured
        return SubscriptionStatus(
            has_subscription=False,
            tier=SubscriptionTier.FREE,
            generations_limit=PRICING_TIERS[SubscriptionTier.FREE].generations_per_month,
        )

    try:
        # Get customer ID for user
        customer_id = await stripe_service.get_customer_id_for_user(user_id)

        if not customer_id:
            # No customer record means free tier
            return SubscriptionStatus(
                has_subscription=False,
                tier=SubscriptionTier.FREE,
                generations_limit=PRICING_TIERS[SubscriptionTier.FREE].generations_per_month,
            )

        status = await stripe_service.get_subscription_status(customer_id)

        logger.info(
            f"Subscription status retrieved for user {user_id}: "
            f"tier={status.tier.value}, has_subscription={status.has_subscription}"
        )

        return status

    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve subscription status", "success": False},
        )


@router.get("/pricing")
async def get_pricing_tiers() -> Dict:
    """
    Get available pricing tiers and their features.

    This endpoint does not require authentication and returns
    public pricing information for display on marketing pages.

    Returns:
        Dictionary containing all pricing tiers with features and prices
    """
    tiers = []
    for tier_key, tier_config in PRICING_TIERS.items():
        # Map to usage tier config so limits/descriptions stay consistent with quota enforcement.
        usage_config = None
        try:
            usage_config = get_tier_config(UsageSubscriptionTier(tier_key.value))
        except Exception:
            usage_config = None

        tier_data = {
            "id": tier_key.value,
            "name": tier_config.name,
            "price_monthly": tier_config.price_monthly / 100,  # Convert cents to dollars
            "price_yearly": tier_config.price_yearly / 100,
            "generations_per_month": tier_config.generations_per_month,
            "features": tier_config.features,
        }

        if usage_config:
            tier_data["daily_limit"] = usage_config.daily_limit
            tier_data["monthly_limit"] = usage_config.monthly_limit
            tier_data["description"] = usage_config.description

        # Add price IDs if configured (for checkout). We intentionally omit Business
        # price IDs unless explicitly enabled.
        if tier_key != SubscriptionTier.BUSINESS or _business_tier_enabled():
            price_ids = stripe_service.get_price_ids_for_tier(tier_key)
            if price_ids.get("month"):
                tier_data["stripe_price_id_monthly"] = price_ids.get("month")
            if price_ids.get("year"):
                tier_data["stripe_price_id_yearly"] = price_ids.get("year")

        tiers.append(tier_data)

    return {
        "success": True,
        "tiers": tiers,
    }
