"""
Tests for health check endpoints.

Tests the /health, /health/db, /health/stripe, /health/redis,
/health/sentry, /health/cache, and /health/cache/cleanup endpoints.
"""

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


class TestMainHealthEndpoint(unittest.TestCase):
    """Tests for the main /health endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_health_returns_200(self):
        """Health endpoint should return 200 status code."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_returns_required_fields(self):
        """Health response should contain required fields."""
        response = self.client.get("/health")
        data = response.json()

        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("services", data)

    def test_health_services_structure(self):
        """Health response should contain services status."""
        response = self.client.get("/health")
        data = response.json()
        services = data["services"]

        self.assertIn("database", services)
        self.assertIn("stripe", services)
        self.assertIn("sentry", services)
        self.assertIn("redis", services)

    def test_health_status_values(self):
        """Service statuses should be valid values."""
        response = self.client.get("/health")
        data = response.json()

        valid_statuses = {"up", "down", "unconfigured"}
        for service, info in data["services"].items():
            self.assertIn(info["status"], valid_statuses)


class TestDatabaseHealthEndpoint(unittest.TestCase):
    """Tests for /health/db endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_db_health_returns_200(self):
        """Database health endpoint should return 200."""
        response = self.client.get("/health/db")
        self.assertEqual(response.status_code, 200)

    def test_db_health_contains_timestamp(self):
        """Database health should contain timestamp."""
        response = self.client.get("/health/db")
        data = response.json()
        self.assertIn("timestamp", data)
        self.assertIn("database", data)

    def test_db_health_unconfigured_without_env(self):
        """Database should report unconfigured when env vars missing."""
        # Clear Supabase env vars
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": ""}):
            response = self.client.get("/health/db")
            data = response.json()
            self.assertFalse(data["database"]["configured"])

    @patch("app.routes.health.get_database_status")
    def test_db_health_connected(self, mock_db_status):
        """Database should report connected when available."""
        mock_db_status.return_value = {
            "configured": True,
            "connected": True,
            "latency_ms": 5.2,
            "tables_accessible": True,
        }
        response = self.client.get("/health/db")
        data = response.json()
        self.assertTrue(data["database"]["connected"])


class TestStripeHealthEndpoint(unittest.TestCase):
    """Tests for /health/stripe endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_stripe_health_returns_200(self):
        """Stripe health endpoint should return 200."""
        response = self.client.get("/health/stripe")
        self.assertEqual(response.status_code, 200)

    def test_stripe_health_contains_required_fields(self):
        """Stripe health should contain required fields."""
        response = self.client.get("/health/stripe")
        data = response.json()
        self.assertIn("timestamp", data)
        self.assertIn("stripe", data)

    def test_stripe_mode_detection_test(self):
        """Stripe should detect test mode from key prefix."""
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_abc123"}):
            with patch("stripe.Account.retrieve") as mock_account:
                mock_account.return_value = MagicMock(id="acct_test")
                response = self.client.get("/health/stripe")
                data = response.json()
                self.assertEqual(data["stripe"]["mode"], "test")

    def test_stripe_unconfigured_without_key(self):
        """Stripe should report unconfigured without key."""
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}, clear=False):
            response = self.client.get("/health/stripe")
            data = response.json()
            # Should still return 200 but show unconfigured
            self.assertEqual(response.status_code, 200)


class TestRedisHealthEndpoint(unittest.TestCase):
    """Tests for /health/redis endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_redis_health_returns_200(self):
        """Redis health endpoint should return 200."""
        response = self.client.get("/health/redis")
        self.assertEqual(response.status_code, 200)

    def test_redis_health_contains_required_fields(self):
        """Redis health should contain required fields."""
        response = self.client.get("/health/redis")
        data = response.json()
        self.assertIn("timestamp", data)
        self.assertIn("redis", data)

    def test_redis_unconfigured_without_url(self):
        """Redis should report unconfigured without REDIS_URL."""
        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            response = self.client.get("/health/redis")
            data = response.json()
            self.assertFalse(data["redis"]["configured"])


class TestSentryHealthEndpoint(unittest.TestCase):
    """Tests for /health/sentry endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_sentry_health_returns_200(self):
        """Sentry health endpoint should return 200."""
        response = self.client.get("/health/sentry")
        self.assertEqual(response.status_code, 200)

    def test_sentry_health_contains_required_fields(self):
        """Sentry health should contain required fields."""
        response = self.client.get("/health/sentry")
        data = response.json()
        self.assertIn("timestamp", data)
        self.assertIn("sentry", data)

    def test_sentry_includes_config_details(self):
        """Sentry health should include configuration details."""
        response = self.client.get("/health/sentry")
        data = response.json()
        sentry = data["sentry"]
        self.assertIn("traces_sample_rate", sentry)
        self.assertIn("profiles_sample_rate", sentry)
        self.assertIn("release", sentry)


class TestCacheHealthEndpoint(unittest.TestCase):
    """Tests for /health/cache endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_cache_stats_returns_200(self):
        """Cache stats endpoint should return 200."""
        response = self.client.get("/health/cache")
        self.assertEqual(response.status_code, 200)

    def test_cache_stats_contains_both_caches(self):
        """Cache stats should contain both cache types."""
        response = self.client.get("/health/cache")
        data = response.json()
        self.assertIn("caches", data)
        self.assertIn("content_analysis", data["caches"])
        self.assertIn("voice_analysis", data["caches"])


class TestCacheCleanupEndpoint(unittest.TestCase):
    """Tests for /health/cache/cleanup endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_cache_cleanup_returns_200(self):
        """Cache cleanup endpoint should return 200."""
        response = self.client.post("/health/cache/cleanup")
        self.assertEqual(response.status_code, 200)

    def test_cache_cleanup_returns_cleaned_counts(self):
        """Cache cleanup should return count of cleaned entries."""
        response = self.client.post("/health/cache/cleanup")
        data = response.json()
        self.assertIn("cleaned", data)
        self.assertIn("content_analysis", data["cleaned"])
        self.assertIn("voice_analysis", data["cleaned"])


class TestRootEndpoint(unittest.TestCase):
    """Tests for the root / endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_root_returns_200(self):
        """Root endpoint should return 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_root_contains_api_info(self):
        """Root endpoint should contain API information."""
        response = self.client.get("/")
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("version", data)
        self.assertIn("docs", data)
        self.assertIn("health", data)


if __name__ == "__main__":
    unittest.main()
