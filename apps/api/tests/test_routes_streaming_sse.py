"""
Quota enforcement on GET /stream/sse/{conversation_id}.

The SSE route authenticates the API key by hand instead of through the
`require_quota` dependency, and it neither checked the quota nor recorded the
generation: a valid key could stream without limit.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-unit-tests-only")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from src.text_generation.streaming import StreamEvent, StreamEventType

URL = "/stream/sse/conv-1"
PARAMS = {"prompt": "hello", "max_tokens": 100}
HEADERS = {"X-API-Key": "valid-key"}


@pytest.fixture
def client():
    from server import app

    with patch("app.auth.api_key.api_key_store.verify_key", return_value="user_1"):
        yield TestClient(app)


def _stream(*events):
    async def fake_stream_text(*_args, **_kwargs):
        for event in events:
            yield event

    return fake_stream_text


def test_sse_is_refused_when_the_quota_is_exhausted(client):
    over_quota = AsyncMock(
        side_effect=HTTPException(status_code=429, detail="Quota exceeded")
    )
    with (
        patch("app.routes.streaming.require_quota", over_quota),
        patch("app.routes.streaming.create_provider_from_env") as mock_provider,
    ):
        response = client.get(URL, params=PARAMS, headers=HEADERS)

    assert response.status_code == 429
    over_quota.assert_awaited_once_with("user_1")
    mock_provider.assert_not_called()


def test_completed_sse_generation_is_recorded(client):
    events = _stream(
        StreamEvent(type=StreamEventType.TOKEN, content="Hi"),
        StreamEvent(type=StreamEventType.END),
    )
    with (
        patch("app.routes.streaming.require_quota", AsyncMock(return_value="user_1")),
        patch("app.routes.streaming.create_provider_from_env"),
        patch("app.routes.streaming.stream_text", events),
        patch(
            "app.routes.streaming.increment_usage_for_operation", new_callable=AsyncMock
        ) as mock_usage,
    ):
        response = client.get(URL, params=PARAMS, headers=HEADERS)

    assert response.status_code == 200
    assert "event: complete" in response.text
    mock_usage.assert_awaited_once()
    assert mock_usage.await_args.kwargs["user_id"] == "user_1"
    assert mock_usage.await_args.kwargs["operation_type"] == "streaming"


def test_failed_sse_generation_is_not_charged(client):
    events = _stream(StreamEvent(type=StreamEventType.ERROR, error="provider down"))
    with (
        patch("app.routes.streaming.require_quota", AsyncMock(return_value="user_1")),
        patch("app.routes.streaming.create_provider_from_env"),
        patch("app.routes.streaming.stream_text", events),
        patch(
            "app.routes.streaming.increment_usage_for_operation", new_callable=AsyncMock
        ) as mock_usage,
    ):
        response = client.get(URL, params=PARAMS, headers=HEADERS)

    assert response.status_code == 200
    assert "event: error" in response.text
    mock_usage.assert_not_awaited()
