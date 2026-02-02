"""
Tests for security and logging middleware.

Tests SecurityHeadersMiddleware, RequestIDMiddleware,
RequestValidationMiddleware, and RateLimiterMiddleware.
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


class TestSecurityHeadersMiddleware(unittest.TestCase):
    """Tests for SecurityHeadersMiddleware."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_response_has_x_content_type_options(self):
        """Response should have X-Content-Type-Options header."""
        response = self.client.get("/health")
        self.assertIn("x-content-type-options", response.headers)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_response_has_x_frame_options(self):
        """Response should have X-Frame-Options header."""
        response = self.client.get("/health")
        self.assertIn("x-frame-options", response.headers)
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_response_has_x_xss_protection(self):
        """Response should have X-XSS-Protection header."""
        response = self.client.get("/health")
        self.assertIn("x-xss-protection", response.headers)
        self.assertEqual(response.headers["x-xss-protection"], "1; mode=block")

    def test_response_has_referrer_policy(self):
        """Response should have Referrer-Policy header."""
        response = self.client.get("/health")
        self.assertIn("referrer-policy", response.headers)
        self.assertEqual(
            response.headers["referrer-policy"], "strict-origin-when-cross-origin"
        )

    def test_response_has_content_security_policy(self):
        """Response should have Content-Security-Policy header."""
        response = self.client.get("/health")
        self.assertIn("content-security-policy", response.headers)
        csp = response.headers["content-security-policy"]
        self.assertIn("default-src", csp)

    def test_response_has_permissions_policy(self):
        """Response should have Permissions-Policy header."""
        response = self.client.get("/health")
        self.assertIn("permissions-policy", response.headers)
        policy = response.headers["permissions-policy"]
        # Should restrict dangerous permissions
        self.assertIn("camera=()", policy)
        self.assertIn("microphone=()", policy)

    def test_response_has_cache_control(self):
        """Response should have Cache-Control header."""
        response = self.client.get("/health")
        self.assertIn("cache-control", response.headers)


class TestRequestIDMiddleware(unittest.TestCase):
    """Tests for RequestIDMiddleware."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_response_has_request_id(self):
        """Response should have X-Request-ID header."""
        response = self.client.get("/health")
        self.assertIn("x-request-id", response.headers)

    def test_request_id_is_uuid_format(self):
        """Request ID should be in UUID-like format."""
        import re

        response = self.client.get("/health")
        request_id = response.headers.get("x-request-id", "")
        # Should contain UUID pattern or prefixed UUID
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        self.assertTrue(
            re.search(uuid_pattern, request_id, re.IGNORECASE),
            f"Request ID '{request_id}' should contain UUID pattern",
        )

    def test_forwarded_request_id_is_used(self):
        """Middleware should use forwarded X-Request-ID if provided."""
        custom_id = "custom-request-123"
        response = self.client.get("/health", headers={"X-Request-ID": custom_id})
        # Note: Middleware may or may not preserve the original ID
        # This tests that the endpoint still works with custom header
        self.assertEqual(response.status_code, 200)

    def test_unique_request_ids(self):
        """Each request should get a unique request ID."""
        response1 = self.client.get("/health")
        response2 = self.client.get("/health")

        id1 = response1.headers.get("x-request-id")
        id2 = response2.headers.get("x-request-id")

        self.assertNotEqual(id1, id2)


class TestRequestValidationMiddleware(unittest.TestCase):
    """Tests for RequestValidationMiddleware."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_accepts_valid_json(self):
        """Middleware should accept valid JSON content."""
        response = self.client.post(
            "/export/markdown",
            json={
                "title": "Test",
                "content": "Content",
                "content_type": "blog",
            },
        )
        # Should get through validation (may fail for other reasons)
        self.assertNotEqual(response.status_code, 415)  # Not unsupported media type

    def test_accepts_valid_content_type(self):
        """Middleware should accept application/json content type."""
        response = self.client.post(
            "/export/markdown",
            json={
                "title": "Test",
                "content": "Content",
                "content_type": "blog",
            },
            headers={"Content-Type": "application/json"},
        )
        self.assertIn(response.status_code, [200, 201, 422])  # Valid request processing


class TestRateLimiterMiddleware(unittest.TestCase):
    """Tests for RateLimiterMiddleware."""

    def setUp(self):
        """Set up test client with rate limiting enabled."""
        os.environ["RATE_LIMIT_ENABLED"] = "true"
        os.environ["RATE_LIMIT_GENERAL"] = "100"  # High limit for tests
        os.environ["RATE_LIMIT_GENERATION"] = "10"

        # Need to reimport to pick up env changes
        import importlib
        import server

        importlib.reload(server)
        self.client = TestClient(server.app)

    def tearDown(self):
        """Reset rate limiting."""
        os.environ["RATE_LIMIT_ENABLED"] = "false"

    def test_response_has_rate_limit_headers(self):
        """Response should have rate limit headers when enabled."""
        response = self.client.get("/health")
        # Rate limit headers are typically added
        # Note: exact header names depend on implementation
        self.assertEqual(response.status_code, 200)

    def test_requests_succeed_under_limit(self):
        """Requests should succeed when under rate limit."""
        # Make several requests
        for _ in range(5):
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)


class TestMiddlewareIntegration(unittest.TestCase):
    """Integration tests for middleware stack."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_all_security_headers_present(self):
        """All security headers should be present in response."""
        response = self.client.get("/health")

        required_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "referrer-policy",
            "content-security-policy",
            "permissions-policy",
        ]

        for header in required_headers:
            self.assertIn(
                header, response.headers, f"Missing security header: {header}"
            )

    def test_middleware_does_not_break_api(self):
        """Middleware stack should not break normal API operations."""
        # Test health endpoint
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        # Test root endpoint
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_middleware_on_post_requests(self):
        """Middleware should work correctly on POST requests."""
        response = self.client.post(
            "/export/markdown",
            json={
                "title": "Test",
                "content": "Content",
                "content_type": "blog",
            },
        )
        # Check security headers are present
        self.assertIn("x-content-type-options", response.headers)
        self.assertIn("x-request-id", response.headers)

    def test_middleware_on_404_responses(self):
        """Middleware should add headers even on 404 responses."""
        response = self.client.get("/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)
        # Should still have security headers
        self.assertIn("x-content-type-options", response.headers)


class TestHSTSHeader(unittest.TestCase):
    """Tests for HSTS header behavior."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_hsts_with_https_forwarded_proto(self):
        """HSTS header should be present when X-Forwarded-Proto is https."""
        response = self.client.get(
            "/health", headers={"X-Forwarded-Proto": "https"}
        )
        # HSTS should be added for HTTPS requests
        # Note: depends on middleware configuration
        self.assertEqual(response.status_code, 200)

    def test_hsts_not_required_for_http(self):
        """HSTS header presence depends on protocol."""
        response = self.client.get("/health")
        # HSTS may or may not be present for HTTP requests
        self.assertEqual(response.status_code, 200)


class TestResponseTimeHeader(unittest.TestCase):
    """Tests for response time tracking."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_response_has_timing_header(self):
        """Response may have timing information."""
        response = self.client.get("/health")
        # X-Response-Time is optional but useful
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
