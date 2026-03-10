"""
Tests for the SEO module.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.seo.meta_description import (
    MetaDescriptionError,
    generate_meta_description,
)
from src.types.seo import MetaDescription


class TestMetaDescription(unittest.TestCase):
    """Tests for the meta description generation module."""

    def setUp(self):
        """Set up test fixtures."""
        self.title = "How AI is Changing Content Creation"
        self.keywords = ["AI", "content creation", "machine learning"]
        self.content = "This is a sample blog post about AI and content creation."

    @patch("src.seo.meta_description.generate_text")
    def test_generate_meta_description(self, mock_generate_text):
        """Test the generate_meta_description function."""
        # Setup mock
        mock_generate_text.return_value = (
            "Discover how AI is revolutionizing content creation. "
            "Learn about machine learning tools that help creators."
        )

        # Create mock provider
        mock_provider = MagicMock()

        # Generate meta description
        result = generate_meta_description(
            title=self.title,
            keywords=self.keywords,
            content=self.content,
            tone="informative",
            provider=mock_provider,
        )

        # Verify results
        self.assertIsInstance(result, MetaDescription)
        self.assertIsNotNone(result.content)
        self.assertLessEqual(len(result.content), 160)
        mock_generate_text.assert_called_once()

    @patch("src.seo.meta_description.generate_text")
    def test_generate_meta_description_truncates_long_text(self, mock_generate_text):
        """Test that meta descriptions are truncated if too long."""
        # Setup mock with long text
        mock_generate_text.return_value = "x" * 200

        mock_provider = MagicMock()

        result = generate_meta_description(
            title=self.title,
            keywords=self.keywords,
            provider=mock_provider,
        )

        # Verify truncation
        self.assertLessEqual(len(result.content), 160)
        self.assertTrue(result.content.endswith("..."))

    @patch("src.seo.meta_description.generate_text")
    def test_generate_meta_description_error(self, mock_generate_text):
        """Test generate_meta_description raises error on failure."""
        mock_generate_text.side_effect = Exception("LLM error")
        mock_provider = MagicMock()

        with self.assertRaises(MetaDescriptionError):
            generate_meta_description(
                title=self.title,
                keywords=self.keywords,
                provider=mock_provider,
            )

    @patch("src.seo.meta_description.generate_text")
    def test_generate_meta_description_without_content(self, mock_generate_text):
        """Test generating meta description without content summary."""
        mock_generate_text.return_value = "A short meta description for the article."
        mock_provider = MagicMock()

        result = generate_meta_description(
            title=self.title,
            keywords=self.keywords,
            provider=mock_provider,
        )

        self.assertIsInstance(result, MetaDescription)
        self.assertIsNotNone(result.content)


class TestMetaDescriptionModel(unittest.TestCase):
    """Tests for the MetaDescription model."""

    def test_meta_description_length_calculation(self):
        """Test MetaDescription calculates length correctly."""
        content = "This is a test meta description."
        meta = MetaDescription(content=content)
        self.assertEqual(meta.length, len(content))

    def test_meta_description_empty_content(self):
        """Test MetaDescription with empty content."""
        meta = MetaDescription(content="")
        self.assertEqual(meta.length, 0)


if __name__ == "__main__":
    unittest.main()
