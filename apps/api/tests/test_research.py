"""
Tests for the research module.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.research.web_researcher import (
    ResearchError,
    conduct_web_research,
    google_serp_search,
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


class TestGoogleSerpSearchProviderSelection(unittest.TestCase):
    """Tests for Google SERP provider selection (SerpApi default / SerpBase)."""

    SERP_PAYLOAD = {
        "organic_results": [
            {
                "title": "Example",
                "link": "https://example.com",
                "snippet": "An example result",
            }
        ],
        "related_questions": [{"question": "What is an example?", "answer": "A demo."}],
        "related_searches": [{"query": "example search"}],
    }

    def setUp(self):
        self.options = SearchOptions()
        self.env_cleanup = patch.dict(
            os.environ,
            {"SERP_API_KEY": "", "SERPBASE_API_KEY": "", "SERP_PROVIDER": ""},
            clear=False,
        )
        self.env_cleanup.start()
        self.addCleanup(self.env_cleanup.stop)

    @patch("requests.get")
    def test_default_provider_is_serpapi(self, mock_get):
        """With no SERP_PROVIDER set, SerpApi is used (backwards compatible)."""
        os.environ["SERP_API_KEY"] = "serpapi-key"
        mock_get.return_value.json.return_value = self.SERP_PAYLOAD

        result = google_serp_search("test query", self.options)

        call_url = mock_get.call_args[0][0]
        call_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(call_url, "https://serpapi.com/search")
        self.assertEqual(call_params["api_key"], "serpapi-key")
        self.assertEqual(call_params["q"], "test query")
        self.assertEqual(len(result.organic), 1)
        self.assertEqual(result.organic[0].title, "Example")
        self.assertEqual(result.people_also_ask[0].question, "What is an example?")

    @patch("requests.get")
    def test_serpbase_provider_uses_serpbase_api(self, mock_get):
        """SERP_PROVIDER=serpbase routes to the SerpBase API."""
        os.environ["SERP_PROVIDER"] = "serpbase"
        os.environ["SERPBASE_API_KEY"] = "serpbase-key"
        mock_get.return_value.json.return_value = self.SERP_PAYLOAD

        result = google_serp_search("test query", self.options)

        call_url = mock_get.call_args[0][0]
        call_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(call_url, "https://api.serpbase.dev/google/search")
        self.assertEqual(call_params["api_key"], "serpbase-key")
        self.assertEqual(call_params["q"], "test query")
        self.assertEqual(len(result.organic), 1)
        self.assertEqual(result.related_searches[0].query, "example search")

    @patch("requests.get")
    def test_serpbase_without_key_raises(self, mock_get):
        """SERP_PROVIDER=serpbase without SERPBASE_API_KEY raises ResearchError."""
        os.environ["SERP_PROVIDER"] = "serpbase"
        os.environ.pop("SERPBASE_API_KEY", None)

        with self.assertRaisesRegex(ResearchError, "SERPBASE_API_KEY"):
            google_serp_search("test query", self.options)
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_serpapi_without_key_raises(self, mock_get):
        """Missing SERP_API_KEY still raises ResearchError (unchanged behavior)."""
        with self.assertRaisesRegex(ResearchError, "SERP_API_KEY"):
            google_serp_search("test query", self.options)
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_unknown_provider_falls_back_to_serpapi(self, mock_get):
        """An unknown SERP_PROVIDER value falls back to SerpApi."""
        os.environ["SERP_PROVIDER"] = "bogus"
        os.environ["SERP_API_KEY"] = "serpapi-key"
        mock_get.return_value.json.return_value = self.SERP_PAYLOAD

        result = google_serp_search("test query", self.options)

        call_url = mock_get.call_args[0][0]
        self.assertEqual(call_url, "https://serpapi.com/search")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
