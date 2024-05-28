"""
Pydantic models for Stripe payment integration.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionInterval(str, Enum):
    """Billing interval options."""

    MONTH = "month"
    YEAR = "year"


class CheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session."""

    price_id: str = Field(
        ...,
        description="Stripe price ID for the subscription tier",
        min_length=1,
    )
    success_url: str = Field(
        ...,
        description="URL to redirect to after successful checkout",
    )
    cancel_url: str = Field(
        ...,
        description="URL to redirect to if checkout is cancelled",
    )


class CheckoutSessionResponse(BaseModel):
    """Response containing checkout session details."""

    success: bool = True
    session_id: str = Field(..., description="Stripe checkout session ID")
    url: str = Field(..., description="URL to redirect the user to for checkout")


class PortalSessionRequest(BaseModel):
    """Request to create a Stripe customer portal session."""

    return_url: str = Field(
        ...,
        description="URL to redirect to when the user exits the portal",
    )


class PortalSessionResponse(BaseModel):
    """Response containing customer portal session details."""

    success: bool = True
    url: str = Field(..., description="URL to redirect the user to for the portal")


class SubscriptionStatus(BaseModel):
    """Current subscription status for a user."""

    success: bool = True
    has_subscription: bool = Field(
        ...,
        description="Whether the user has an active subscription",
    )
    tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        description="Current subscription tier",
    )
    status: Optional[str] = Field(
        None,
        description="Stripe subscription status (active, past_due, canceled, etc.)",
    )
    current_period_end: Optional[int] = Field(
        None,
        description="Unix timestamp when the current billing period ends",
    )
    cancel_at_period_end: bool = Field(
        False,
        description="Whether the subscription will cancel at period end",
    )
    customer_id: Optional[str] = Field(
        None,
        description="Stripe customer ID",
    )
    generations_limit: int = Field(
        5,
        description="Monthly generation limit based on tier",
    )


class WebhookEventType(str, Enum):
    """Stripe webhook event types we handle."""

    CHECKOUT_COMPLETED = "checkout.session.completed"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"


class WebhookResponse(BaseModel):
    """Response for webhook processing."""

    success: bool = True
    message: str = Field(default="Webhook processed successfully")


class PricingTier(BaseModel):
    """Pricing tier configuration."""

    name: str
    tier: SubscriptionTier
    price_monthly: int = Field(..., description="Monthly price in cents")
    price_yearly: int = Field(..., description="Yearly price in cents")
    generations_per_month: int
    features: list[str]
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None


# Tier configurations with pricing and limits
PRICING_TIERS: dict[SubscriptionTier, PricingTier] = {
    SubscriptionTier.FREE: PricingTier(
        name="Free",
        tier=SubscriptionTier.FREE,
        price_monthly=0,
        price_yearly=0,
        generations_per_month=5,
        features=[
            "5 generations per month",
            "Basic blog generation",
            "Standard support",
        ],
    ),
    SubscriptionTier.STARTER: PricingTier(
        name="Starter",
        tier=SubscriptionTier.STARTER,
        price_monthly=1900,  # $19.00
        price_yearly=19000,  # $190.00 (save ~17%)
        generations_per_month=50,
        features=[
            "50 generations per month",
            "Blog and book generation",
            "Research mode",
            "Priority support",
        ],
    ),
    SubscriptionTier.PRO: PricingTier(
        name="Pro",
        tier=SubscriptionTier.PRO,
        price_monthly=4900,  # $49.00
        price_yearly=49000,  # $490.00 (save ~17%)
        generations_per_month=200,
        features=[
            "200 generations per month",
            "All content types",
            "Bulk generation",
            "Brand voice training",
            "Priority support",
        ],
    ),
    SubscriptionTier.BUSINESS: PricingTier(
        name="Business",
        tier=SubscriptionTier.BUSINESS,
        price_monthly=14900,  # $149.00
        price_yearly=149000,  # $1490.00 (save ~17%)
        generations_per_month=1000,
        features=[
            "1000 generations per month",
            "All Pro features",
            "API access",
            "Custom integrations",
            "Dedicated support",
        ],
    ),
}


def get_tier_generation_limit(tier: SubscriptionTier) -> int:
    """Get the monthly generation limit for a tier."""
    return PRICING_TIERS[tier].generations_per_month
