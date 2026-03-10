"""
Tests for the research module.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.research.web_researcher import (
    ResearchError,
    conduct_web_research,
)
from src.types.research import (
    GoogleSerpResult,
    ResearchResults,
    SearchOptions,
    SearchResult,
)


class TestWebResearcher(unittest.TestCase):
    """Tests for the web research module."""

    def setUp(self):
        """Set up test fixtures."""
        self.keywords = ["artificial intelligence", "machine learning"]
        self.search_options = SearchOptions()

    @patch("src.research.web_researcher.google_serp_search")
    @patch("src.research.web_researcher.tavily_ai_search")
    @patch("src.research.web_researcher.metaphor_ai_search")
    @patch("src.research.web_researcher.google_trends_analysis")
    def test_conduct_web_research(
        self,
        mock_trends,
        mock_metaphor,
        mock_tavily,
        mock_google,
    ):
        """Test the conduct_web_research function."""
        # Setup mock return values
        mock_google.return_value = GoogleSerpResult(
            organic=[
                SearchResult(
                    title="AI Article",
                    url="https://example.com/ai",
                    snippet="An article about AI",
                )
            ],
            people_also_ask=[],
            related_searches=[],
        )
        mock_tavily.return_value = None
        mock_metaphor.return_value = None
        mock_trends.return_value = None

        # Conduct research
        results = conduct_web_research(self.keywords, self.search_options)

        # Verify results
        self.assertIsInstance(results, ResearchResults)
        self.assertIsNotNone(results.google)
        self.assertEqual(len(results.google.organic), 1)
        self.assertEqual(results.google.organic[0].title, "AI Article")

    @patch("src.research.web_researcher.google_serp_search")
    @patch("src.research.web_researcher.tavily_ai_search")
    @patch("src.research.web_researcher.metaphor_ai_search")
    @patch("src.research.web_researcher.google_trends_analysis")
    def test_conduct_web_research_with_error(
        self,
        mock_trends,
        mock_metaphor,
        mock_tavily,
        mock_google,
    ):
        """Test conduct_web_research raises ResearchError on failure."""
        mock_google.side_effect = Exception("API error")

        with self.assertRaises(ResearchError):
            conduct_web_research(self.keywords, self.search_options)

    def test_search_options_defaults(self):
        """Test SearchOptions has correct defaults."""
        options = SearchOptions()
        self.assertEqual(options.num_results, 10)
        self.assertEqual(options.language, "en")
        self.assertEqual(options.location, "us")


class TestResearchResults(unittest.TestCase):
    """Tests for the ResearchResults model."""

    def test_research_results_empty(self):
        """Test ResearchResults with no data."""
        results = ResearchResults(
            google=None,
            tavily=None,
            metaphor=None,
            trends=None,
        )
        self.assertIsNone(results.google)
        self.assertIsNone(results.tavily)
        self.assertIsNone(results.metaphor)
        self.assertIsNone(results.trends)

    def test_research_results_with_google(self):
        """Test ResearchResults with Google data."""
        google_result = GoogleSerpResult(
            organic=[
                SearchResult(
                    title="Test",
                    url="https://test.com",
                    snippet="Test snippet",
                )
            ],
            people_also_ask=[],
            related_searches=[],
        )
        results = ResearchResults(
            google=google_result,
            tavily=None,
            metaphor=None,
            trends=None,
        )
        self.assertIsNotNone(results.google)
        self.assertEqual(len(results.google.organic), 1)


class TestSearchResult(unittest.TestCase):
    """Tests for the SearchResult model."""

    def test_search_result_creation(self):
        """Test SearchResult creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet content",
        )
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.snippet, "Test snippet content")


if __name__ == "__main__":
    unittest.main()
