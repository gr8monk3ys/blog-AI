"""
Pydantic request models for API endpoints.
"""

import logging
import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.sanitization import contains_injection_attempt, sanitize_text
from .validation import (
    ALLOWED_TONES,
    MAX_CHAPTERS,
    MAX_KEYWORD_LENGTH,
    MAX_KEYWORDS_COUNT,
    MAX_SECTIONS_PER_CHAPTER,
    MAX_TOPIC_LENGTH,
)

logger = logging.getLogger(__name__)


class BlogGenerationRequest(BaseModel):
    """Request model for blog post generation."""

    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    keywords: List[str] = Field(default=[], max_length=MAX_KEYWORDS_COUNT)
    tone: str = Field(default="informative")
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Sanitize topic to prevent prompt injection."""
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in topic: {v[:100]}...")
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

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format."""
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v


class BookGenerationRequest(BaseModel):
    """Request model for book generation."""

    title: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    num_chapters: int = Field(default=5, ge=1, le=MAX_CHAPTERS)
    sections_per_chapter: int = Field(default=3, ge=1, le=MAX_SECTIONS_PER_CHAPTER)
    keywords: List[str] = Field(default=[], max_length=MAX_KEYWORDS_COUNT)
    tone: str = Field(default="informative")
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Sanitize title to prevent prompt injection."""
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in title: {v[:100]}...")
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

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v


class WebSocketMessage(BaseModel):
    """Model for validating WebSocket messages."""

    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[str] = None
