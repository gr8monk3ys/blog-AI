"""
Brand Voice Training types and data models.

Includes security validation for:
- URL fields (SSRF protection)
- HTML content (XSS protection)
- Content size limits (DoS protection)
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator

import bleach


# =============================================================================
# Security Constants
# =============================================================================

# SSRF protection - blocked hostnames
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]",
    "metadata.google.internal", "169.254.169.254", "metadata",
}

# Allowed HTML tags for content sanitization (whitelist approach)
ALLOWED_HTML_TAGS: Set[str] = {
    "p", "br", "b", "i", "u", "strong", "em", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "code", "pre",
}


class WritingStyle(str, Enum):
    """Available writing styles."""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    BALANCED = "balanced"


class ContentType(str, Enum):
    """Types of content samples."""
    TEXT = "text"
    BLOG = "blog"
    EMAIL = "email"
    SOCIAL = "social"
    WEBSITE = "website"
    ARTICLE = "article"


class TrainingStatus(str, Enum):
    """Voice profile training status."""
    UNTRAINED = "untrained"
    ANALYZING = "analyzing"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"


class VocabularyProfile(BaseModel):
    """Vocabulary analysis of a voice sample."""
    common_words: List[str] = Field(default_factory=list)
    unique_phrases: List[str] = Field(default_factory=list)
    avg_word_length: float = 0.0
    vocabulary_richness: float = 0.0  # type-token ratio
    formality_indicators: List[str] = Field(default_factory=list)
    casual_indicators: List[str] = Field(default_factory=list)


class SentencePatterns(BaseModel):
    """Sentence structure analysis."""
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    question_frequency: float = 0.0
    exclamation_frequency: float = 0.0
    complex_sentence_ratio: float = 0.0
    opening_patterns: List[str] = Field(default_factory=list)
    transition_words: List[str] = Field(default_factory=list)


class ToneDistribution(BaseModel):
    """Tone analysis scores."""
    professional: float = 0.0
    friendly: float = 0.0
    casual: float = 0.0
    authoritative: float = 0.0
    empathetic: float = 0.0
    enthusiastic: float = 0.0
    confident: float = 0.0
    approachable: float = 0.0
    innovative: float = 0.0
    trustworthy: float = 0.0
    playful: float = 0.0
    serious: float = 0.0


class StyleMetrics(BaseModel):
    """Style measurement metrics."""
    formality_score: float = 0.0  # 0=casual, 1=formal
    complexity_score: float = 0.0  # reading level
    engagement_score: float = 0.0  # hooks, CTAs, questions
    personality_score: float = 0.0  # distinctiveness
    consistency_score: float = 0.0  # internal consistency


class SampleAnalysis(BaseModel):
    """Complete analysis of a voice sample."""
    vocabulary: VocabularyProfile = Field(default_factory=VocabularyProfile)
    sentences: SentencePatterns = Field(default_factory=SentencePatterns)
    tone: ToneDistribution = Field(default_factory=ToneDistribution)
    style: StyleMetrics = Field(default_factory=StyleMetrics)
    key_characteristics: List[str] = Field(default_factory=list)
    quality_score: float = 0.0


class VoiceSample(BaseModel):
    """A content sample for voice training with security validation."""
    id: str
    profile_id: str = Field(..., max_length=100)
    title: Optional[str] = Field(default=None, max_length=200)
    content: str = Field(..., min_length=10, max_length=50000)
    content_type: ContentType = ContentType.TEXT
    word_count: int = Field(default=0, ge=0)
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_platform: Optional[str] = Field(default=None, max_length=100)
    is_analyzed: bool = False
    analysis_result: Optional[SampleAnalysis] = None
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_primary_example: bool = False

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content using bleach library for proper XSS protection."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()

        # Use bleach for proper HTML sanitization (cannot be bypassed like regex)
        v = bleach.clean(v, tags=ALLOWED_HTML_TAGS, strip=True, strip_comments=True)

        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters")
        if len(v) > 50000:
            raise ValueError("Content exceeds maximum length of 50000 characters")

        return v

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v):
        """Validate source URL for SSRF protection."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        from urllib.parse import urlparse
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("Invalid URL format")

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")

        # Check hostname
        if not parsed.hostname:
            raise ValueError("URL must include hostname")

        hostname = parsed.hostname.lower()
        if hostname in BLOCKED_HOSTNAMES:
            raise ValueError(f"URL hostname '{hostname}' is not allowed")

        # Check for IP address in hostname (block private IPs)
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise ValueError("Private/internal IP addresses are not allowed")
        except ValueError:
            pass  # Not an IP, that's fine

        return v

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, v):
        """Validate profile ID format."""
        if not v or not v.strip():
            raise ValueError("Profile ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid profile ID format")
        return v


class VoiceFingerprint(BaseModel):
    """Aggregated voice characteristics from all samples."""
    id: str
    profile_id: str
    vocabulary_profile: VocabularyProfile = Field(default_factory=VocabularyProfile)
    sentence_patterns: SentencePatterns = Field(default_factory=SentencePatterns)
    tone_distribution: ToneDistribution = Field(default_factory=ToneDistribution)
    style_metrics: StyleMetrics = Field(default_factory=StyleMetrics)
    voice_summary: str = ""
    sample_count: int = 0
    training_quality: float = 0.0
    last_trained_at: Optional[str] = None


class VoiceScore(BaseModel):
    """Consistency score for generated content."""
    overall_score: float
    tone_match: float
    vocabulary_match: float
    style_match: float
    feedback: Dict[str, Any] = Field(default_factory=dict)
    deviations: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class BrandProfile(BaseModel):
    """Enhanced brand profile with voice training."""
    id: str
    name: str
    slug: str
    tone_keywords: List[str] = Field(default_factory=list)
    writing_style: WritingStyle = WritingStyle.BALANCED
    example_content: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    preferred_words: List[str] = Field(default_factory=list)
    avoid_words: List[str] = Field(default_factory=list)
    brand_values: List[str] = Field(default_factory=list)
    content_themes: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_default: bool = False
    # Voice training fields
    training_status: TrainingStatus = TrainingStatus.UNTRAINED
    training_quality: float = 0.0
    sample_count: int = 0
    voice_fingerprint: Optional[VoiceFingerprint] = None
    created_at: str = ""
    updated_at: str = ""


class AnalyzeSampleRequest(BaseModel):
    """Request to analyze a voice sample."""
    content: str
    content_type: ContentType = ContentType.TEXT
    title: Optional[str] = None


class TrainVoiceRequest(BaseModel):
    """Request to train voice from samples."""
    profile_id: str
    sample_ids: Optional[List[str]] = None  # If None, use all samples


class ScoreContentRequest(BaseModel):
    """Request to score content against brand voice."""
    profile_id: str
    content: str
    content_type: ContentType = ContentType.TEXT


class AddSampleRequest(BaseModel):
    """Request to add a voice sample with security validation."""
    profile_id: str = Field(..., max_length=100)
    content: str = Field(..., min_length=10, max_length=50000)
    content_type: ContentType = ContentType.TEXT
    title: Optional[str] = Field(default=None, max_length=200)
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_platform: Optional[str] = Field(default=None, max_length=100)
    is_primary_example: bool = False

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content using bleach library for proper XSS protection."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()

        # Use bleach for proper HTML sanitization (cannot be bypassed like regex)
        v = bleach.clean(v, tags=ALLOWED_HTML_TAGS, strip=True, strip_comments=True)

        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters")

        return v

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v):
        """Validate source URL for SSRF protection."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        from urllib.parse import urlparse
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("Invalid URL format")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")

        if not parsed.hostname:
            raise ValueError("URL must include hostname")

        hostname = parsed.hostname.lower()
        if hostname in BLOCKED_HOSTNAMES:
            raise ValueError(f"URL hostname '{hostname}' is not allowed")

        # Block private IPs
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                raise ValueError("Private/internal IP addresses are not allowed")
        except ValueError:
            pass

        return v

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, v):
        """Validate profile ID format."""
        if not v or not v.strip():
            raise ValueError("Profile ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid profile ID format")
        return v
