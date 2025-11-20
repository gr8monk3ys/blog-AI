"""
Tests for the post-processing module.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.post_processing.proofreader import (
    ProofreadingError,
    proofread_content,
)
from src.post_processing.humanizer import (
    HumanizationError,
    humanize_content,
)
from src.types.post_processing import (
    ProofreadingOptions,
    ProofreadingResult,
    HumanizationOptions,
)


class TestProofreader(unittest.TestCase):
    """Tests for the proofreading module."""

    def setUp(self):
        """Set up test fixtures."""
        self.content = """
        This is a sample blog post about artificial intelligence.
        It contains some text that may have grammer issues.
        """

    @patch("src.post_processing.proofreader.generate_text")
    def test_proofread_content(self, mock_generate_text):
        """Test the proofread_content function."""
        # Setup mock
        mock_generate_text.return_value = """
        {
            "corrected_content": "This is a sample blog post about artificial intelligence. It contains some text that may have grammar issues.",
            "issues": [
                {
                    "type": "spelling",
                    "original": "grammer",
                    "suggestion": "grammar",
                    "position": {"line": 3, "character": 45}
                }
            ]
        }
        """

        mock_provider = MagicMock()
        options = ProofreadingOptions(
            check_grammar=True,
            check_spelling=True,
            check_style=False,
            check_plagiarism=False,
        )

        result = proofread_content(
            content=self.content,
            options=options,
            provider=mock_provider,
        )

        self.assertIsInstance(result, ProofreadingResult)
        mock_generate_text.assert_called_once()

    @patch("src.post_processing.proofreader.generate_text")
    def test_proofread_content_with_all_checks(self, mock_generate_text):
        """Test proofreading with all checks enabled."""
        mock_generate_text.return_value = """
        {
            "corrected_content": "Corrected content",
            "issues": []
        }
        """

        mock_provider = MagicMock()
        options = ProofreadingOptions(
            check_grammar=True,
            check_spelling=True,
            check_style=True,
            check_plagiarism=True,
        )

        result = proofread_content(
            content=self.content,
            options=options,
            provider=mock_provider,
        )

        self.assertIsInstance(result, ProofreadingResult)

    @patch("src.post_processing.proofreader.generate_text")
    def test_proofread_content_error(self, mock_generate_text):
        """Test proofread_content raises error on failure."""
        mock_generate_text.side_effect = Exception("LLM error")
        mock_provider = MagicMock()

        with self.assertRaises(ProofreadingError):
            proofread_content(
                content=self.content,
                provider=mock_provider,
            )


class TestHumanizer(unittest.TestCase):
    """Tests for the humanizer module."""

    def setUp(self):
        """Set up test fixtures."""
        self.content = """
        Artificial intelligence is a field of computer science.
        It focuses on creating intelligent machines.
        """

    @patch("src.post_processing.humanizer.generate_text")
    def test_humanize_content(self, mock_generate_text):
        """Test the humanize_content function."""
        mock_generate_text.return_value = """
        Have you ever wondered how AI works? Well, artificial intelligence
        is basically a branch of computer science that's all about building
        smart machines that can think and learn like humans do.
        """

        mock_provider = MagicMock()
        options = HumanizationOptions(
            tone="conversational",
            formality="neutral",
            personality="friendly",
        )

        result = humanize_content(
            content=self.content,
            options=options,
            provider=mock_provider,
        )

        # humanize_content returns a string
        self.assertIsInstance(result, str)
        self.assertIsNotNone(result)
        mock_generate_text.assert_called_once()

    @patch("src.post_processing.humanizer.generate_text")
    def test_humanize_content_formal_tone(self, mock_generate_text):
        """Test humanizing with formal tone."""
        mock_generate_text.return_value = (
            "Artificial intelligence represents a significant field within computer science."
        )

        mock_provider = MagicMock()
        options = HumanizationOptions(tone="formal")

        result = humanize_content(
            content=self.content,
            options=options,
            provider=mock_provider,
        )

        self.assertIsInstance(result, str)

    @patch("src.post_processing.humanizer.generate_text")
    def test_humanize_content_error(self, mock_generate_text):
        """Test humanize_content raises error on failure."""
        mock_generate_text.side_effect = Exception("LLM error")
        mock_provider = MagicMock()

        with self.assertRaises(HumanizationError):
            humanize_content(
                content=self.content,
                provider=mock_provider,
            )


class TestProofreadingOptions(unittest.TestCase):
    """Tests for the ProofreadingOptions model."""

    def test_proofreading_options_defaults(self):
        """Test ProofreadingOptions has correct defaults."""
        options = ProofreadingOptions()
        self.assertTrue(options.check_grammar)
        self.assertTrue(options.check_spelling)
        self.assertTrue(options.check_style)
        self.assertFalse(options.check_plagiarism)

    def test_proofreading_options_custom(self):
        """Test ProofreadingOptions with custom values."""
        options = ProofreadingOptions(
            check_grammar=False,
            check_spelling=True,
            check_style=False,
            check_plagiarism=True,
        )
        self.assertFalse(options.check_grammar)
        self.assertTrue(options.check_spelling)
        self.assertFalse(options.check_style)
        self.assertTrue(options.check_plagiarism)


class TestHumanizationOptions(unittest.TestCase):
    """Tests for the HumanizationOptions model."""

    def test_humanization_options_defaults(self):
        """Test HumanizationOptions has correct defaults."""
        options = HumanizationOptions()
        self.assertEqual(options.tone, "casual")
        self.assertEqual(options.formality, "neutral")
        self.assertEqual(options.personality, "friendly")

    def test_humanization_options_custom(self):
        """Test HumanizationOptions with custom values."""
        options = HumanizationOptions(
            tone="professional",
            formality="formal",
            personality="authoritative",
        )
        self.assertEqual(options.tone, "professional")
        self.assertEqual(options.formality, "formal")
        self.assertEqual(options.personality, "authoritative")


if __name__ == "__main__":
    unittest.main()
