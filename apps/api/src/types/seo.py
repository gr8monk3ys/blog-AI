"""
Type definitions for SEO functionality.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MetaDescription:
    """A meta description for a blog post or webpage."""

    content: str
    length: int

    def __init__(self, content: str):
        self.content = content
        self.length = len(content)


class MetaTag:
    """A meta tag for a blog post or webpage."""

    name: str
    content: str

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class OpenGraphTag:
    """An Open Graph tag for social media sharing."""

    property: str
    content: str

    def __init__(self, property: str, content: str):
        self.property = property
        self.content = content


class TwitterCard:
    """A Twitter card for Twitter sharing."""

    card_type: str
    site: Optional[str]
    title: str
    description: str
    image: Optional[str]

    def __init__(
        self,
        card_type: str = "summary_large_image",
        site: Optional[str] = None,
        title: str = "",
        description: str = "",
        image: Optional[str] = None,
    ):
        self.card_type = card_type
        self.site = site
        self.title = title
        self.description = description
        self.image = image


class ImageAltText:
    """Alt text for an image."""

    image_path: str
    alt_text: str

    def __init__(self, image_path: str, alt_text: str):
        self.image_path = image_path
        self.alt_text = alt_text


class StructuredData:
    """Structured data for rich snippets."""

    type: str
    data: Dict[str, Any]

    def __init__(self, type: str, data: Dict[str, Any]):
        self.type = type
        self.data = data


class SEOAnalysisResult:
    """Results from an SEO analysis."""

    score: int
    title_analysis: Dict[str, Any]
    meta_description_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    keyword_analysis: Dict[str, Any]
    recommendations: List[str]

    def __init__(
        self,
        score: int,
        title_analysis: Dict[str, Any],
        meta_description_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        keyword_analysis: Dict[str, Any],
        recommendations: List[str],
    ):
        self.score = score
        self.title_analysis = title_analysis
        self.meta_description_analysis = meta_description_analysis
        self.content_analysis = content_analysis
        self.keyword_analysis = keyword_analysis
        self.recommendations = recommendations


class SEOMetadata:
    """SEO metadata for a blog post or webpage."""

    title: str
    meta_description: MetaDescription
    meta_tags: List[MetaTag]
    open_graph_tags: List[OpenGraphTag]
    twitter_card: TwitterCard
    structured_data: Optional[StructuredData]

    def __init__(
        self,
        title: str,
        meta_description: MetaDescription,
        meta_tags: Optional[List[MetaTag]] = None,
        open_graph_tags: Optional[List[OpenGraphTag]] = None,
        twitter_card: Optional[TwitterCard] = None,
        structured_data: Optional[StructuredData] = None,
    ):
        self.title = title
        self.meta_description = meta_description
        self.meta_tags = meta_tags or []
        self.open_graph_tags = open_graph_tags or []
        self.twitter_card = twitter_card or TwitterCard(
            title=title, description=meta_description.content
        )
        self.structured_data = structured_data


# =============================================================================
# SERP Analysis and Content Optimization Types (Pydantic)
# =============================================================================


class SuggestionPriority(str, Enum):
    """Priority level for optimization suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionType(str, Enum):
    """Type of optimization suggestion."""

    ADD_HEADING = "add_heading"
    COVER_TOPIC = "cover_topic"
    ADD_TERM = "add_term"
    ANSWER_QUESTION = "answer_question"
    ADJUST_LENGTH = "adjust_length"
    IMPROVE_STRUCTURE = "improve_structure"


class SERPResult(BaseModel):
    """A single result from the SERP analysis."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(default="", description="Meta description or snippet")
    position: int = Field(..., ge=1, description="Ranking position in SERP")


class SERPAnalysis(BaseModel):
    """Complete SERP analysis for a target keyword."""

    keyword: str = Field(..., description="Target keyword analyzed")
    results: List[SERPResult] = Field(
        default_factory=list,
        description="Top SERP results extracted",
    )
    common_topics: List[str] = Field(
        default_factory=list,
        description="Topics frequently covered by top-ranking pages",
    )
    suggested_headings: List[str] = Field(
        default_factory=list,
        description="Recommended headings derived from competitor content",
    )
    questions_to_answer: List[str] = Field(
        default_factory=list,
        description="Questions that top results address or PAA questions",
    )
    recommended_word_count: int = Field(
        default=1500,
        ge=0,
        description="Recommended word count based on competitor average",
    )
    nlp_terms: List[str] = Field(
        default_factory=list,
        description="Semantically related NLP terms to include for topical depth",
    )
    people_also_ask: List[str] = Field(
        default_factory=list,
        description="People Also Ask questions from the SERP",
    )
    related_searches: List[str] = Field(
        default_factory=list,
        description="Related search queries from the SERP",
    )


class ContentScore(BaseModel):
    """Breakdown of content optimization score against SERP data."""

    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall content optimization score (0-100)",
    )
    topic_coverage: float = Field(
        ...,
        ge=0,
        le=100,
        description="How well the content covers competitor topics",
    )
    term_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="How well NLP/semantic terms are utilized",
    )
    structure_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="How well the heading structure matches top results",
    )
    readability_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Readability alignment with top-ranking content",
    )
    word_count_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="How well word count matches the recommended range",
    )


class OptimizationSuggestion(BaseModel):
    """A single actionable optimization suggestion."""

    type: SuggestionType = Field(..., description="Category of the suggestion")
    priority: SuggestionPriority = Field(..., description="Urgency of the suggestion")
    description: str = Field(..., description="Human-readable recommendation")
    current_value: Optional[str] = Field(
        None,
        description="Current state in the content (if applicable)",
    )
    recommended_value: Optional[str] = Field(
        None,
        description="Recommended target value",
    )


class ContentOptimization(BaseModel):
    """Full content optimization result scored against SERP data."""

    score: ContentScore = Field(
        ...,
        description="Detailed score breakdown",
    )
    suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="Ordered list of optimization suggestions",
    )
    missing_topics: List[str] = Field(
        default_factory=list,
        description="Topics covered by competitors but missing from content",
    )
    missing_terms: List[str] = Field(
        default_factory=list,
        description="NLP terms present in top results but absent from content",
    )
    covered_topics: List[str] = Field(
        default_factory=list,
        description="Topics already well covered in the content",
    )
    covered_terms: List[str] = Field(
        default_factory=list,
        description="NLP terms already present in the content",
    )


class ContentBrief(BaseModel):
    """A full content brief generated from SERP analysis."""

    keyword: str = Field(..., description="Target keyword for the brief")
    recommended_title: str = Field(
        ...,
        description="Suggested title based on competitor analysis",
    )
    recommended_outline: List[str] = Field(
        default_factory=list,
        description="Suggested heading/outline structure",
    )
    recommended_word_count: int = Field(
        default=1500,
        ge=0,
        description="Target word count",
    )
    terms_to_include: List[str] = Field(
        default_factory=list,
        description="NLP terms to weave into the content",
    )
    questions_to_answer: List[str] = Field(
        default_factory=list,
        description="Questions the content should address",
    )
    competitor_insights: str = Field(
        default="",
        description="Summary of competitor content strategies",
    )
    tone_guidance: str = Field(
        default="",
        description="Recommended tone and style based on top results",
    )


class SEOThresholds(BaseModel):
    """Minimum score thresholds for SEO optimization to pass."""

    overall_minimum: float = Field(default=70.0, ge=0, le=100)
    topic_coverage_minimum: float = Field(default=60.0, ge=0, le=100)
    term_usage_minimum: float = Field(default=50.0, ge=0, le=100)
    structure_minimum: float = Field(default=50.0, ge=0, le=100)
    readability_minimum: float = Field(default=50.0, ge=0, le=100)
    word_count_minimum: float = Field(default=50.0, ge=0, le=100)
    max_optimization_passes: int = Field(default=3, ge=1, le=10)


class SEOOptimizationResult(BaseModel):
    """Result of the SEO optimization loop."""

    score: ContentScore
    passed: bool = Field(description="Whether all thresholds were met")
    suggestions_applied: int = Field(default=0, description="Number of suggestions fed to LLM")
    passes_used: int = Field(default=0, description="Optimization passes executed")
    final_suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list,
        description="Remaining suggestions after optimization",
    )
