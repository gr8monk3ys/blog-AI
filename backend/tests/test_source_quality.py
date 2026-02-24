"""Tests for source quality scoring."""

import pytest

from src.research.source_quality import (
    _extract_domain,
    _score_domain_authority,
    _score_recency,
    _score_relevance,
    score_source_quality,
)
from src.types.research import CredibilityTier


class TestExtractDomain:
    def test_basic_url(self):
        assert _extract_domain("https://www.example.com/page") == "example.com"

    def test_no_www(self):
        assert _extract_domain("https://nature.com/articles/123") == "nature.com"

    def test_subdomain(self):
        assert _extract_domain("https://blog.example.com") == "blog.example.com"

    def test_invalid_url(self):
        assert _extract_domain("not a url") == ""


class TestDomainAuthority:
    def test_edu_domain(self):
        score, tier = _score_domain_authority("https://www.mit.edu/research")
        assert score >= 85
        assert tier == CredibilityTier.HIGH

    def test_gov_domain(self):
        score, tier = _score_domain_authority("https://data.gov/datasets")
        assert score >= 85
        assert tier == CredibilityTier.HIGH

    def test_high_authority_exact(self):
        score, tier = _score_domain_authority("https://nature.com/articles/s41586")
        assert score >= 80
        assert tier == CredibilityTier.HIGH

    def test_medium_authority(self):
        score, tier = _score_domain_authority("https://medium.com/some-article")
        assert tier == CredibilityTier.MEDIUM

    def test_unknown_domain(self):
        score, tier = _score_domain_authority("https://randomsite.xyz/page")
        assert tier == CredibilityTier.LOW


class TestRecency:
    def test_current_year(self):
        from datetime import datetime, timezone
        year = datetime.now(timezone.utc).year
        score = _score_recency(f"Published in {year}", "")
        assert score >= 90

    def test_old_content(self):
        score = _score_recency("Published in 2010", "")
        assert score < 50

    def test_no_dates(self):
        score = _score_recency("No date information here", "https://example.com")
        assert score == 50.0


class TestRelevance:
    def test_full_match(self):
        score = _score_relevance("AI and machine learning tools", "AI Tools", ["ai", "machine learning"])
        assert score >= 90

    def test_partial_match(self):
        score = _score_relevance("cooking recipes", "Food Blog", ["ai", "cooking"])
        assert 40 <= score <= 60

    def test_no_keywords(self):
        score = _score_relevance("anything", "title", [])
        assert score == 50.0


class TestScoreSourceQuality:
    def test_high_quality_source(self):
        result = score_source_quality(
            url="https://nature.com/articles/2024-study",
            title="AI Research 2024",
            snippet="A comprehensive study of AI in 2024",
            keywords=["AI", "research"],
        )
        assert result.overall >= 60
        assert result.credibility_tier == CredibilityTier.HIGH

    def test_low_quality_source(self):
        result = score_source_quality(
            url="https://random-blog.xyz/post",
            title="My thoughts",
            snippet="Just some random thoughts from 2015",
            keywords=["quantum computing"],
        )
        assert result.overall < 50
