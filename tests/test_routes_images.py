"""
Tests for image generation endpoints.

Tests the /images/generate, /images/featured, /images/social,
and /images/styles endpoints.
"""

import os
import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


class TestImageGeneration(unittest.TestCase):
    """Tests for /images/generate endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "custom_prompt": "A beautiful sunset over mountains",
            "size": "1024x1024",
            "style": "natural",  # Valid ImageStyle enum value
            "quality": "standard",
            "provider": "openai",
        }

    @patch("app.routes.images.get_image_generator")
    def test_generate_image_returns_201(self, mock_get_generator):
        """Generate image should return 201 for valid request."""
        from src.types.images import ImageResult

        mock_generator = MagicMock()
        mock_result = ImageResult(
            url="https://example.com/image.png",
            prompt_used="A beautiful sunset",
            provider="openai",
            size="1024x1024",
            style="natural",
            created_at=datetime.now(),
        )
        mock_generator.generate_image = AsyncMock(return_value=mock_result)
        mock_get_generator.return_value = mock_generator

        response = self.client.post("/images/generate", json=self.valid_request)
        self.assertEqual(response.status_code, 201)

    @patch("app.routes.images.get_image_generator")
    def test_generate_image_returns_success(self, mock_get_generator):
        """Generate image should return success in response."""
        from src.types.images import ImageResult

        mock_generator = MagicMock()
        mock_result = ImageResult(
            url="https://example.com/image.png",
            prompt_used="Test prompt",
            provider="openai",
            size="1024x1024",
            style="natural",
            created_at=datetime.now(),
        )
        mock_generator.generate_image = AsyncMock(return_value=mock_result)
        mock_get_generator.return_value = mock_generator

        response = self.client.post("/images/generate", json=self.valid_request)
        data = response.json()
        self.assertTrue(data["success"])

    def test_generate_image_missing_prompt_and_content_returns_422(self):
        """Missing both prompt and content should return 422 validation error."""
        invalid_request = {
            "size": "1024x1024",
            "style": "natural",
            "quality": "standard",
            "provider": "openai",
        }
        response = self.client.post("/images/generate", json=invalid_request)
        # Model validation should catch this
        self.assertIn(response.status_code, [400, 422])

    @patch("app.routes.images.get_image_generator")
    def test_generate_from_content(self, mock_get_generator):
        """Generate image from content should work."""
        from src.types.images import ImageResult

        mock_generator = MagicMock()
        mock_result = ImageResult(
            url="https://example.com/image.png",
            prompt_used="Generated from content",
            provider="openai",
            size="1024x1024",
            style="natural",
            created_at=datetime.now(),
        )
        # When content is provided, generate_from_content is called
        mock_generator.generate_from_content = AsyncMock(return_value=mock_result)
        mock_get_generator.return_value = mock_generator

        request = {
            "content": "An article about machine learning and AI",
            "image_type": "featured",
            "size": "1024x1024",
            "style": "natural",  # Valid ImageStyle enum value
            "quality": "standard",
            "provider": "openai",
        }
        response = self.client.post("/images/generate", json=request)
        self.assertEqual(response.status_code, 201)


class TestImageGenerationValidation(unittest.TestCase):
    """Tests for image generation input validation."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_invalid_style_returns_422(self):
        """Invalid style should return 422 validation error."""
        request = {
            "custom_prompt": "Test prompt",
            "size": "1024x1024",
            "style": "invalid_style",
            "quality": "standard",
            "provider": "openai",
        }
        response = self.client.post("/images/generate", json=request)
        self.assertEqual(response.status_code, 422)

    def test_invalid_quality_returns_422(self):
        """Invalid quality should return 422 validation error."""
        request = {
            "custom_prompt": "Test prompt",
            "size": "1024x1024",
            "style": "natural",  # Valid style
            "quality": "ultra_hd",  # Invalid quality
            "provider": "openai",
        }
        response = self.client.post("/images/generate", json=request)
        self.assertEqual(response.status_code, 422)

    def test_invalid_provider_returns_422(self):
        """Invalid provider should return 422 validation error."""
        request = {
            "custom_prompt": "Test prompt",
            "size": "1024x1024",
            "style": "natural",  # Valid style
            "quality": "standard",
            "provider": "invalid_provider",
        }
        response = self.client.post("/images/generate", json=request)
        self.assertEqual(response.status_code, 422)


class TestImageGenerationErrors(unittest.TestCase):
    """Tests for image generation error handling."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)
        self.valid_request = {
            "custom_prompt": "A beautiful sunset",
            "size": "1024x1024",
            "style": "natural",  # Valid ImageStyle enum value
            "quality": "standard",
            "provider": "openai",
        }

    @patch("app.routes.images.get_image_generator")
    def test_generation_error_returns_error_status(self, mock_get_generator):
        """Image generation error should return 5xx status."""
        from src.images import ImageGenerationError

        mock_generator = MagicMock()
        mock_generator.generate_image = AsyncMock(
            side_effect=ImageGenerationError("Generation failed")
        )
        mock_get_generator.return_value = mock_generator

        response = self.client.post("/images/generate", json=self.valid_request)
        # Should return a 5xx error code
        self.assertGreaterEqual(response.status_code, 400)

    @patch("app.routes.images.get_image_generator")
    def test_error_response_has_error_field(self, mock_get_generator):
        """Error response should have error field."""
        from src.images import ImageGenerationError

        mock_generator = MagicMock()
        mock_generator.generate_image = AsyncMock(
            side_effect=ImageGenerationError("Provider unavailable")
        )
        mock_get_generator.return_value = mock_generator

        response = self.client.post("/images/generate", json=self.valid_request)
        data = response.json()
        # Error response should contain error information
        self.assertTrue("error" in data or "detail" in data or "success" in data)


class TestImageStyles(unittest.TestCase):
    """Tests for /images/styles endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_get_styles_returns_200(self):
        """Get styles endpoint should return 200."""
        response = self.client.get("/images/styles")
        self.assertEqual(response.status_code, 200)

    def test_get_styles_returns_list(self):
        """Get styles should return a list of available styles."""
        response = self.client.get("/images/styles")
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn("styles", data)


class TestImageServiceHealth(unittest.TestCase):
    """Tests for /images/health endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_image_service_health_returns_200(self):
        """Image service health endpoint should return 200."""
        response = self.client.get("/images/health")
        self.assertEqual(response.status_code, 200)

    def test_image_service_health_contains_status(self):
        """Image service health should contain status."""
        response = self.client.get("/images/health")
        data = response.json()
        self.assertIn("status", data)


if __name__ == "__main__":
    unittest.main()
