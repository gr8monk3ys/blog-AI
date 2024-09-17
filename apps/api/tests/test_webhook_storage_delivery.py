"""
Tests for webhook storage (in-memory fallback) and the delivery path.

Covers the WebhookStorage subscription lifecycle on the in-memory fallback
backend (Redis unavailable — the same code path production hits on Redis
outage), the _deliver_webhook success/failure outcomes against a mocked HTTP
client, and the reconcile_subscriptions guard rails. Closes the Phase 2.2
backlog in docs/REMEDIATION_PLAN.md.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("DEV_API_KEY", "test-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-unit-tests-only")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.types.webhooks import (
    DeliveryStatus,
    WebhookEventType,
    WebhookPayload,
    WebhookSubscription,
)
from src.webhooks.webhook_storage import WebhookStorage


def make_sub(sub_id="sub-1", user_id="user-1", **overrides) -> WebhookSubscription:
    defaults = dict(
        id=sub_id,
        user_id=user_id,
        target_url="https://hooks.example.com/endpoint",
        event_types=[WebhookEventType.CONTENT_GENERATED],
    )
    defaults.update(overrides)
    return WebhookSubscription(**defaults)


@pytest.fixture
def storage():
    """A WebhookStorage forced onto the in-memory fallback (no Redis)."""
    s = WebhookStorage()
    patcher = patch.object(s, "_get_redis", AsyncMock(return_value=None))
    patcher.start()
    yield s
    patcher.stop()


# ---------------------------------------------------------------------------
# In-memory fallback: subscription lifecycle
# ---------------------------------------------------------------------------


async def test_save_and_get_subscription(storage):
    assert await storage.save_subscription(make_sub()) is True
    sub = await storage.get_subscription("sub-1")
    assert sub is not None
    assert sub.user_id == "user-1"
    assert sub.target_url == "https://hooks.example.com/endpoint"


async def test_get_subscription_if_owned_enforces_ownership(storage):
    await storage.save_subscription(make_sub())
    assert await storage.get_subscription_if_owned("sub-1", "user-1") is not None
    # Another user must not be able to read it.
    assert await storage.get_subscription_if_owned("sub-1", "intruder") is None


async def test_list_and_count_scope_to_user(storage):
    await storage.save_subscription(make_sub("sub-a", "user-1"))
    await storage.save_subscription(make_sub("sub-b", "user-1"))
    await storage.save_subscription(make_sub("sub-c", "user-2"))

    mine = await storage.list_user_subscriptions("user-1")
    assert {s.id for s in mine} == {"sub-a", "sub-b"}
    assert await storage.count_user_subscriptions("user-1") == 2
    assert await storage.count_user_subscriptions("user-2") == 1


async def test_delete_subscription(storage):
    await storage.save_subscription(make_sub())
    assert await storage.delete_subscription("sub-1") is True
    assert await storage.get_subscription("sub-1") is None


async def test_get_subscriptions_for_event_filters_type_and_active(storage):
    await storage.save_subscription(make_sub("sub-match", "user-1"))
    await storage.save_subscription(
        make_sub(
            "sub-other-event",
            "user-1",
            event_types=[WebhookEventType.BATCH_COMPLETED],
        )
    )
    await storage.save_subscription(make_sub("sub-inactive", "user-1", is_active=False))

    subs = await storage.get_subscriptions_for_event(WebhookEventType.CONTENT_GENERATED)
    assert {s.id for s in subs} == {"sub-match"}


# ---------------------------------------------------------------------------
# Delivery path (_deliver_webhook) against a mocked HTTP client
# ---------------------------------------------------------------------------


def _payload() -> WebhookPayload:
    return WebhookPayload(
        id="evt-1",
        event_type=WebhookEventType.CONTENT_GENERATED,
        data={"k": "v"},
    )


def _http_response(status_code: int):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    resp.text = "ok" if status_code < 300 else "boom"
    return resp


async def _deliver_with(status_code=None, exc=None):
    from src.webhooks.webhook_service import WebhookService

    service = WebhookService()
    client = MagicMock()
    if exc is not None:
        client.post = AsyncMock(side_effect=exc)
    else:
        client.post = AsyncMock(return_value=_http_response(status_code))

    mock_storage = MagicMock()
    mock_storage.save_delivery = AsyncMock(return_value=True)
    mock_storage.update_subscription_stats = AsyncMock(return_value=True)

    with (
        patch.object(service, "_get_client", AsyncMock(return_value=client)),
        patch("src.webhooks.webhook_service.webhook_storage", mock_storage),
    ):
        delivery = await service._deliver_webhook(
            subscription=make_sub(secret="s3cret"),
            payload=_payload(),
            delivery_id="dlv-1",
        )
    return delivery, client, mock_storage


async def test_delivery_2xx_is_delivered_and_signed():
    delivery, client, storage = await _deliver_with(status_code=200)
    assert delivery.status == DeliveryStatus.DELIVERED
    assert delivery.response_status_code == 200
    # The request carried the signature header (secret was set).
    _, kwargs = client.post.call_args
    assert "X-Webhook-Signature" in kwargs["headers"]
    storage.save_delivery.assert_awaited()


async def test_delivery_5xx_is_failed_with_error():
    delivery, _, _ = await _deliver_with(status_code=500)
    assert delivery.status == DeliveryStatus.FAILED
    assert "HTTP 500" in (delivery.error_message or "")


async def test_delivery_network_error_is_failed():
    import httpx

    delivery, _, _ = await _deliver_with(exc=httpx.RequestError("connection refused"))
    assert delivery.status == DeliveryStatus.FAILED


# ---------------------------------------------------------------------------
# reconcile_subscriptions guard rails
# ---------------------------------------------------------------------------


async def test_reconcile_without_db_returns_error_summary():
    from src.payments.subscription_sync import SubscriptionSyncService

    service = SubscriptionSyncService()
    service._use_db = False
    result = await service.reconcile_subscriptions()
    assert result["checked"] == 0
    assert result["error"] == "Database not configured"


async def test_reconcile_no_paid_users_returns_zero_summary():
    from src.payments.subscription_sync import SubscriptionSyncService

    service = SubscriptionSyncService()
    service._use_db = True
    with patch(
        "src.payments.subscription_sync.db_fetch", new=AsyncMock(return_value=[])
    ):
        result = await service.reconcile_subscriptions()
    assert result == {
        "checked": 0,
        "mismatches_found": 0,
        "fixed": 0,
        "errors": 0,
        "details": [],
    }


async def test_reconcile_aborts_when_stripe_unconfigured():
    from src.payments.subscription_sync import SubscriptionSyncService

    service = SubscriptionSyncService()
    service._use_db = True
    rows = [
        {
            "user_id": "u1",
            "tier": "pro",
            "customer_id": "cus_1",
            "subscription_id": "sub_1",
        }
    ]
    with (
        patch(
            "src.payments.subscription_sync.db_fetch", new=AsyncMock(return_value=rows)
        ),
        patch("src.payments.stripe_service.stripe_service") as mock_svc,
    ):
        mock_svc.is_configured = False
        result = await service.reconcile_subscriptions()
    assert result["error"] == "Stripe not configured"
    assert result["fixed"] == 0
