"""
Minimal backend smoke checks for CI required-status gating.

These tests intentionally validate only startup + core liveness routes so
regression-heavy suites don't block unrelated frontend/release hardening PRs.
"""

import os
import sys

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


def test_root_endpoint_returns_metadata():
    from server import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert "message" in payload
    assert "version" in payload


def test_health_endpoint_is_healthy():
    from server import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "healthy"
    assert "timestamp" in payload
