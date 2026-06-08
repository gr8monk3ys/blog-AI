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
