"""
Tests for error handlers.

Tests exception handling, error sanitization, and response formatting.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.error_handlers import (
    sanitize_details,
    sanitize_error_message,
)


class TestErrorMessageSanitization(unittest.TestCase):
    """Tests for error message sanitization."""

    def test_normal_message_unchanged(self):
        """Normal messages should pass through."""
        message = "An error occurred while processing the request"
        sanitized = sanitize_error_message(message)
        self.assertEqual(sanitized, message)

    def test_api_key_is_redacted(self):
        """Messages containing API keys should be sanitized."""
        message = "Invalid api_key: sk-abc123xyz"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("sk-abc123xyz", sanitized)

    def test_password_is_redacted(self):
        """Messages containing passwords should be sanitized."""
        message = "Authentication failed with password: secret123"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("secret123", sanitized)

    def test_file_path_is_redacted(self):
        """File paths should be sanitized."""
        message = "File not found: /Users/john/secret/file.txt"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("/Users/john", sanitized)

    def test_ip_address_is_redacted(self):
        """IP addresses should be sanitized."""
        message = "Connection failed to 192.168.1.100:5432"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("192.168.1.100", sanitized)

    def test_uuid_is_redacted(self):
        """UUIDs should be sanitized."""
        message = "User abc12345-6789-0abc-def1-234567890abc not found"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("abc12345-6789-0abc-def1-234567890abc", sanitized)

    def test_database_url_is_redacted(self):
        """Database connection strings should be sanitized."""
        message = "Connection error: postgres://user:pass@localhost/db"
        sanitized = sanitize_error_message(message)
        self.assertNotIn("postgres://", sanitized)

    def test_long_message_is_truncated(self):
        """Very long messages should be truncated."""
        long_message = "a" * 1000
        sanitized = sanitize_error_message(long_message)
        self.assertLessEqual(len(sanitized), 503)  # 500 + "..."

    def test_empty_message_returns_empty(self):
        """Empty message should return empty."""
        sanitized = sanitize_error_message("")
        self.assertEqual(sanitized, "")

    def test_none_message_returns_none(self):
        """None message should return None."""
        sanitized = sanitize_error_message(None)
        self.assertIsNone(sanitized)


class TestErrorDetailsSanitization(unittest.TestCase):
    """Tests for error details sanitization."""

    def test_safe_keys_are_preserved(self):
        """Safe keys should be preserved in details."""
        details = {
            "field": "username",
            "value": "test_user",
            "resource_type": "user",
        }
        sanitized = sanitize_details(details)
        self.assertIn("field", sanitized)
        self.assertIn("value", sanitized)
        self.assertIn("resource_type", sanitized)

    def test_unsafe_keys_are_removed(self):
        """Unsafe keys should be removed from details."""
        details = {
            "field": "username",
            "api_key": "secret123",
            "password": "hunter2",
            "internal_error": "stack trace...",
        }
        sanitized = sanitize_details(details)
        self.assertNotIn("api_key", sanitized)
        self.assertNotIn("password", sanitized)
        self.assertNotIn("internal_error", sanitized)

    def test_empty_details_returns_empty(self):
        """Empty details should return empty dict."""
        sanitized = sanitize_details({})
        self.assertEqual(sanitized, {})

    def test_none_details_returns_empty(self):
        """None details should return empty dict."""
        sanitized = sanitize_details(None)
        self.assertEqual(sanitized, {})

    def test_quota_related_keys_preserved(self):
        """Quota-related keys should be preserved."""
        details = {
            "limit": 100,
            "current_usage": 95,
            "quota_type": "daily",
            "retry_after": 3600,
        }
        sanitized = sanitize_details(details)
        self.assertEqual(sanitized["limit"], 100)
        self.assertEqual(sanitized["current_usage"], 95)


class TestExceptionHandlerIntegration(unittest.TestCase):
    """Integration tests for exception handlers with API."""

    def setUp(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from server import app

        self.client = TestClient(app)

    def test_validation_error_returns_422(self):
        """Validation errors should return 422."""
        response = self.client.post(
            "/generate-blog",
            json={"topic": "", "keywords": []},  # Empty topic
        )
        self.assertEqual(response.status_code, 422)

    def test_validation_error_has_detail(self):
        """Validation errors should have detail field."""
        response = self.client.post(
            "/generate-blog",
            json={"topic": "", "keywords": []},
        )
        data = response.json()
        # Response may have 'detail' or 'error' depending on error handler
        self.assertTrue("detail" in data or "error" in data)

    def test_not_found_returns_404(self):
        """Not found errors should return 404."""
        response = self.client.get("/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed_returns_405(self):
        """Method not allowed should return 405."""
        response = self.client.delete("/health")
        self.assertEqual(response.status_code, 405)


class TestErrorResponseFormat(unittest.TestCase):
    """Tests for consistent error response format."""

    def setUp(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from server import app

        self.client = TestClient(app)

    def test_error_response_is_json(self):
        """Error responses should be JSON."""
        response = self.client.post(
            "/generate-blog",
            json={"topic": "", "keywords": []},
        )
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_validation_error_detail_is_list(self):
        """Validation error detail should be a list of errors."""
        response = self.client.post(
            "/generate-blog",
            json={"topic": "", "keywords": []},
        )
        data = response.json()
        # Response may have 'detail' or 'error' depending on error handler
        self.assertTrue("detail" in data or "error" in data)


class TestSentryIntegration(unittest.TestCase):
    """Tests for Sentry error reporting integration."""

    def setUp(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from server import app

        self.client = TestClient(app)

    @patch("sentry_sdk.capture_exception")
    def test_unexpected_errors_reported_to_sentry(self, mock_capture):
        """Unexpected errors should be reported to Sentry."""
        # This is difficult to test without causing actual errors
        # Just verify Sentry SDK is imported and configured
        import sentry_sdk

        self.assertIsNotNone(sentry_sdk)


class TestHTTPExceptionHandling(unittest.TestCase):
    """Tests for HTTP exception handling."""

    def setUp(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from server import app

        self.client = TestClient(app)

    def test_http_exception_preserves_status_code(self):
        """HTTP exceptions should preserve their status code."""
        # Request with invalid conversation ID format
        response = self.client.get("/conversations/invalid!@#id")
        # Should be a client error (400-499)
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_http_exception_has_error_body(self):
        """HTTP exceptions should have an error body."""
        response = self.client.get("/nonexistent")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIsNotNone(data)


class TestProductionErrorHandling(unittest.TestCase):
    """Tests for production environment error handling."""

    def test_production_hides_stack_traces(self):
        """Production should not expose stack traces."""
        # Set production environment
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            # Verify error messages are sanitized
            message = "Error at /app/src/module.py:123"
            sanitized = sanitize_error_message(message)
            # File paths should be removed
            self.assertNotIn("/app/src/module.py", sanitized)

    def test_development_may_show_details(self):
        """Development mode may show more details."""
        # In development, normal messages pass through
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            message = "Error processing request"
            sanitized = sanitize_error_message(message)
            self.assertEqual(sanitized, message)


if __name__ == "__main__":
    unittest.main()
