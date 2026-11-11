"""
Stripe handlers against objects built by the real, installed Stripe SDK.

Every other payment test replaces the `stripe` module with a MagicMock and feeds
the handlers plain dicts. That hid a production bug: from stripe 13 a
StripeObject is no longer a dict, so `event["data"]["object"].get(...)` raises
AttributeError. With the locked SDK (15.x) every handled webhook returned 500
and no paid plan was ever activated. These tests sign a payload, run it through
the SDK's own `Webhook.construct_event`, and hand the result to the handlers.
"""

import asyncio
import hashlib
import hmac
import importlib
import json
import os
import sys
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

WEBHOOK_SECRET = "whsec_test_secret_for_unit_tests"
ENV = {
    "STRIPE_SECRET_KEY": "sk_test_dummy",
    "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
    "STRIPE_PRICE_ID_STARTER_MONTHLY": "price_starter_m",
    "STRIPE_PRICE_ID_PRO_MONTHLY": "price_pro_m",
}


@contextmanager
def real_stripe():
    """Yield the real `stripe` module even if another test installed the mock."""
    mocked = {
        name: module
        for name, module in sys.modules.items()
        if (name == "stripe" or name.startswith("stripe."))
        and isinstance(module, MagicMock)
    }
    for name in mocked:
        del sys.modules[name]
    try:
        stripe = importlib.import_module("stripe")
        previous_key = stripe.api_key
        try:
            yield stripe
        finally:
            stripe.api_key = previous_key
    finally:
        sys.modules.update(mocked)


@contextmanager
def service_on_real_sdk():
    """A StripeService bound to the real SDK, plus that SDK module."""
    # `src.payments` re-exports the `stripe_service` instance under the same
    # name as the submodule, so resolve the module through the import system.
    service_module = importlib.import_module("src.payments.stripe_service")

    with (
        real_stripe() as stripe,
        patch.dict(os.environ, ENV, clear=False),
        patch.object(service_module, "stripe", stripe),
        patch.object(
            service_module,
            "SignatureVerificationError",
            stripe.SignatureVerificationError,
        ),
    ):
        yield service_module.StripeService(), stripe


def signed(event: dict, secret: str = WEBHOOK_SECRET) -> tuple[bytes, str]:
    payload = json.dumps(event)
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256
    ).hexdigest()
    return payload.encode(), f"t={timestamp},v1={signature}"


def event(event_type: str, obj: dict) -> dict:
    return {
        "id": "evt_real_sdk_1",
        "object": "event",
        "type": event_type,
        "data": {"object": obj},
    }


def test_sdk_objects_are_not_dicts():
    """The premise of this file: if this ever fails the guard can be dropped."""
    with real_stripe() as stripe:
        payload, header = signed(
            event("checkout.session.completed", {"object": "checkout.session"})
        )
        obj = stripe.Webhook.construct_event(payload, header, WEBHOOK_SECRET)["data"][
            "object"
        ]
        if isinstance(obj, dict):
            pytest.skip("installed stripe SDK still returns dict-based objects")
        with pytest.raises(AttributeError):
            obj.get("customer")


def test_checkout_completed_webhook_is_parsed():
    with service_on_real_sdk() as (service, _):
        payload, header = signed(
            event(
                "checkout.session.completed",
                {
                    "id": "cs_1",
                    "object": "checkout.session",
                    "customer": "cus_1",
                    "subscription": "sub_1",
                    "metadata": {"user_id": "user_1"},
                },
            )
        )

        result = service.handle_webhook(payload, header)

    assert result == {
        "event_type": "checkout.session.completed",
        "event_id": "evt_real_sdk_1",
        "customer_id": "cus_1",
        "subscription_id": "sub_1",
        "user_id": "user_1",
    }


@pytest.mark.parametrize(
    "event_type",
    ["customer.subscription.created", "customer.subscription.updated"],
)
def test_subscription_webhook_resolves_the_paid_tier(event_type):
    with service_on_real_sdk() as (service, _):
        payload, header = signed(
            event(
                event_type,
                {
                    "id": "sub_1",
                    "object": "subscription",
                    "customer": "cus_1",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "metadata": {"user_id": "user_1"},
                    "items": {
                        "object": "list",
                        "data": [{"id": "si_1", "price": {"id": "price_pro_m"}}],
                    },
                },
            )
        )

        result = service.handle_webhook(payload, header)

    assert result["user_id"] == "user_1"
    assert result["subscription_id"] == "sub_1"
    assert result["status"] == "active"
    assert result["tier"] == "pro"


@pytest.mark.parametrize(
    "invoice_fields",
    [
        {"subscription": "sub_1"},
        # API versions >= 2025-03-31 nest the subscription under `parent`.
        {
            "parent": {
                "type": "subscription_details",
                "subscription_details": {"subscription": "sub_1"},
            }
        },
    ],
)
def test_invoice_paid_webhook_finds_the_subscription(invoice_fields):
    with service_on_real_sdk() as (service, _):
        payload, header = signed(
            event(
                "invoice.paid",
                {
                    "id": "in_1",
                    "object": "invoice",
                    "customer": "cus_1",
                    "amount_paid": 4900,
                    **invoice_fields,
                },
            )
        )

        result = service.handle_webhook(payload, header)

    assert result["customer_id"] == "cus_1"
    assert result["subscription_id"] == "sub_1"
    assert result["amount_paid"] == 4900


def test_forged_signature_is_still_rejected():
    with service_on_real_sdk() as (service, _):
        payload, header = signed(
            event("checkout.session.completed", {"object": "checkout.session"}),
            secret="whsec_not_the_configured_secret",
        )

        with pytest.raises(ValueError, match="Invalid webhook signature"):
            service.handle_webhook(payload, header)


def _subscription(stripe, **overrides):
    return stripe.Subscription.construct_from(
        {
            "id": "sub_1",
            "object": "subscription",
            "status": "active",
            "cancel_at_period_end": False,
            "items": {
                "object": "list",
                "data": [
                    {
                        "id": "si_1",
                        "current_period_end": 1900000000,
                        "price": {"id": "price_pro_m"},
                    }
                ],
            },
            **overrides,
        },
        "sk_test_dummy",
    )


def test_subscription_status_reads_period_end_from_the_item():
    """`subscription.current_period_end` no longer exists on current API versions."""
    with service_on_real_sdk() as (service, stripe):
        listing = MagicMock(data=[_subscription(stripe)])
        with patch.object(stripe.Subscription, "list", return_value=listing):
            status = asyncio.run(service.get_subscription_status("cus_1"))

    assert status.has_subscription is True
    assert status.tier.value == "pro"
    assert status.current_period_end == 1900000000


def test_subscription_status_still_reads_a_top_level_period_end():
    with service_on_real_sdk() as (service, stripe):
        listing = MagicMock(data=[_subscription(stripe, current_period_end=1800000000)])
        with patch.object(stripe.Subscription, "list", return_value=listing):
            status = asyncio.run(service.get_subscription_status("cus_1"))

    assert status.current_period_end == 1800000000


def test_checkout_tier_is_resolved_from_a_real_subscription_object():
    """checkout.session.completed activates the plan by fetching the subscription."""
    from src.payments.subscription_sync import SubscriptionSyncService

    with service_on_real_sdk() as (service, stripe):
        service_module = importlib.import_module("src.payments.stripe_service")

        stripe.api_key = "sk_test_dummy"
        with (
            patch.object(
                stripe.Subscription, "retrieve", return_value=_subscription(stripe)
            ),
            patch.object(service_module, "stripe_service", service),
        ):
            tier = asyncio.run(
                SubscriptionSyncService()._resolve_tier_from_subscription("sub_1")
            )

    assert tier == "pro"


def test_user_is_found_from_a_real_customer_object():
    from src.payments.subscription_sync import SubscriptionSyncService

    with real_stripe() as stripe:
        stripe.api_key = "sk_test_dummy"
        customer = stripe.Customer.construct_from(
            {"id": "cus_1", "object": "customer", "metadata": {"user_id": "user_1"}},
            "sk_test_dummy",
        )
        sync = SubscriptionSyncService()
        sync._use_db = False
        with patch.object(stripe.Customer, "retrieve", return_value=customer):
            user_id = asyncio.run(sync._get_user_id_from_customer("cus_1"))

    assert user_id == "user_1"
