"""Tests for SEO optimization loop."""

from unittest.mock import MagicMock, patch

import pytest

from src.types.seo import (
    ContentOptimization,
    ContentScore,
    OptimizationSuggestion,
    SEOOptimizationResult,
    SEOThresholds,
    SuggestionPriority,
    SuggestionType,
)


def _make_score(overall: float = 80.0, **kwargs) -> ContentScore:
    defaults = {
        "overall_score": overall,
        "topic_coverage": kwargs.get("topic_coverage", 75.0),
        "term_usage": kwargs.get("term_usage", 70.0),
        "structure_score": kwargs.get("structure_score", 65.0),
        "readability_score": kwargs.get("readability_score", 60.0),
        "word_count_score": kwargs.get("word_count_score", 85.0),
    }
    return ContentScore(**defaults)


def _make_optimization(score: ContentScore, suggestions=None) -> ContentOptimization:
    return ContentOptimization(
        score=score,
        suggestions=suggestions or [],
        missing_topics=[],
        missing_terms=[],
        covered_topics=[],
        covered_terms=[],
    )


def _make_blog_post():
    post = MagicMock()
    post.title = "Test Blog Post"
    post.description = "Test description"
    section = MagicMock()
    section.title = "Introduction"
    subtopic = MagicMock()
    subtopic.title = "Overview"
    subtopic.content = "This is the content of the blog post about testing SEO optimization."
    section.subtopics = [subtopic]
    post.sections = [section]
    return post


class TestCheckThresholds:
    def test_all_above_threshold(self):
        from src.seo.optimization_loop import _check_thresholds

        score = _make_score(overall=80, topic_coverage=70, term_usage=60, structure_score=60, readability_score=60, word_count_score=60)
        thresholds = SEOThresholds()
        assert _check_thresholds(score, thresholds) is True

    def test_overall_below(self):
        from src.seo.optimization_loop import _check_thresholds

        score = _make_score(overall=50)
        thresholds = SEOThresholds(overall_minimum=70)
        assert _check_thresholds(score, thresholds) is False

    def test_single_dimension_below(self):
        from src.seo.optimization_loop import _check_thresholds

        score = _make_score(overall=80, term_usage=30)
        thresholds = SEOThresholds(term_usage_minimum=50)
        assert _check_thresholds(score, thresholds) is False


class TestOptimizeUntilThreshold:
    @patch("src.seo.optimization_loop.optimize_content")
    def test_passes_on_first_try(self, mock_optimize):
        from src.seo.optimization_loop import optimize_until_threshold

        high_score = _make_score(overall=85, topic_coverage=80, term_usage=75, structure_score=70, readability_score=65, word_count_score=80)
        mock_optimize.return_value = _make_optimization(high_score)

        blog_post = _make_blog_post()
        result = optimize_until_threshold(blog_post, "seo testing")

        assert isinstance(result, SEOOptimizationResult)
        assert result.passed is True
        assert result.passes_used == 1
        assert result.suggestions_applied == 0

    @patch("src.seo.optimization_loop.generate_text")
    @patch("src.seo.optimization_loop.create_provider_from_env")
    @patch("src.seo.optimization_loop.optimize_content")
    def test_retry_improves_score(self, mock_optimize, mock_provider, mock_generate):
        from src.seo.optimization_loop import optimize_until_threshold

        low_score = _make_score(overall=40, topic_coverage=30, term_usage=25, structure_score=35, readability_score=40, word_count_score=50)
        high_score = _make_score(overall=85, topic_coverage=80, term_usage=75, structure_score=70, readability_score=65, word_count_score=80)

        suggestions = [
            OptimizationSuggestion(
                type=SuggestionType.COVER_TOPIC,
                priority=SuggestionPriority.HIGH,
                description="Cover topic X",
            ),
        ]

        mock_optimize.side_effect = [
            _make_optimization(low_score, suggestions),
            _make_optimization(high_score),
        ]
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = "## Introduction\n### Overview\nImproved content about testing."

        blog_post = _make_blog_post()
        result = optimize_until_threshold(blog_post, "seo testing")

        assert result.passed is True
        assert result.passes_used == 2
        assert result.suggestions_applied == 1

    @patch("src.seo.optimization_loop.generate_text")
    @patch("src.seo.optimization_loop.create_provider_from_env")
    @patch("src.seo.optimization_loop.optimize_content")
    def test_max_passes_exhausted(self, mock_optimize, mock_provider, mock_generate):
        from src.seo.optimization_loop import optimize_until_threshold

        low_score = _make_score(overall=40, topic_coverage=30, term_usage=25, structure_score=35, readability_score=40, word_count_score=50)
        suggestions = [
            OptimizationSuggestion(
                type=SuggestionType.ADD_TERM,
                priority=SuggestionPriority.HIGH,
                description="Add term Y",
            ),
        ]

        mock_optimize.return_value = _make_optimization(low_score, suggestions)
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = "## Intro\nStill low quality."

        blog_post = _make_blog_post()
        thresholds = SEOThresholds(max_optimization_passes=2)
        result = optimize_until_threshold(blog_post, "seo testing", thresholds=thresholds)

        assert result.passed is False
        assert result.passes_used == 2

    @patch("src.seo.optimization_loop.optimize_content")
    def test_no_suggestions_stops_early(self, mock_optimize):
        from src.seo.optimization_loop import optimize_until_threshold

        low_score = _make_score(overall=40, topic_coverage=30, term_usage=25, structure_score=35, readability_score=40, word_count_score=50)
        mock_optimize.return_value = _make_optimization(low_score, suggestions=[])

        blog_post = _make_blog_post()
        result = optimize_until_threshold(blog_post, "seo testing")

        assert result.passed is False
        assert result.passes_used == 1
        assert result.suggestions_applied == 0


class TestBlogPostConversion:
    def test_roundtrip(self):
        from src.seo.optimization_loop import _blog_post_to_text, _text_to_sections

        blog_post = _make_blog_post()
        text = _blog_post_to_text(blog_post)

        assert "# Test Blog Post" in text
        assert "## Introduction" in text
        assert "### Overview" in text

        # Parse back
        updated = _text_to_sections(text, blog_post)
        assert len(updated.sections) >= 1
