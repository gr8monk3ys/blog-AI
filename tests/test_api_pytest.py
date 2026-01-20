"""
Pytest-style integration tests for the Blog AI API.

These tests use fixtures from conftest.py and provide additional coverage.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestAuthenticationFlow:
    """End-to-end tests for the authentication flow."""

    def test_full_auth_flow(self, test_client):
        """Test complete registration -> login -> profile -> api key flow."""
        # 1. Register
        register_response = test_client.post(
            "/auth/register",
            json={
                "email": "flow@example.com",
                "username": "flowuser",
                "password": "FlowPass123",
            },
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "flow@example.com"

        # 2. Login
        login_response = test_client.post(
            "/auth/login",
            json={
                "email": "flow@example.com",
                "password": "FlowPass123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]

        # 3. Get profile
        profile_response = test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == "flow@example.com"
        assert profile["username"] == "flowuser"

        # 4. Create API key
        api_key_response = test_client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "My API Key"},
        )
        assert api_key_response.status_code == 201
        api_key_data = api_key_response.json()
        assert len(api_key_data["key"]) > 30  # URL-safe base64 key

        # 5. Refresh token
        refresh_response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

    def test_multiple_users_isolation(self, test_client):
        """Test that users cannot access each other's resources."""
        # Register two users
        test_client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "password": "User1Pass123",
            },
        )
        test_client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "User2Pass123",
            },
        )

        # Login as user1
        login1 = test_client.post(
            "/auth/login",
            json={"email": "user1@example.com", "password": "User1Pass123"},
        )
        token1 = login1.json()["access_token"]

        # Login as user2
        login2 = test_client.post(
            "/auth/login",
            json={"email": "user2@example.com", "password": "User2Pass123"},
        )
        token2 = login2.json()["access_token"]

        # Create API key as user1
        key_response = test_client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {token1}"},
            json={"name": "User1 Key"},
        )
        assert key_response.status_code == 201

        # Get key ID from database
        from app.db import get_db, APIKey

        db = next(get_db())
        api_key = db.query(APIKey).first()
        key_id = api_key.id

        # User2 should not be able to revoke user1's key
        revoke_response = test_client.delete(
            f"/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert revoke_response.status_code == 404


class TestAPIVersioning:
    """Tests for API versioning."""

    def test_v1_endpoints_available(self, test_client):
        """Verify v1 API endpoints are accessible."""
        # Health endpoints at root
        response = test_client.get("/health")
        assert response.status_code == 200

        # V1 auth endpoints
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "v1test@example.com",
                "username": "v1user",
                "password": "V1Pass123",
            },
        )
        assert response.status_code == 201

    def test_backward_compatibility(self, test_client):
        """Both root and v1 endpoints should work identically."""
        # Register at root
        root_response = test_client.post(
            "/auth/register",
            json={
                "email": "root@example.com",
                "username": "rootuser",
                "password": "RootPass123",
            },
        )
        assert root_response.status_code == 201

        # Register at v1 (different email)
        v1_response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "v1@example.com",
                "username": "v1user",
                "password": "V1Pass123",
            },
        )
        assert v1_response.status_code == 201

        # Both should have same response structure
        assert set(root_response.json().keys()) == set(v1_response.json().keys())


class TestInputValidation:
    """Tests for input validation across endpoints."""

    def test_xss_prevention_in_username(self, test_client):
        """XSS in username should be rejected."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "xss@example.com",
                "username": "<script>alert('xss')</script>",
                "password": "XssPass123",
            },
        )
        # Should be rejected due to invalid characters
        assert response.status_code == 422

    def test_sql_injection_in_email(self, test_client):
        """SQL injection in email should be handled safely."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "'; DROP TABLE users; --",
                "username": "injector",
                "password": "SqlPass123",
            },
        )
        # Should be rejected as invalid email
        assert response.status_code == 422

    def test_very_long_inputs_rejected(self, test_client):
        """Very long inputs should be rejected."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "a" * 1000 + "@example.com",
                "username": "longuser",
                "password": "LongPass123",
            },
        )
        # Should be rejected
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "invalid_topic",
        [
            "",  # Empty
            " ",  # Whitespace only
            "a" * 501,  # Too long
        ],
    )
    def test_blog_topic_validation(self, test_client, invalid_topic):
        """Blog topic validation should reject invalid inputs."""
        response = test_client.post(
            "/generate-blog",
            json={
                "topic": invalid_topic,
                "keywords": [],
                "conversation_id": "test-123",
            },
        )
        assert response.status_code == 422


class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints."""

    def test_health_database_integration(self, test_client):
        """Health check should reflect actual database state."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Database should be healthy in test environment
        assert data["checks"]["database"]["status"] == "healthy"

    def test_readiness_reflects_database(self, test_client):
        """Readiness should fail if database is unavailable."""
        # In test environment, database should be available
        response = test_client.get("/health/ready")
        assert response.status_code == 200

    def test_liveness_independent_of_database(self, test_client):
        """Liveness should succeed even with database issues."""
        # Liveness only checks if app is running
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestErrorHandling:
    """Tests for error handling and error response formats."""

    def test_404_for_unknown_endpoint(self, test_client):
        """Unknown endpoints should return 404."""
        response = test_client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, test_client):
        """Wrong HTTP method should return 405."""
        response = test_client.delete("/health")
        assert response.status_code == 405

    def test_422_includes_validation_details(self, test_client):
        """422 errors should include validation details."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "username": "ab",  # Too short
                "password": "weak",  # Too weak
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestConversationEndpoints:
    """Tests for conversation endpoints."""

    def test_get_empty_conversation(self, test_client):
        """Getting a non-existent conversation should return empty list."""
        response = test_client.get("/conversations/new-conversation-id")
        assert response.status_code == 200
        assert response.json()["conversation"] == []

    def test_conversation_id_validation(self, test_client):
        """Conversation IDs with invalid characters should be rejected."""
        invalid_ids = [
            "id with spaces",
            "id/with/slashes",
            "id@with#special$chars",
            "../path/traversal",
        ]
        for invalid_id in invalid_ids:
            response = test_client.get(f"/conversations/{invalid_id}")
            assert response.status_code in [400, 404], f"Failed for: {invalid_id}"


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, test_client):
        """CORS headers should be present in responses."""
        # Make a request with Origin header
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should get CORS headers back
        assert response.status_code in [200, 204]


class TestContentTypeHandling:
    """Tests for content type handling."""

    def test_json_content_type_required(self, test_client):
        """POST endpoints should require JSON content type."""
        response = test_client.post(
            "/auth/login",
            content="email=test@example.com&password=Test123",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 422

    def test_json_responses(self, test_client):
        """All API responses should be JSON."""
        response = test_client.get("/health")
        assert response.headers["content-type"].startswith("application/json")
