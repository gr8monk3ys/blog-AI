"""
Tests for export endpoints.

Tests the /export/markdown, /export/html, /export/text,
/export/wordpress, and /export/medium endpoints.
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

from fastapi.testclient import TestClient


class TestExportMarkdown(unittest.TestCase):
    """Tests for /export/markdown endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "title": "Test Blog Post",
            "content": "# Introduction\n\nThis is test content with **bold** text.",
            "content_type": "blog",
        }

    def test_export_markdown_returns_200(self):
        """Export markdown should return 200 for valid request."""
        response = self.client.post("/export/markdown", json=self.valid_request)
        self.assertEqual(response.status_code, 200)

    def test_export_markdown_content_type(self):
        """Export markdown should return text/markdown content type."""
        response = self.client.post("/export/markdown", json=self.valid_request)
        self.assertIn("text/markdown", response.headers.get("content-type", ""))

    def test_export_markdown_contains_title(self):
        """Exported markdown should contain the title."""
        response = self.client.post("/export/markdown", json=self.valid_request)
        self.assertIn("Test Blog Post", response.text)

    def test_export_markdown_missing_title_returns_422(self):
        """Missing title should return 422 validation error."""
        invalid_request = {"content": "Some content", "content_type": "blog"}
        response = self.client.post("/export/markdown", json=invalid_request)
        self.assertEqual(response.status_code, 422)

    def test_export_markdown_empty_title_returns_422(self):
        """Empty title should return 422 validation error."""
        invalid_request = {
            "title": "",
            "content": "Some content",
            "content_type": "blog",
        }
        response = self.client.post("/export/markdown", json=invalid_request)
        self.assertEqual(response.status_code, 422)

    def test_export_markdown_invalid_content_type_returns_422(self):
        """Invalid content_type should return 422 validation error."""
        invalid_request = {
            "title": "Test",
            "content": "Content",
            "content_type": "invalid",
        }
        response = self.client.post("/export/markdown", json=invalid_request)
        self.assertEqual(response.status_code, 422)


class TestExportHTML(unittest.TestCase):
    """Tests for /export/html endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "title": "Test HTML Export",
            "content": "# Heading\n\nParagraph with **bold** and *italic*.",
            "content_type": "blog",
        }

    def test_export_html_returns_200(self):
        """Export HTML should return 200 for valid request."""
        response = self.client.post("/export/html", json=self.valid_request)
        self.assertEqual(response.status_code, 200)

    def test_export_html_content_type(self):
        """Export HTML should return text/html content type."""
        response = self.client.post("/export/html", json=self.valid_request)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_export_html_contains_html_tags(self):
        """Exported HTML should contain HTML tags."""
        response = self.client.post("/export/html", json=self.valid_request)
        content = response.text
        self.assertIn("<html", content.lower())
        self.assertIn("</html>", content.lower())

    def test_export_html_sanitizes_xss_in_title(self):
        """Export HTML should sanitize potential XSS content in title."""
        malicious_request = {
            "title": "Test <script>alert('xss')</script>",
            "content": "Normal content here for testing.",
            "content_type": "blog",
        }
        response = self.client.post("/export/html", json=malicious_request)
        content = response.text
        # Title should be HTML-escaped
        self.assertNotIn("<script>alert", content)
        # Should contain escaped version
        self.assertIn("&lt;script&gt;", content)


class TestExportPlainText(unittest.TestCase):
    """Tests for /export/text endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "title": "Plain Text Export",
            "content": "# Heading\n\n**Bold** and *italic* text.",
            "content_type": "blog",
        }

    def test_export_plain_text_returns_200(self):
        """Export plain text should return 200 for valid request."""
        response = self.client.post("/export/text", json=self.valid_request)
        self.assertEqual(response.status_code, 200)

    def test_export_plain_text_content_type(self):
        """Export plain text should return text/plain content type."""
        response = self.client.post("/export/text", json=self.valid_request)
        self.assertIn("text/plain", response.headers.get("content-type", ""))

    def test_export_plain_text_strips_markdown(self):
        """Exported plain text should strip markdown formatting."""
        response = self.client.post("/export/text", json=self.valid_request)
        content = response.text
        # Should not contain markdown symbols
        self.assertNotIn("**", content)
        self.assertNotIn("# ", content)


class TestExportWordPress(unittest.TestCase):
    """Tests for /export/wordpress endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "title": "WordPress Export Test",
            "content": "# Introduction\n\nTest content for WordPress export.",
            "content_type": "blog",
        }

    def test_export_wordpress_returns_200(self):
        """Export WordPress should return 200 for valid request."""
        response = self.client.post("/export/wordpress", json=self.valid_request)
        self.assertEqual(response.status_code, 200)

    def test_export_wordpress_response_format(self):
        """WordPress export should return JSON with success and content."""
        response = self.client.post("/export/wordpress", json=self.valid_request)
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("content", data)
        self.assertIn("format", data)
        self.assertEqual(data["format"], "wordpress")


class TestExportMedium(unittest.TestCase):
    """Tests for /export/medium endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "title": "Medium Export Test",
            "content": "# My Article\n\nContent for Medium publishing.",
            "content_type": "blog",
        }

    def test_export_medium_returns_200(self):
        """Export Medium should return 200 for valid request."""
        response = self.client.post("/export/medium", json=self.valid_request)
        self.assertEqual(response.status_code, 200)

    def test_export_medium_response_format(self):
        """Medium export should return JSON with success and content."""
        response = self.client.post("/export/medium", json=self.valid_request)
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("content", data)
        self.assertIn("format", data)
        self.assertEqual(data["format"], "medium")


class TestExportWithMetadata(unittest.TestCase):
    """Tests for export endpoints with metadata."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_export_with_metadata(self):
        """Export should handle metadata correctly."""
        request_with_metadata = {
            "title": "Test with Metadata",
            "content": "Content here.",
            "content_type": "blog",
            "metadata": {
                "author": "Test Author",
                "date": "2024-01-01",
                "tags": ["test", "example"],
            },
        }
        response = self.client.post("/export/markdown", json=request_with_metadata)
        self.assertEqual(response.status_code, 200)

    def test_export_without_metadata(self):
        """Export should work without metadata."""
        request_no_metadata = {
            "title": "Test without Metadata",
            "content": "Content here.",
            "content_type": "blog",
        }
        response = self.client.post("/export/markdown", json=request_no_metadata)
        self.assertEqual(response.status_code, 200)


class TestExportContentTypes(unittest.TestCase):
    """Tests for different content_type values."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_export_blog_content_type(self):
        """Export should accept 'blog' content_type."""
        request = {
            "title": "Blog Test",
            "content": "Blog content.",
            "content_type": "blog",
        }
        response = self.client.post("/export/markdown", json=request)
        self.assertEqual(response.status_code, 200)

    def test_export_book_content_type(self):
        """Export should accept 'book' content_type."""
        request = {
            "title": "Book Test",
            "content": "Book content.",
            "content_type": "book",
        }
        response = self.client.post("/export/markdown", json=request)
        self.assertEqual(response.status_code, 200)

    def test_export_tool_content_type(self):
        """Export should accept 'tool' content_type."""
        request = {
            "title": "Tool Output",
            "content": "Tool generated content.",
            "content_type": "tool",
        }
        response = self.client.post("/export/markdown", json=request)
        self.assertEqual(response.status_code, 200)


class TestExportFilenameHeader(unittest.TestCase):
    """Tests for Content-Disposition header with filename."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_markdown_has_filename_header(self):
        """Markdown export should include Content-Disposition with filename."""
        request = {
            "title": "My Test Article",
            "content": "Content here.",
            "content_type": "blog",
        }
        response = self.client.post("/export/markdown", json=request)
        disposition = response.headers.get("content-disposition", "")
        self.assertIn("filename=", disposition)

    def test_html_has_filename_header(self):
        """HTML export should include Content-Disposition with filename."""
        request = {
            "title": "My Test Article",
            "content": "Content here.",
            "content_type": "blog",
        }
        response = self.client.post("/export/html", json=request)
        disposition = response.headers.get("content-disposition", "")
        self.assertIn("filename=", disposition)


if __name__ == "__main__":
    unittest.main()
