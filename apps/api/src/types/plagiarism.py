"""
Type definitions for plagiarism detection system.

This module defines the types used for plagiarism checking across
multiple providers (Copyscape, Originality.ai) and fallback methods.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlagiarismProvider(str, Enum):
    """Available plagiarism detection providers."""

    COPYSCAPE = "copyscape"
    ORIGINALITY = "originality"
    EMBEDDING = "embedding"  # Fallback using semantic similarity


class PlagiarismCheckStatus(str, Enum):
    """Status of a plagiarism check."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class PlagiarismRiskLevel(str, Enum):
    """Risk level classification for plagiarism scores."""

    NONE = "none"          # 0-5% similarity
    LOW = "low"            # 5-15% similarity
    MODERATE = "moderate"  # 15-30% similarity
    HIGH = "high"          # 30-50% similarity
    CRITICAL = "critical"  # 50%+ similarity


class MatchingSource(BaseModel):
    """A source that matches content being checked."""

    url: str = Field(..., description="URL of the matching source")
    title: Optional[str] = Field(None, description="Title of the source page")
    similarity_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of content that matches this source"
    )
    matched_words: int = Field(
        default=0,
        ge=0,
        description="Number of words matched"
    )
    matched_text: Optional[str] = Field(
        None,
        max_length=1000,
        description="Sample of matched text (truncated)"
    )
    is_exact_match: bool = Field(
        default=False,
        description="Whether this is an exact phrase match"
    )


class PlagiarismCheckResult(BaseModel):
    """Result of a plagiarism check."""

    check_id: str = Field(..., description="Unique identifier for this check")
    status: PlagiarismCheckStatus = Field(
        ...,
        description="Current status of the check"
    )
    provider: PlagiarismProvider = Field(
        ...,
        description="Provider used for this check"
    )
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall plagiarism score (0 = unique, 100 = copied)"
    )
    risk_level: PlagiarismRiskLevel = Field(
        ...,
        description="Risk level based on score"
    )
    original_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of content that appears original"
    )
    matching_sources: List[MatchingSource] = Field(
        default_factory=list,
        description="List of sources that match the content"
    )
    total_words_checked: int = Field(
        default=0,
        ge=0,
        description="Total words analyzed"
    )
    total_matched_words: int = Field(
        default=0,
        ge=0,
        description="Total words matched across all sources"
    )
    check_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the check was performed"
    )
    cached: bool = Field(
        default=False,
        description="Whether this result was from cache"
    )
    cache_key: Optional[str] = Field(
        None,
        description="Cache key if result was cached"
    )
    api_credits_used: float = Field(
        default=0,
        ge=0,
        description="API credits consumed for this check"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if check failed"
    )
    processing_time_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken to process the check in milliseconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific metadata"
    )


class PlagiarismCheckRequest(BaseModel):
    """Request to check content for plagiarism."""

    content: str = Field(
        ...,
        min_length=50,
        max_length=100000,
        description="Content to check for plagiarism"
    )
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional title for context"
    )
    exclude_urls: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="URLs to exclude from matching (e.g., your own site)"
    )
    preferred_provider: Optional[PlagiarismProvider] = Field(
        None,
        description="Preferred provider (falls back to available)"
    )
    skip_cache: bool = Field(
        default=False,
        description="Skip cache and force fresh check"
    )
    detailed_results: bool = Field(
        default=True,
        description="Include detailed source matching info"
    )


class PlagiarismCheckResponse(BaseModel):
    """API response for plagiarism check."""

    success: bool = Field(..., description="Whether the check succeeded")
    result: Optional[PlagiarismCheckResult] = Field(
        None,
        description="Check result if successful"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings"
    )


class ProviderQuota(BaseModel):
    """Quota information for a plagiarism provider."""

    provider: PlagiarismProvider
    remaining_credits: float = Field(
        default=-1,
        description="Remaining API credits (-1 if unknown)"
    )
    credits_per_check: float = Field(
        default=1,
        description="Credits consumed per check"
    )
    daily_limit: int = Field(
        default=-1,
        description="Daily check limit (-1 if unlimited)"
    )
    daily_used: int = Field(
        default=0,
        description="Checks used today"
    )
    reset_time: Optional[datetime] = Field(
        None,
        description="When daily quota resets"
    )
    is_available: bool = Field(
        default=True,
        description="Whether provider is currently available"
    )


class PlagiarismQuotaResponse(BaseModel):
    """Response containing quota info for all providers."""

    providers: List[ProviderQuota] = Field(
        default_factory=list,
        description="Quota info for each configured provider"
    )
    recommended_provider: Optional[PlagiarismProvider] = Field(
        None,
        description="Recommended provider based on availability and cost"
    )
