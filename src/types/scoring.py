"""
Type definitions for content scoring system.

This module defines the types used for evaluating generated content
across readability, SEO, and engagement dimensions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScoreLevel(str, Enum):
    """Score classification levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ScoreMetric(BaseModel):
    """Individual score metric with details."""

    name: str = Field(..., description="Metric name")
    score: float = Field(..., ge=0, le=100, description="Score value (0-100)")
    level: ScoreLevel = Field(..., description="Score classification")
    details: str = Field(default="", description="Explanation of the score")
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )


class ReadabilityScore(BaseModel):
    """Readability analysis results."""

    score: float = Field(..., ge=0, le=100, description="Overall readability score")
    level: ScoreLevel = Field(..., description="Score classification")
    flesch_kincaid_grade: float = Field(
        ...,
        description="Flesch-Kincaid grade level"
    )
    flesch_reading_ease: float = Field(
        ...,
        description="Flesch reading ease score"
    )
    average_sentence_length: float = Field(
        ...,
        description="Average words per sentence"
    )
    average_word_length: float = Field(
        ...,
        description="Average characters per word"
    )
    complex_word_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of complex words (3+ syllables)"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )


class SEOScore(BaseModel):
    """SEO analysis results."""

    score: float = Field(..., ge=0, le=100, description="Overall SEO score")
    level: ScoreLevel = Field(..., description="Score classification")
    keyword_density: float = Field(
        ...,
        ge=0,
        le=100,
        description="Primary keyword density percentage"
    )
    keyword_placement: Dict[str, bool] = Field(
        default_factory=dict,
        description="Keyword placement in key positions"
    )
    word_count: int = Field(..., description="Total word count")
    heading_count: int = Field(..., description="Number of headings")
    has_meta_elements: bool = Field(
        default=False,
        description="Whether content has meta-like elements"
    )
    internal_link_potential: int = Field(
        default=0,
        description="Potential internal linking opportunities"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )


class EngagementScore(BaseModel):
    """Engagement analysis results."""

    score: float = Field(..., ge=0, le=100, description="Overall engagement score")
    level: ScoreLevel = Field(..., description="Score classification")
    hook_strength: float = Field(
        ...,
        ge=0,
        le=100,
        description="Opening hook effectiveness"
    )
    cta_count: int = Field(..., description="Number of calls to action")
    emotional_word_count: int = Field(
        ...,
        description="Number of emotional/power words"
    )
    question_count: int = Field(
        ...,
        description="Number of questions (engagement drivers)"
    )
    list_count: int = Field(
        ...,
        description="Number of lists (scannable content)"
    )
    storytelling_elements: int = Field(
        default=0,
        description="Number of storytelling elements detected"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )


class ContentScoreResult(BaseModel):
    """Complete content scoring result."""

    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Weighted overall score"
    )
    overall_level: ScoreLevel = Field(..., description="Overall classification")
    readability: ReadabilityScore = Field(..., description="Readability analysis")
    seo: SEOScore = Field(..., description="SEO analysis")
    engagement: EngagementScore = Field(..., description="Engagement analysis")
    summary: str = Field(default="", description="Brief summary of the analysis")
    top_improvements: List[str] = Field(
        default_factory=list,
        description="Top 3 priority improvements"
    )


class ContentScoreRequest(BaseModel):
    """Request to score content."""

    text: str = Field(..., min_length=1, description="Content to score")
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Target keywords for SEO analysis"
    )
    content_type: Optional[str] = Field(
        default="blog",
        description="Type of content (blog, email, social, etc.)"
    )


class ContentVariation(BaseModel):
    """A single content variation for A/B testing."""

    id: str = Field(..., description="Unique variation identifier")
    content: str = Field(..., description="Generated content")
    label: str = Field(..., description="Variation label (A, B, C)")
    temperature: float = Field(..., description="Temperature used for generation")
    prompt_style: str = Field(
        default="standard",
        description="Prompt style variation used"
    )
    scores: Optional[ContentScoreResult] = Field(
        default=None,
        description="Content scores if calculated"
    )


class VariationGenerationRequest(BaseModel):
    """Request to generate multiple content variations."""

    tool_id: str = Field(..., description="Tool identifier")
    inputs: Dict[str, Any] = Field(..., description="Tool input values")
    variation_count: int = Field(
        default=2,
        ge=2,
        le=3,
        description="Number of variations to generate (2-3)"
    )
    include_scores: bool = Field(
        default=True,
        description="Whether to include scores for each variation"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords for SEO scoring"
    )


class VariationGenerationResult(BaseModel):
    """Result of generating multiple content variations."""

    success: bool = Field(..., description="Whether generation succeeded")
    tool_id: str = Field(..., description="Tool that was executed")
    variations: List[ContentVariation] = Field(
        default_factory=list,
        description="Generated variations"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    execution_time_ms: int = Field(
        ...,
        description="Total execution time in milliseconds"
    )
