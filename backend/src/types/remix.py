"""
Content Remix Engine types and data models.

This module defines the types for transforming content between formats:
- Blog -> Twitter Thread
- Blog -> LinkedIn Post
- Blog -> Email Newsletter
- Blog -> YouTube Script
- Blog -> Instagram Carousel
- And more...

Includes security validation for content size limits and input sanitization.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ContentFormat(str, Enum):
    """Supported content formats for remix."""
    # Source formats
    BLOG = "blog"
    ARTICLE = "article"

    # Target formats
    TWITTER_THREAD = "twitter_thread"
    LINKEDIN_POST = "linkedin_post"
    EMAIL_NEWSLETTER = "email_newsletter"
    YOUTUBE_SCRIPT = "youtube_script"
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    PODCAST_NOTES = "podcast_notes"
    FACEBOOK_POST = "facebook_post"
    TIKTOK_SCRIPT = "tiktok_script"
    MEDIUM_ARTICLE = "medium_article"
    PRESS_RELEASE = "press_release"
    EXECUTIVE_SUMMARY = "executive_summary"
    SLIDE_DECK_OUTLINE = "slide_deck_outline"


# Format metadata for UI display
FORMAT_METADATA: Dict[ContentFormat, Dict[str, Any]] = {
    ContentFormat.TWITTER_THREAD: {
        "name": "Twitter Thread",
        "icon": "🐦",
        "description": "10-15 tweet thread with hooks and engagement",
        "max_length": 4200,  # ~15 tweets
        "platform": "twitter",
        "supports_images": True,
    },
    ContentFormat.LINKEDIN_POST: {
        "name": "LinkedIn Post",
        "icon": "💼",
        "description": "Professional post with insights and CTA",
        "max_length": 3000,
        "platform": "linkedin",
        "supports_images": True,
    },
    ContentFormat.EMAIL_NEWSLETTER: {
        "name": "Email Newsletter",
        "icon": "📧",
        "description": "Engaging email with subject line and sections",
        "max_length": 5000,
        "platform": "email",
        "supports_images": True,
    },
    ContentFormat.YOUTUBE_SCRIPT: {
        "name": "YouTube Script",
        "icon": "🎬",
        "description": "Video script with intro, sections, and outro",
        "max_length": 8000,
        "platform": "youtube",
        "supports_images": False,
    },
    ContentFormat.INSTAGRAM_CAROUSEL: {
        "name": "Instagram Carousel",
        "icon": "📸",
        "description": "5-10 slide carousel with captions",
        "max_length": 2200,
        "platform": "instagram",
        "supports_images": True,
        "slide_count": {"min": 5, "max": 10},
    },
    ContentFormat.PODCAST_NOTES: {
        "name": "Podcast Show Notes",
        "icon": "🎙️",
        "description": "Episode summary, timestamps, and key takeaways",
        "max_length": 3000,
        "platform": "podcast",
        "supports_images": False,
    },
    ContentFormat.FACEBOOK_POST: {
        "name": "Facebook Post",
        "icon": "📘",
        "description": "Engaging post with storytelling and engagement hooks",
        "max_length": 2000,
        "platform": "facebook",
        "supports_images": True,
    },
    ContentFormat.TIKTOK_SCRIPT: {
        "name": "TikTok Script",
        "icon": "🎵",
        "description": "Short-form video script with hook and punchline",
        "max_length": 500,
        "platform": "tiktok",
        "supports_images": False,
    },
    ContentFormat.MEDIUM_ARTICLE: {
        "name": "Medium Article",
        "icon": "📝",
        "description": "Reformatted article optimized for Medium",
        "max_length": 10000,
        "platform": "medium",
        "supports_images": True,
    },
    ContentFormat.PRESS_RELEASE: {
        "name": "Press Release",
        "icon": "📰",
        "description": "Formal press release format with quotes",
        "max_length": 3000,
        "platform": "pr",
        "supports_images": False,
    },
    ContentFormat.EXECUTIVE_SUMMARY: {
        "name": "Executive Summary",
        "icon": "📋",
        "description": "Concise summary for decision-makers",
        "max_length": 1500,
        "platform": "business",
        "supports_images": False,
    },
    ContentFormat.SLIDE_DECK_OUTLINE: {
        "name": "Slide Deck Outline",
        "icon": "📊",
        "description": "Presentation outline with slide-by-slide content",
        "max_length": 4000,
        "platform": "presentation",
        "supports_images": True,
        "slide_count": {"min": 8, "max": 15},
    },
}


class QualityScore(BaseModel):
    """Quality assessment for remixed content."""
    overall: float = Field(ge=0.0, le=1.0, description="Overall quality score")
    format_fit: float = Field(ge=0.0, le=1.0, description="How well content fits the format")
    voice_match: float = Field(ge=0.0, le=1.0, description="Brand voice preservation")
    completeness: float = Field(ge=0.0, le=1.0, description="Key points coverage")
    engagement: float = Field(ge=0.0, le=1.0, description="Predicted engagement potential")
    platform_optimization: float = Field(ge=0.0, le=1.0, description="Platform-specific optimization")

    @property
    def grade(self) -> str:
        """Return letter grade based on overall score."""
        if self.overall >= 0.9:
            return "A+"
        elif self.overall >= 0.8:
            return "A"
        elif self.overall >= 0.7:
            return "B"
        elif self.overall >= 0.6:
            return "C"
        else:
            return "D"


class ContentChunk(BaseModel):
    """A chunk of content extracted from source."""
    id: str
    type: str  # "heading", "paragraph", "list", "quote", "key_point"
    content: str
    importance: float = Field(ge=0.0, le=1.0, description="Importance score for prioritization")
    word_count: int = 0
    source_section: Optional[str] = None


class ContentAnalysis(BaseModel):
    """Analysis of source content for transformation."""
    title: str
    summary: str = Field(max_length=500)
    key_points: List[str] = Field(max_length=10)
    main_argument: str
    target_audience: str
    tone: str
    word_count: int
    chunks: List[ContentChunk] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    suggested_formats: List[ContentFormat] = Field(default_factory=list)


class TwitterThread(BaseModel):
    """Twitter thread format."""
    tweets: List[str] = Field(max_length=15)
    hook: str = Field(description="First tweet hook")
    cta: str = Field(description="Call-to-action in final tweet")
    hashtags: List[str] = Field(default_factory=list, max_length=5)

    @property
    def tweet_count(self) -> int:
        return len(self.tweets)


class LinkedInPost(BaseModel):
    """LinkedIn post format."""
    hook: str = Field(description="Opening hook line")
    body: str = Field(max_length=3000)
    cta: str = Field(description="Call-to-action")
    hashtags: List[str] = Field(default_factory=list, max_length=5)


class EmailNewsletter(BaseModel):
    """Email newsletter format."""
    subject_line: str = Field(max_length=60)
    preview_text: str = Field(max_length=100)
    greeting: str
    intro: str
    sections: List[Dict[str, str]]  # {"title": "...", "content": "..."}
    cta: str
    signoff: str


class YouTubeScript(BaseModel):
    """YouTube video script format."""
    title: str
    hook: str = Field(description="First 5-second hook")
    intro: str
    sections: List[Dict[str, str]]  # {"title": "...", "content": "...", "duration": "..."}
    outro: str
    cta: str
    estimated_duration: str


class InstagramCarousel(BaseModel):
    """Instagram carousel format."""
    caption: str = Field(max_length=2200)
    slides: List[Dict[str, str]]  # {"title": "...", "content": "...", "image_prompt": "..."}
    hashtags: List[str] = Field(default_factory=list, max_length=30)
    cta: str


class PodcastNotes(BaseModel):
    """Podcast show notes format."""
    episode_title: str
    summary: str
    key_takeaways: List[str]
    timestamps: List[Dict[str, str]]  # {"time": "...", "topic": "..."}
    resources: List[Dict[str, str]]  # {"title": "...", "url": "..."}
    transcript_excerpt: str


class RemixedContent(BaseModel):
    """A single remixed content piece."""
    format: ContentFormat
    content: Dict[str, Any]  # Format-specific content
    quality_score: QualityScore
    word_count: int
    character_count: int
    generation_time_ms: int = 0
    provider_used: Optional[str] = None


class RemixRequest(BaseModel):
    """Request to remix content into multiple formats with security validation."""
    source_content: Dict[str, Any] = Field(
        ...,
        description="Source content to remix (blog post)"
    )
    target_formats: List[ContentFormat] = Field(
        min_length=1,
        max_length=10,
        description="Target formats to generate"
    )
    preserve_voice: bool = Field(default=True, description="Preserve brand voice")
    brand_profile_id: Optional[str] = Field(default=None, max_length=100)
    tone_override: Optional[str] = Field(default=None, max_length=50)
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("source_content")
    @classmethod
    def validate_source_content(cls, v):
        """Validate source content size and structure."""
        if not v:
            raise ValueError("Source content is required")

        # Check if it's a dictionary
        if not isinstance(v, dict):
            raise ValueError("Source content must be a dictionary")

        # Estimate content size by serializing
        import json
        try:
            content_str = json.dumps(v)
            if len(content_str) > 500000:  # 500KB limit
                raise ValueError("Source content exceeds maximum size of 500KB")
        except (TypeError, ValueError) as e:
            if "exceeds maximum" in str(e):
                raise
            raise ValueError("Source content must be JSON serializable")

        return v

    @field_validator("brand_profile_id")
    @classmethod
    def validate_brand_profile_id(cls, v):
        """Validate brand profile ID format."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid brand profile ID format")
        return v

    @field_validator("tone_override")
    @classmethod
    def validate_tone_override(cls, v):
        """Validate tone override."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        # Only allow safe characters
        v = "".join(char for char in v if char.isalnum() or char in " -_")
        return v[:50] if v else None

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        """Validate conversation ID format."""
        if not v or not v.strip():
            raise ValueError("Conversation ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid conversation ID format")
        return v


class RemixResponse(BaseModel):
    """Response from remix operation."""
    success: bool
    source_analysis: ContentAnalysis
    remixed_content: List[RemixedContent]
    total_generation_time_ms: int
    average_quality_score: float
    message: Optional[str] = None


class RemixPreviewRequest(BaseModel):
    """Request to preview remix without full generation."""
    source_content: Dict[str, Any] = Field(...)
    target_format: ContentFormat

    @field_validator("source_content")
    @classmethod
    def validate_source_content(cls, v):
        """Validate source content size."""
        if not v:
            raise ValueError("Source content is required")
        if not isinstance(v, dict):
            raise ValueError("Source content must be a dictionary")

        import json
        try:
            content_str = json.dumps(v)
            if len(content_str) > 500000:
                raise ValueError("Source content exceeds maximum size of 500KB")
        except (TypeError, ValueError) as e:
            if "exceeds maximum" in str(e):
                raise
            raise ValueError("Source content must be JSON serializable")

        return v


class RemixPreviewResponse(BaseModel):
    """Preview of remix transformation."""
    format: ContentFormat
    estimated_length: int
    key_elements: List[str]
    sample_hook: str
    confidence: float


def get_format_info(format: ContentFormat) -> Dict[str, Any]:
    """Get metadata for a content format."""
    return FORMAT_METADATA.get(format, {
        "name": format.value.replace("_", " ").title(),
        "icon": "📄",
        "description": f"Convert to {format.value}",
        "max_length": 5000,
        "platform": "general",
        "supports_images": False,
    })


def get_available_formats() -> List[Dict[str, Any]]:
    """Get all available formats with metadata."""
    return [
        {
            "format": fmt.value,
            **get_format_info(fmt)
        }
        for fmt in ContentFormat
        if fmt not in [ContentFormat.BLOG, ContentFormat.ARTICLE]  # Exclude source formats
    ]
