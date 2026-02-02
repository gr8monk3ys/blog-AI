"""
Tests for brand voice training endpoints.

Tests the /brand-voice/analyze, /brand-voice/samples, /brand-voice/train,
and /brand-voice/score endpoints.
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


class TestAnalyzeSampleValidation(unittest.TestCase):
    """Tests for /brand-voice/analyze endpoint validation."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        # Don't raise server exceptions so we can check status codes
        self.client = TestClient(app, raise_server_exceptions=False)
        self.valid_content = "This is a sample piece of content that needs to be at least 50 characters long for the brand voice analysis to work properly."

    def test_analyze_content_too_short_returns_422(self):
        """Content less than 50 chars should return 422."""
        response = self.client.post(
            "/brand-voice/analyze",
            json={
                "content": "Too short",
                "content_type": "text",
                "provider": "openai",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_invalid_provider_returns_422(self):
        """Invalid provider should return 422."""
        response = self.client.post(
            "/brand-voice/analyze",
            json={
                "content": self.valid_content,
                "content_type": "text",
                "provider": "invalid_provider",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_valid_provider_openai(self):
        """Valid openai provider should not return 422 validation error."""
        response = self.client.post(
            "/brand-voice/analyze",
            json={
                "content": self.valid_content,
                "content_type": "text",
                "provider": "openai",
            },
        )
        # Should not be a 422 validation error (may be 400/500 without real API key)
        self.assertNotEqual(response.status_code, 422)


class TestAddSampleValidation(unittest.TestCase):
    """Tests for /brand-voice/samples endpoint validation."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_content = "This is sample content that needs to be at least 50 characters long for brand voice training."
        self.valid_profile_id = "test-profile-123"

    def test_add_sample_invalid_profile_id_returns_422(self):
        """Invalid profile ID should return 422."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": "invalid/profile!@#",
                "content": self.valid_content,
                "content_type": "text",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_add_sample_content_too_short_returns_422(self):
        """Content less than 50 chars should return 422."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": self.valid_profile_id,
                "content": "Too short",
                "content_type": "text",
            },
        )
        self.assertEqual(response.status_code, 422)


class TestSampleSourceURLValidation(unittest.TestCase):
    """Tests for source URL SSRF protection."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_content = "This is sample content that needs to be at least 50 characters long for testing."
        self.valid_profile_id = "test-profile"

    def test_valid_https_url_accepted(self):
        """Valid HTTPS URLs should be accepted."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": self.valid_profile_id,
                "content": self.valid_content,
                "source_url": "https://example.com/article",
            },
        )
        # Should not be validation error for URL
        # (may fail for other reasons like auth)
        if response.status_code == 422:
            data = response.json()
            # Check that the error is not about source_url
            error_fields = [e.get("loc", [])[-1] for e in data.get("detail", [])]
            self.assertNotIn("source_url", error_fields)

    def test_localhost_url_rejected(self):
        """Localhost URLs should be rejected for SSRF protection."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": self.valid_profile_id,
                "content": self.valid_content,
                "source_url": "http://localhost/secret",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_metadata_endpoint_rejected(self):
        """Cloud metadata endpoints should be rejected."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": self.valid_profile_id,
                "content": self.valid_content,
                "source_url": "http://169.254.169.254/latest/meta-data/",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_ftp_scheme_rejected(self):
        """FTP scheme should be rejected."""
        response = self.client.post(
            "/brand-voice/samples",
            json={
                "profile_id": self.valid_profile_id,
                "content": self.valid_content,
                "source_url": "ftp://example.com/file",
            },
        )
        self.assertEqual(response.status_code, 422)


class TestContentSanitization(unittest.TestCase):
    """Tests for content HTML sanitization."""

    def setUp(self):
        """Set up test client."""
        from server import app
        # Don't raise server exceptions so we can check status codes
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_script_tags_removed_in_validation(self):
        """Script tags should be sanitized during validation, not cause 422."""
        malicious_content = """
        This is legitimate content that is at least 50 characters.
        <script>alert('xss')</script>
        More content here to meet the minimum length requirement.
        """
        response = self.client.post(
            "/brand-voice/analyze",
            json={
                "content": malicious_content,
                "content_type": "text",
                "provider": "openai",
            },
        )
        # Should NOT be a 422 validation error (script tags stripped by bleach)
        # May fail with 400/500 if no real API key
        self.assertNotEqual(response.status_code, 422)


class TestScoreContentValidation(unittest.TestCase):
    """Tests for /brand-voice/score endpoint validation."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)
        self.valid_content = "This is content to score against a brand voice profile. It should be at least 50 characters."

    def test_score_content_too_short_returns_422(self):
        """Content less than 50 chars should return 422."""
        response = self.client.post(
            "/brand-voice/score",
            json={
                "profile_id": "test-profile",
                "content": "Too short",
            },
        )
        self.assertEqual(response.status_code, 422)


class TestSamplesEndpoint(unittest.TestCase):
    """Tests for /brand-voice/samples endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_get_samples_method_not_allowed(self):
        """GET method should not be allowed on /brand-voice/samples."""
        response = self.client.get("/brand-voice/samples")
        # /brand-voice/samples is POST only
        self.assertEqual(response.status_code, 405)


class TestDeleteSampleEndpoint(unittest.TestCase):
    """Tests for DELETE /brand-voice/samples/{sample_id} endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_delete_samples_method_not_allowed(self):
        """DELETE method on /brand-voice/samples/{id} returns 405."""
        response = self.client.delete("/brand-voice/samples/nonexistent-sample-id")
        # DELETE is not implemented on this endpoint
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
