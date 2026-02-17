"""
Smoke tests for 6 backend features that previously had zero test coverage.

Each test class covers a single route file and verifies:
1. Unauthenticated requests are rejected (401)
2. Invalid / missing body triggers validation errors (400 or 422)
3. The endpoint exists and is routable

These are HTTP-layer tests only -- no internal logic is mocked.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Environment setup (must happen before any app import)
# ---------------------------------------------------------------------------
os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a fresh TestClient bound to the real FastAPI app."""
    from server import app

    return TestClient(app)


# ============================================================================
# 1. Bulk Generation
# ============================================================================


class TestBulkGenerationSmoke:
    """Smoke tests for /api/v1/bulk/* endpoints."""

    def test_bulk_generate_requires_auth(self, client):
        """POST /api/v1/bulk/generate without auth must return 401."""
        response = client.post(
            "/api/v1/bulk/generate",
            json={
                "items": [{"topic": "Test", "keywords": ["a"], "tone": "professional"}],
                "conversation_id": "smoke-bulk-001",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_bulk_status_requires_auth(self, client):
        """GET /api/v1/bulk/status/{job_id} without auth must return 401."""
        response = client.get("/api/v1/bulk/status/nonexistent-job-id")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_bulk_generate_rejects_empty_body(self, client):
        """POST /api/v1/bulk/generate with empty body must return 422."""
        response = client.post(
            "/api/v1/bulk/generate",
            json={},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422, (
            f"Expected 422, got {response.status_code}: {response.text}"
        )

    def test_bulk_cancel_requires_auth(self, client):
        """POST /api/v1/bulk/cancel/{job_id} without auth must return 401."""
        response = client.post("/api/v1/bulk/cancel/nonexistent-job-id")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )


# ============================================================================
# 2. Social Media
# ============================================================================


class TestSocialMediaSmoke:
    """Smoke tests for /api/social/* endpoints."""

    def test_list_accounts_requires_auth(self, client):
        """GET /api/social/accounts without auth must return 401."""
        response = client.get("/api/social/accounts")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_schedule_post_requires_auth(self, client):
        """POST /api/social/posts/schedule without auth must return 401."""
        response = client.post(
            "/api/social/posts/schedule",
            json={
                "account_id": "fake-account",
                "content": {"text": "Hello"},
                "scheduled_at": "2026-03-01T12:00:00Z",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_create_campaign_requires_auth(self, client):
        """POST /api/social/campaigns without auth must return 401."""
        response = client.post(
            "/api/social/campaigns",
            json={
                "name": "Test Campaign",
                "content": {"text": "Hello"},
                "platforms": [{"platform": "twitter", "account_id": "acc-1"}],
                "scheduled_at": "2026-03-01T12:00:00Z",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )


# ============================================================================
# 3. Workflows
# ============================================================================


class TestWorkflowsSmoke:
    """Smoke tests for /api/v1/workflows/* endpoints."""

    def test_create_workflow_requires_auth(self, client):
        """POST /api/v1/workflows without auth must return 401."""
        response = client.post(
            "/api/v1/workflows",
            json={
                "name": "Test Workflow",
                "steps": [{"type": "research", "name": "Step 1"}],
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_list_presets_is_public(self, client):
        """GET /api/v1/workflows/presets should be accessible (no auth required)."""
        response = client.get("/api/v1/workflows/presets")
        # The presets endpoint has no auth dependency, so it should return 200
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"

    def test_list_step_types_is_public(self, client):
        """GET /api/v1/workflows/step-types should be accessible (no auth required)."""
        response = client.get("/api/v1/workflows/step-types")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected at least one step type"

    def test_execute_workflow_requires_auth(self, client):
        """POST /api/v1/workflows/{id}/execute without auth must return 401."""
        response = client.post(
            "/api/v1/workflows/some-workflow-id/execute",
            json={
                "variables": {"topic": "Test"},
                "provider": "openai",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_workflow_status_requires_auth(self, client):
        """GET /api/v1/workflows/{id}/status without auth must return 401."""
        response = client.get("/api/v1/workflows/some-execution-id/status")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )


# ============================================================================
# 4. Zapier
# ============================================================================


class TestZapierSmoke:
    """Smoke tests for /api/v1/zapier/* endpoints."""

    def test_zapier_me_requires_auth(self, client):
        """GET /api/v1/zapier/me without auth must return 401."""
        response = client.get("/api/v1/zapier/me")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_zapier_generate_requires_auth(self, client):
        """POST /api/v1/zapier/actions/generate without auth must return 401."""
        response = client.post(
            "/api/v1/zapier/actions/generate",
            json={
                "topic": "Test Topic",
                "content_type": "blog",
                "tone": "professional",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_zapier_trigger_new_content_requires_auth(self, client):
        """GET /api/v1/zapier/triggers/new-content without auth must return 401."""
        response = client.get("/api/v1/zapier/triggers/new-content")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_zapier_sample_content_is_public(self, client):
        """GET /api/v1/zapier/sample/content should be accessible (no auth)."""
        response = client.get("/api/v1/zapier/sample/content")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"

    def test_zapier_subscribe_requires_auth(self, client):
        """POST /api/v1/zapier/hooks/subscribe/{event_type} without auth must return 401."""
        response = client.post(
            "/api/v1/zapier/hooks/subscribe/content.generated",
            json={"target_url": "https://hooks.zapier.com/test"},
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )


# ============================================================================
# 5. Remix
# ============================================================================


class TestRemixSmoke:
    """Smoke tests for /api/v1/remix/* endpoints."""

    def test_remix_transform_requires_auth(self, client):
        """POST /api/v1/remix/transform without auth must return 401."""
        response = client.post(
            "/api/v1/remix/transform",
            json={
                "source_content": {"title": "Test", "body": "Content body"},
                "target_formats": ["twitter_thread"],
                "conversation_id": "smoke-remix-001",
                "provider": "openai",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_remix_transform_rejects_empty_body(self, client):
        """POST /api/v1/remix/transform with empty body must return 422."""
        response = client.post(
            "/api/v1/remix/transform",
            json={},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422, (
            f"Expected 422, got {response.status_code}: {response.text}"
        )

    def test_remix_formats_endpoint_exists(self, client):
        """GET /api/v1/remix/formats should return available formats."""
        response = client.get("/api/v1/remix/formats")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected at least one format"


# ============================================================================
# 6. Extension
# ============================================================================


class TestExtensionSmoke:
    """Smoke tests for /api/v1/extension/* endpoints."""

    def test_extension_generate_requires_auth(self, client):
        """POST /api/v1/extension/generate without auth must return 401."""
        response = client.post(
            "/api/v1/extension/generate",
            json={
                "topic": "Test Topic",
                "action": "blog",
            },
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_extension_user_requires_auth(self, client):
        """GET /api/v1/extension/user without auth must return 401."""
        response = client.get("/api/v1/extension/user")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_extension_usage_requires_auth(self, client):
        """GET /api/v1/extension/usage without auth must return 401."""
        response = client.get("/api/v1/extension/usage")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text}"
        )

    def test_extension_auth_rejects_empty_body(self, client):
        """POST /api/v1/extension/auth with empty body must return 422."""
        response = client.post(
            "/api/v1/extension/auth",
            json={},
        )
        assert response.status_code == 422, (
            f"Expected 422, got {response.status_code}: {response.text}"
        )

    def test_extension_generate_rejects_empty_body(self, client):
        """POST /api/v1/extension/generate with empty body must return 422."""
        response = client.post(
            "/api/v1/extension/generate",
            json={},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 422, (
            f"Expected 422, got {response.status_code}: {response.text}"
        )
