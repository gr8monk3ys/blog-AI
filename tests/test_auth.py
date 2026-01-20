"""
Integration tests for authentication endpoints.

Tests cover user registration, login, token refresh, profile access,
and API key management.
"""

import os
import unittest

# Set test environment before importing app modules
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from fastapi.testclient import TestClient


def setup_test_db():
    """Initialize a fresh test database."""
    from app.db.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestUserRegistration(unittest.TestCase):
    """Tests for user registration endpoint."""

    def setUp(self):
        """Set up test client with fresh database."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

    def test_register_success(self):
        """Valid registration should return user data."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["username"], "testuser")
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertTrue(data["is_active"])

    def test_register_duplicate_email(self):
        """Duplicate email should return 409 conflict."""
        # First registration
        self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser1",
                "password": "TestPass123",
            },
        )
        # Duplicate email
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser2",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("Email already registered", response.json()["detail"])

    def test_register_duplicate_username(self):
        """Duplicate username should return 409 conflict."""
        # First registration
        self.client.post(
            "/auth/register",
            json={
                "email": "test1@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        # Duplicate username
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("Username already taken", response.json()["detail"])

    def test_register_invalid_email(self):
        """Invalid email format should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_short_password(self):
        """Password under 8 characters should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "Short1",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_password_no_uppercase(self):
        """Password without uppercase should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_password_no_lowercase(self):
        """Password without lowercase should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TESTPASS123",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_password_no_digit(self):
        """Password without digit should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPassword",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_invalid_username_characters(self):
        """Username with invalid characters should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "test@user!",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_username_too_short(self):
        """Username under 3 characters should return 422."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_register_username_normalized_to_lowercase(self):
        """Username should be normalized to lowercase."""
        response = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "TestUser",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "testuser")


class TestUserLogin(unittest.TestCase):
    """Tests for user login endpoint."""

    def setUp(self):
        """Set up test client with fresh database and registered user."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

        # Register a test user
        self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )

    def test_login_success(self):
        """Valid credentials should return tokens."""
        response = self.client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("expires_in", data)

    def test_login_invalid_email(self):
        """Non-existent email should return 401."""
        response = self.client.post(
            "/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.json()["detail"])

    def test_login_invalid_password(self):
        """Wrong password should return 401."""
        response = self.client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPass123",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.json()["detail"])


class TestTokenRefresh(unittest.TestCase):
    """Tests for token refresh endpoint."""

    def setUp(self):
        """Set up test client with authenticated user."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

        # Register and login
        self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        login_response = self.client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        tokens = login_response.json()
        self.refresh_token = tokens["refresh_token"]
        self.access_token = tokens["access_token"]

    def test_refresh_token_success(self):
        """Valid refresh token should return new access token."""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_refresh_token_invalid(self):
        """Invalid refresh token should return 401."""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_with_access_token_fails(self):
        """Using access token as refresh token should fail."""
        response = self.client.post(
            "/auth/refresh",
            json={"refresh_token": self.access_token},
        )
        self.assertEqual(response.status_code, 401)


class TestUserProfile(unittest.TestCase):
    """Tests for user profile endpoint."""

    def setUp(self):
        """Set up test client with authenticated user."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

        # Register and login
        self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        login_response = self.client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.access_token = login_response.json()["access_token"]

    def test_get_profile_success(self):
        """Authenticated user should get their profile."""
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["username"], "testuser")
        self.assertTrue(data["is_active"])

    def test_get_profile_no_token(self):
        """Missing token should return 401."""
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_get_profile_invalid_token(self):
        """Invalid token should return 401."""
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_get_profile_malformed_header(self):
        """Malformed auth header should return 401."""
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer token"},
        )
        self.assertEqual(response.status_code, 401)


class TestAPIKeyManagement(unittest.TestCase):
    """Tests for API key management endpoints."""

    def setUp(self):
        """Set up test client with authenticated user."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

        # Register and login
        self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        login_response = self.client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.access_token = login_response.json()["access_token"]

    def test_create_api_key_success(self):
        """Authenticated user should be able to create API key."""
        response = self.client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"name": "Test Key"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key", data)
        self.assertEqual(data["name"], "Test Key")
        self.assertIn("created_at", data)
        self.assertIn("message", data)
        # Key should be a URL-safe base64 string (32 bytes = ~43 chars)
        self.assertGreater(len(data["key"]), 30)

    def test_create_api_key_without_name(self):
        """API key can be created without a name."""
        response = self.client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("key", data)
        self.assertIsNone(data["name"])

    def test_create_api_key_no_auth(self):
        """Creating API key without auth should return 401."""
        response = self.client.post(
            "/auth/api-keys",
            json={"name": "Test Key"},
        )
        self.assertEqual(response.status_code, 401)

    def test_revoke_api_key_success(self):
        """User should be able to revoke their own API key."""
        # Create a key first
        create_response = self.client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"name": "Test Key"},
        )
        # Get key ID from database (since we don't return it in response)
        from app.db import get_db, APIKey

        db = next(get_db())
        api_key = db.query(APIKey).first()
        key_id = api_key.id

        # Revoke it
        response = self.client.delete(
            f"/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(response.status_code, 204)

    def test_revoke_nonexistent_api_key(self):
        """Revoking non-existent key should return 404."""
        response = self.client.delete(
            "/auth/api-keys/nonexistent-id",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        self.assertEqual(response.status_code, 404)


class TestVersionedAuthEndpoints(unittest.TestCase):
    """Tests for versioned auth endpoints (/api/v1/auth/*)."""

    def setUp(self):
        """Set up test client with fresh database."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

    def test_v1_register(self):
        """Versioned register endpoint should work."""
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_v1_login(self):
        """Versioned login endpoint should work."""
        # Register first
        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
            },
        )
        # Login
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())


if __name__ == "__main__":
    unittest.main()
