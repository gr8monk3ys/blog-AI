"""
Pydantic models for bulk generation endpoints.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.sanitization import contains_injection_attempt, sanitize_text
from .validation import ALLOWED_TONES, MAX_KEYWORD_LENGTH, MAX_KEYWORDS_COUNT, MAX_TOPIC_LENGTH


class BulkGenerationItem(BaseModel):
    """A single item in a bulk generation request."""

    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    keywords: List[str] = Field(default=[], max_length=MAX_KEYWORDS_COUNT)
    tone: str = Field(default="informative")

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Sanitize topic to prevent prompt injection."""
        if contains_injection_attempt(v):
            pass  # Log handled at request level
        return sanitize_text(v)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and sanitize keywords."""
        validated = []
        for keyword in v:
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(
                    f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH}"
                )
            validated.append(sanitize_text(keyword))
        return validated

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Validate tone is one of the allowed values."""
        if v.lower() not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        return v.lower()


class BulkGenerationRequest(BaseModel):
    """Request model for bulk content generation."""

    items: List[BulkGenerationItem] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of items to generate (max 50)"
    )
    tool_id: str = Field(
        default="blog-post",
        description="Tool to use for all generations"
    )
    research: bool = Field(default=False, description="Enable web research")
    proofread: bool = Field(default=True, description="Enable proofreading")
    humanize: bool = Field(default=True, description="Enable humanization")
    parallel_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum parallel generations (1-10)"
    )
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v

    @field_validator("tool_id")
    @classmethod
    def validate_tool_id(cls, v: str) -> str:
        """Validate tool ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Tool ID contains invalid characters")
        return v


class BulkGenerationItemResult(BaseModel):
    """Result for a single item in bulk generation."""

    index: int
    success: bool
    topic: str
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


class BulkGenerationResponse(BaseModel):
    """Response model for bulk generation."""

    success: bool
    job_id: str
    total_items: int
    completed_items: int
    failed_items: int
    results: List[BulkGenerationItemResult]
    total_execution_time_ms: int
    message: Optional[str] = None


class BulkGenerationStatus(BaseModel):
    """Status of a bulk generation job."""

    job_id: str
    status: str  # "pending", "processing", "completed", "cancelled", "failed"
    total_items: int
    completed_items: int
    failed_items: int
    progress_percentage: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    can_cancel: bool = True
