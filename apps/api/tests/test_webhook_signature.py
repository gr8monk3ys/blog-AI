"""
Unit tests for outgoing-webhook HMAC signature generation.

The signature is a security primitive: receivers verify it to trust payloads,
and the included timestamp guards against replay. These tests pin the exact
HMAC-SHA256 scheme and its tamper/replay properties.
"""

import hashlib
import hmac

from src.webhooks.webhook_service import webhook_service


def _expected(payload: str, secret: str, timestamp: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.{payload}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def test_signature_matches_hmac_sha256_over_timestamp_dot_payload():
    payload = '{"event":"content.generated","id":"abc"}'
    sig = webhook_service._generate_signature(payload, "shhh", "1700000000")
    assert sig == _expected(payload, "shhh", "1700000000")
    # hex-encoded SHA256 is 64 chars
    assert len(sig) == 64


def test_signature_is_deterministic():
    a = webhook_service._generate_signature("p", "s", "1")
    b = webhook_service._generate_signature("p", "s", "1")
    assert a == b


def test_empty_secret_returns_empty_string():
    assert webhook_service._generate_signature("p", "", "1") == ""


def test_timestamp_is_bound_into_signature_for_replay_protection():
    a = webhook_service._generate_signature("p", "s", "1700000000")
    b = webhook_service._generate_signature("p", "s", "1700000001")
    assert a != b


def test_payload_tamper_changes_signature():
    a = webhook_service._generate_signature('{"amount":10}', "s", "1")
    b = webhook_service._generate_signature('{"amount":1000}', "s", "1")
    assert a != b


def test_different_secret_changes_signature():
    a = webhook_service._generate_signature("p", "secret-a", "1")
    b = webhook_service._generate_signature("p", "secret-b", "1")
    assert a != b


# ---------------------------------------------------------------------------
# Delivery-prep helpers: header building and retry backoff
# ---------------------------------------------------------------------------

from src.types.webhooks import WebhookEventType
from src.webhooks.webhook_service import (
    WEBHOOK_RETRY_BASE_DELAY,
    WEBHOOK_RETRY_MAX_DELAY,
    WEBHOOK_USER_AGENT,
)


def test_build_headers_includes_identity_and_signature():
    headers = webhook_service._build_headers(
        payload='{"a":1}',
        secret="topsecret",
        event_id="evt-1",
        event_type=WebhookEventType.CONTENT_GENERATED,
    )
    assert headers["Content-Type"] == "application/json"
    assert headers["User-Agent"] == WEBHOOK_USER_AGENT
    assert headers["X-Webhook-ID"] == "evt-1"
    assert headers["X-Webhook-Event"] == "content.generated"
    # Stripe-style signature header: t=<ts>,v1=<sig>, with ts matching the
    # X-Webhook-Timestamp header so receivers can verify what was signed.
    sig_header = headers["X-Webhook-Signature"]
    ts = headers["X-Webhook-Timestamp"]
    assert sig_header.startswith(f"t={ts},v1=")
    expected = webhook_service._generate_signature('{"a":1}', "topsecret", ts)
    assert sig_header == f"t={ts},v1={expected}"


def test_build_headers_omits_signature_without_secret():
    headers = webhook_service._build_headers(
        payload="{}",
        secret="",
        event_id="evt-2",
        event_type=WebhookEventType.CONTENT_GENERATED,
    )
    assert "X-Webhook-Signature" not in headers


def test_retry_delay_grows_exponentially_and_caps():
    # Base 1s doubling: attempt n is in [2^(n-1), 2^(n-1)*1.25] before the cap.
    for attempt in (1, 2, 3, 4):
        base = WEBHOOK_RETRY_BASE_DELAY * (2 ** (attempt - 1))
        delay = webhook_service._calculate_retry_delay(attempt)
        assert base <= delay <= int(base * 1.25) + 1
    # Very high attempts are capped at the max delay.
    assert webhook_service._calculate_retry_delay(20) <= WEBHOOK_RETRY_MAX_DELAY
