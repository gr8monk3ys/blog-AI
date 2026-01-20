"""
Integration tests for health check endpoints.

Tests cover main health check, liveness probe, readiness probe,
and root endpoint.
"""

import os
import unittest
from unittest.mock import patch

# Set test environment before importing app modules
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_health.db"

from fastapi.testclient import TestClient


def setup_test_db():
    """Initialize a fresh test database."""
    from app.db.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestHealthCheck(unittest.TestCase):
    """Tests for the /health endpoint."""

    def setUp(self):
        """Set up test client."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

    def test_health_check_returns_200(self):
        """Health check should return 200 status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_health_check_contains_required_fields(self):
        """Health check should contain status, timestamp, version, checks."""
        response = self.client.get("/health")
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertIn("version", data)
        self.assertIn("checks", data)

    def test_health_check_database_status(self):
        """Health check should include database status."""
        response = self.client.get("/health")
        data = response.json()
        self.assertIn("database", data["checks"])
        db_status = data["checks"]["database"]
        self.assertIn("status", db_status)
        # With in-memory SQLite, should be healthy
        self.assertEqual(db_status["status"], "healthy")

    def test_health_check_database_latency(self):
        """Health check should report database latency."""
        response = self.client.get("/health")
        data = response.json()
        db_status = data["checks"]["database"]
        # Latency should be present for healthy database
        if db_status["status"] == "healthy":
            self.assertIn("latency_ms", db_status)
            self.assertIsInstance(db_status["latency_ms"], (int, float))

    def test_health_check_llm_config_status(self):
        """Health check should include LLM config status."""
        response = self.client.get("/health")
        data = response.json()
        self.assertIn("llm_config", data["checks"])
        llm_status = data["checks"]["llm_config"]
        self.assertIn("status", llm_status)

    def test_health_check_timestamp_format(self):
        """Health check timestamp should be ISO format with Z suffix."""
        response = self.client.get("/health")
        data = response.json()
        timestamp = data["timestamp"]
        self.assertTrue(timestamp.endswith("Z"))
        # Should be parseable as ISO datetime
        from datetime import datetime

        # Remove Z and parse
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_health_check_version(self):
        """Health check should return version string."""
        response = self.client.get("/health")
        data = response.json()
        self.assertEqual(data["version"], "1.0.0")


class TestHealthCheckWithLLMKeys(unittest.TestCase):
    """Tests for health check with various LLM API key configurations."""

    def setUp(self):
        """Set up test client."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

    def test_health_with_openai_key(self):
        """Health check with OpenAI key configured."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            response = self.client.get("/health")
            data = response.json()
            llm_status = data["checks"]["llm_config"]
            self.assertEqual(llm_status["status"], "healthy")
            self.assertIn("openai", llm_status["message"])

    def test_health_with_anthropic_key(self):
        """Health check with Anthropic key configured."""
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "test-key", "OPENAI_API_KEY": ""},
            clear=False,
        ):
            response = self.client.get("/health")
            data = response.json()
            llm_status = data["checks"]["llm_config"]
            # Status depends on whether any key is configured
            if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
                self.assertIn(llm_status["status"], ["healthy", "degraded"])

    def test_health_with_no_llm_keys(self):
        """Health check with no LLM keys configured."""
        # Clear all LLM keys
        env_patch = {
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "GEMINI_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            response = self.client.get("/health")
            data = response.json()
            llm_status = data["checks"]["llm_config"]
            self.assertEqual(llm_status["status"], "degraded")
            self.assertIn("No LLM API keys", llm_status["message"])


class TestLivenessProbe(unittest.TestCase):
    """Tests for the /health/live endpoint (Kubernetes liveness probe)."""

    def setUp(self):
        """Set up test client."""
        from server import app

        self.client = TestClient(app)

    def test_liveness_returns_200(self):
        """Liveness probe should always return 200 if app is running."""
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)

    def test_liveness_returns_alive_status(self):
        """Liveness probe should return alive status."""
        response = self.client.get("/health/live")
        data = response.json()
        self.assertEqual(data["status"], "alive")


class TestReadinessProbe(unittest.TestCase):
    """Tests for the /health/ready endpoint (Kubernetes readiness probe)."""

    def setUp(self):
        """Set up test client."""
        setup_test_db()

        from server import app

        self.client = TestClient(app)

    def test_readiness_returns_200_when_healthy(self):
        """Readiness probe should return 200 when database is healthy."""
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)

    def test_readiness_returns_ready_status(self):
        """Readiness probe should return ready status."""
        response = self.client.get("/health/ready")
        data = response.json()
        self.assertEqual(data["status"], "ready")

    def test_readiness_returns_503_when_db_unavailable(self):
        """Readiness probe should return 503 when database is unavailable."""
        from app.routes.health import check_database

        # Mock database check to return unhealthy
        with patch("app.routes.health.check_database") as mock_check:
            from app.routes.health import ServiceStatus

            mock_check.return_value = ServiceStatus(
                status="unhealthy", message="Database connection failed"
            )
            response = self.client.get("/health/ready")
            self.assertEqual(response.status_code, 503)


class TestRootEndpoint(unittest.TestCase):
    """Tests for the root endpoint /."""

    def setUp(self):
        """Set up test client."""
        from server import app

        self.client = TestClient(app)

    def test_root_returns_200(self):
        """Root endpoint should return 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_root_contains_welcome_message(self):
        """Root endpoint should contain welcome message."""
        response = self.client.get("/")
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Blog AI", data["message"])

    def test_root_contains_version(self):
        """Root endpoint should contain version."""
        response = self.client.get("/")
        data = response.json()
        self.assertIn("version", data)
        self.assertEqual(data["version"], "1.0.0")

    def test_root_contains_api_info(self):
        """Root endpoint should contain API information."""
        response = self.client.get("/")
        data = response.json()
        self.assertIn("api_version", data)
        self.assertIn("docs", data)
        self.assertIn("health", data)
        self.assertIn("api_base", data)

    def test_root_api_base_is_v1(self):
        """Root endpoint should indicate v1 API base."""
        response = self.client.get("/")
        data = response.json()
        self.assertEqual(data["api_base"], "/api/v1")


if __name__ == "__main__":
    unittest.main()
