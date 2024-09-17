"""Tests for deep researcher."""

from unittest.mock import MagicMock, patch

import pytest

from src.types.research import DeepResearchResult, ResearchDepth


class TestConductDeepResearch:
    @patch("src.research.deep_researcher.extract_research_sources")
    @patch("src.research.deep_researcher.conduct_web_research")
    def test_basic_depth(self, mock_research, mock_extract):
        from src.research.deep_researcher import conduct_deep_research

        mock_research.return_value = MagicMock()
        mock_extract.return_value = [
            {"title": "Source 1", "url": "https://nature.com/s1", "snippet": "AI research 2024", "provider": "google"},
            {"title": "Source 2", "url": "https://example.com/s2", "snippet": "Basic info", "provider": "google"},
        ]

        result = conduct_deep_research("AI research", keywords=["AI"], depth=ResearchDepth.BASIC)

        assert isinstance(result, DeepResearchResult)
        assert result.depth == ResearchDepth.BASIC
        assert result.total_sources_found == 2
        assert len(result.sources) <= 5

    @patch("src.research.deep_researcher.extract_research_sources")
    @patch("src.research.deep_researcher.conduct_web_research")
    def test_quality_sorting(self, mock_research, mock_extract):
        from src.research.deep_researcher import conduct_deep_research

        mock_research.return_value = MagicMock()
        mock_extract.return_value = [
            {"title": "Low Quality", "url": "https://random.xyz/page", "snippet": "stuff", "provider": "google"},
            {"title": "High Quality", "url": "https://nature.com/study", "snippet": "AI 2024", "provider": "google"},
        ]

        result = conduct_deep_research("AI", keywords=["AI"], depth=ResearchDepth.BASIC)

        # Higher quality source should come first
        if len(result.sources) >= 2:
            assert result.sources[0].quality.overall >= result.sources[1].quality.overall

    @patch("src.research.deep_researcher.extract_research_sources")
    @patch("src.research.deep_researcher.conduct_web_research")
    def test_quality_filtering(self, mock_research, mock_extract):
        from src.research.deep_researcher import conduct_deep_research

        mock_research.return_value = MagicMock()
        mock_extract.return_value = [
            {"title": "Good", "url": "https://nature.com/s1", "snippet": "AI 2024", "provider": "google"},
            {"title": "Bad", "url": "https://x.xyz/z", "snippet": "", "provider": "google"},
        ]

        result = conduct_deep_research("AI", keywords=["AI"], depth=ResearchDepth.BASIC, min_quality_score=50)

        # Low-quality source should be filtered out
        assert all(s.quality.overall >= 50 for s in result.sources)

    @patch("src.research.deep_researcher.extract_research_sources")
    @patch("src.research.deep_researcher.conduct_web_research")
    def test_empty_results(self, mock_research, mock_extract):
        from src.research.deep_researcher import conduct_deep_research

        mock_research.return_value = MagicMock()
        mock_extract.return_value = []

        result = conduct_deep_research("obscure topic", depth=ResearchDepth.BASIC)

        assert result.total_sources_found == 0
        assert len(result.sources) == 0
