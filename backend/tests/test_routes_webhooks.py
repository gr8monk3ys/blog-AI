"""
Tests for webhook management routes.

Comprehensive tests covering:
- Webhook subscription CRUD operations
- SSRF protection on webhook target URLs
- Duplicate subscription detection
- Webhook test endpoint
- Event type listing
- Activate/deactivate subscriptions
- Authorization via content permissions
- Proper status codes (201, 204, 400, 404, 409)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.organizations import AuthorizationContext


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create test client."""
    from server import app
    return TestClient(app)


@pytest.fixture
def mock_auth_ctx():
    """Create a mock AuthorizationContext for content operations."""
    return AuthorizationContext(
        user_id="test-user-001",
        organization_id="org-001",
        role="admin",
        is_org_member=True,
    )


@pytest.fixture
def mock_webhook_deps(mock_auth_ctx):
    """Mock common webhook route dependencies."""
    with patch(
        "app.routes.webhooks.require_content_creation",
    ) as mock_create, patch(
        "app.routes.webhooks.require_content_access",
    ) as mock_access:
        # Make the dependencies return the auth context
        mock_create.return_value = mock_auth_ctx
        mock_access.return_value = mock_auth_ctx

        # Override FastAPI dependency resolution
        from server import app
        from app.dependencies import require_content_creation, require_content_access

        app.dependency_overrides[require_content_creation] = lambda: mock_auth_ctx
        app.dependency_overrides[require_content_access] = lambda: mock_auth_ctx

        yield {
            "create": mock_create,
            "access": mock_access,
            "auth_ctx": mock_auth_ctx,
        }

        app.dependency_overrides.clear()


@pytest.fixture
def sample_subscription():
    """Create a sample webhook subscription for testing."""
    from src.types.webhooks import WebhookEventType, WebhookSubscription
    return WebhookSubscription(
        id="sub-001",
        user_id="org-001",
        target_url="https://hooks.example.com/webhook",
        event_types=[WebhookEventType.CONTENT_GENERATED],
        secret="whsec_test123",
        is_active=True,
        description="Test subscription",
        metadata={},
    )


# =============================================================================
# Subscribe Webhook
# =============================================================================


class TestSubscribeWebhook:
    """Tests for webhook subscription creation."""

    def test_subscribe_with_valid_url_succeeds(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Subscribing with a valid HTTPS URL returns 201."""
        with patch(
            "app.routes.webhooks.validate_url", return_value=(True, "")
        ), patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.list_user_subscriptions = AsyncMock(return_value=[])
            mock_storage.save_subscription = AsyncMock(return_value=True)

            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://hooks.example.com/webhook",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["target_url"] == "https://hooks.example.com/webhook"
        assert data["is_active"] is True

    def test_subscribe_with_ssrf_localhost_returns_400(
        self, client, mock_webhook_deps
    ):
        """Subscribing with localhost URL returns 400 (SSRF protection)."""
        with patch(
            "app.routes.webhooks.validate_url",
            return_value=(False, "Hostname 'localhost' is not allowed"),
        ):
            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://localhost/webhook",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_subscribe_with_ssrf_metadata_ip_returns_400(
        self, client, mock_webhook_deps
    ):
        """Subscribing with AWS metadata IP returns 400 (SSRF protection)."""
        with patch(
            "app.routes.webhooks.validate_url",
            return_value=(False, "Hostname '169.254.169.254' is not allowed"),
        ):
            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://169.254.169.254/latest/meta-data/",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 400

    def test_subscribe_with_private_ip_returns_400(
        self, client, mock_webhook_deps
    ):
        """Subscribing with private IP returns 400 (SSRF protection)."""
        with patch(
            "app.routes.webhooks.validate_url",
            return_value=(False, "Private/internal IP addresses are not allowed"),
        ):
            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://192.168.1.1/webhook",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 400

    def test_subscribe_duplicate_url_returns_409(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Subscribing to the same URL with overlapping events returns 409."""
        with patch(
            "app.routes.webhooks.validate_url", return_value=(True, "")
        ), patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.list_user_subscriptions = AsyncMock(
                return_value=[sample_subscription]
            )

            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://hooks.example.com/webhook",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 409

    def test_subscribe_storage_failure_returns_500(
        self, client, mock_webhook_deps
    ):
        """Storage failure during subscribe returns 500."""
        with patch(
            "app.routes.webhooks.validate_url", return_value=(True, "")
        ), patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.list_user_subscriptions = AsyncMock(return_value=[])
            mock_storage.save_subscription = AsyncMock(return_value=False)

            response = client.post(
                "/webhooks/subscribe",
                json={
                    "target_url": "https://hooks.example.com/new-webhook",
                    "event_types": ["content.generated"],
                },
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 500


# =============================================================================
# Unsubscribe Webhook
# =============================================================================


class TestUnsubscribeWebhook:
    """Tests for webhook unsubscribe (delete)."""

    def test_delete_webhook_returns_204(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Deleting an owned subscription returns 204."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )
            mock_storage.delete_subscription = AsyncMock(return_value=True)

            response = client.delete(
                "/webhooks/sub-001",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 204

    def test_delete_nonexistent_webhook_returns_404(
        self, client, mock_webhook_deps
    ):
        """Deleting a non-existent subscription returns 404."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(return_value=None)

            response = client.delete(
                "/webhooks/sub-nonexistent",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 404


# =============================================================================
# List Webhooks
# =============================================================================


class TestListWebhooks:
    """Tests for listing webhook subscriptions."""

    def test_list_webhooks_returns_proper_format(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Listing webhooks returns paginated results."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.list_user_subscriptions = AsyncMock(
                return_value=[sample_subscription]
            )

            response = client.get(
                "/webhooks",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        assert data["total"] == 1

    def test_list_webhooks_empty(self, client, mock_webhook_deps):
        """Listing webhooks with no subscriptions returns empty list."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.list_user_subscriptions = AsyncMock(return_value=[])

            response = client.get(
                "/webhooks",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["subscriptions"] == []


# =============================================================================
# Get Webhook
# =============================================================================


class TestGetWebhook:
    """Tests for retrieving a single webhook subscription."""

    def test_get_webhook_by_id(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Getting an existing webhook by ID succeeds."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )

            response = client.get(
                "/webhooks/sub-001",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sub-001"

    def test_get_nonexistent_webhook_returns_404(
        self, client, mock_webhook_deps
    ):
        """Getting a non-existent webhook returns 404."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(return_value=None)

            response = client.get(
                "/webhooks/sub-nonexistent",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 404


# =============================================================================
# Update Webhook
# =============================================================================


class TestUpdateWebhook:
    """Tests for updating webhook subscriptions."""

    def test_update_webhook_target_url_validates_ssrf(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Updating target URL validates against SSRF."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage, patch(
            "app.routes.webhooks.validate_url",
            return_value=(False, "Hostname 'localhost' is not allowed"),
        ):
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )

            response = client.patch(
                "/webhooks/sub-001",
                json={"target_url": "https://localhost/evil"},
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 400

    def test_update_webhook_valid_url_succeeds(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Updating with a valid target URL succeeds."""
        updated_sub = sample_subscription.model_copy()
        updated_sub.target_url = "https://new-hooks.example.com/webhook"

        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage, patch(
            "app.routes.webhooks.validate_url", return_value=(True, "")
        ):
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )
            mock_storage.update_subscription = AsyncMock(return_value=True)
            mock_storage.get_subscription = AsyncMock(return_value=updated_sub)

            response = client.patch(
                "/webhooks/sub-001",
                json={"target_url": "https://new-hooks.example.com/webhook"},
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200

    def test_update_nonexistent_webhook_returns_404(
        self, client, mock_webhook_deps
    ):
        """Updating a non-existent webhook returns 404."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(return_value=None)

            response = client.patch(
                "/webhooks/sub-nonexistent",
                json={"description": "Updated"},
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 404


# =============================================================================
# Test Webhook
# =============================================================================


class TestWebhookTest:
    """Tests for webhook test endpoint."""

    def test_test_webhook_validates_target_url(
        self, client, mock_webhook_deps
    ):
        """Test webhook validates target URL against SSRF."""
        with patch(
            "app.routes.webhooks.validate_url",
            return_value=(False, "Private/internal IP addresses are not allowed"),
        ):
            response = client.post(
                "/webhooks/test",
                json={"target_url": "https://10.0.0.1/hook"},
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 400

    def test_test_webhook_with_subscription_id(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Test webhook using existing subscription ID."""
        from src.types.webhooks import DeliveryStatus

        mock_delivery = MagicMock()
        mock_delivery.status = DeliveryStatus.DELIVERED
        mock_delivery.id = "del-001"
        mock_delivery.response_status_code = 200
        mock_delivery.duration_ms = 150
        mock_delivery.error_message = None

        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage, patch(
            "app.routes.webhooks.webhook_service"
        ) as mock_service:
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )
            mock_service.test_webhook = AsyncMock(return_value=mock_delivery)

            response = client.post(
                "/webhooks/test",
                json={"subscription_id": "sub-001"},
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status_code"] == 200

    def test_test_webhook_missing_params_returns_400(
        self, client, mock_webhook_deps
    ):
        """Test webhook without subscription_id or target_url returns 400."""
        response = client.post(
            "/webhooks/test",
            json={},
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 400


# =============================================================================
# Event Types
# =============================================================================


class TestEventTypes:
    """Tests for event type listing endpoint."""

    def test_list_event_types_returns_all_types(self, client):
        """List event types returns all supported webhook event types."""
        response = client.get("/webhooks/events/types")

        assert response.status_code == 200
        data = response.json()
        assert "event_types" in data
        assert data["total"] > 0

        # Verify expected event types are present
        type_values = [et["type"] for et in data["event_types"]]
        assert "content.generated" in type_values
        assert "content.published" in type_values
        assert "batch.completed" in type_values
        assert "quota.exceeded" in type_values

    def test_list_event_types_includes_descriptions(self, client):
        """Each event type includes a description and data_fields."""
        response = client.get("/webhooks/events/types")

        data = response.json()
        for event_type in data["event_types"]:
            assert "description" in event_type
            assert "data_fields" in event_type
            assert len(event_type["description"]) > 0


# =============================================================================
# Activate / Deactivate
# =============================================================================


class TestActivateDeactivate:
    """Tests for activating and deactivating webhook subscriptions."""

    def test_activate_webhook(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Activating a webhook sets is_active to True."""
        activated_sub = sample_subscription.model_copy()
        activated_sub.is_active = True

        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )
            mock_storage.update_subscription = AsyncMock(return_value=True)
            mock_storage.get_subscription = AsyncMock(return_value=activated_sub)

            response = client.post(
                "/webhooks/sub-001/activate",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_deactivate_webhook(
        self, client, mock_webhook_deps, sample_subscription
    ):
        """Deactivating a webhook sets is_active to False."""
        deactivated_sub = sample_subscription.model_copy()
        deactivated_sub.is_active = False

        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(
                return_value=sample_subscription
            )
            mock_storage.update_subscription = AsyncMock(return_value=True)
            mock_storage.get_subscription = AsyncMock(return_value=deactivated_sub)

            response = client.post(
                "/webhooks/sub-001/deactivate",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_activate_nonexistent_returns_404(
        self, client, mock_webhook_deps
    ):
        """Activating a non-existent subscription returns 404."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(return_value=None)

            response = client.post(
                "/webhooks/sub-nonexistent/activate",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 404

    def test_deactivate_nonexistent_returns_404(
        self, client, mock_webhook_deps
    ):
        """Deactivating a non-existent subscription returns 404."""
        with patch(
            "app.routes.webhooks.webhook_storage"
        ) as mock_storage:
            mock_storage.get_subscription_if_owned = AsyncMock(return_value=None)

            response = client.post(
                "/webhooks/sub-nonexistent/deactivate",
                headers={"X-API-Key": "test-key"},
            )

        assert response.status_code == 404
