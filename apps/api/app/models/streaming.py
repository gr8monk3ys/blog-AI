"""
Pydantic models for streaming API endpoints.
"""

import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.sanitization import contains_injection_attempt, sanitize_text
from .validation import MAX_TOPIC_LENGTH


class StreamingGenerationRequest(BaseModel):
    """Request model for streaming text generation."""

    prompt: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH * 10)
    conversation_id: str = Field(..., min_length=1, max_length=100)
    provider: Literal["openai", "anthropic", "gemini"] = Field(default="openai")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1, le=32000)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    session_id: Optional[str] = Field(default=None, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("prompt")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Sanitize prompt to prevent prompt injection."""
        if contains_injection_attempt(v):
            pass  # Log warning but allow through sanitized
        return sanitize_text(v)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate session ID format if provided."""
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Session ID contains invalid characters")
        return v


class StreamingBlogRequest(BaseModel):
    """Request model for streaming blog generation."""

    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    keywords: List[str] = Field(default=[])
    tone: str = Field(default="informative")
    conversation_id: str = Field(..., min_length=1, max_length=100)
    provider: Literal["openai", "anthropic", "gemini"] = Field(default="openai")
    section_index: Optional[int] = Field(default=None, ge=0)
    session_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Sanitize topic to prevent prompt injection."""
        if contains_injection_attempt(v):
            pass  # Log warning but allow through sanitized
        return sanitize_text(v)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v


class StreamCancelRequest(BaseModel):
    """Request model for cancelling a stream."""

    session_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Session ID contains invalid characters")
        return v


class StreamSessionResponse(BaseModel):
    """Response model for stream session information."""

    session_id: str
    conversation_id: str
    status: str
    token_count: int
    accumulated_content: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamStartResponse(BaseModel):
    """Response model for starting a stream."""

    success: bool
    session_id: str
    conversation_id: str
    message: str = "Streaming started"


class StreamCancelResponse(BaseModel):
    """Response model for cancelling a stream."""

    success: bool
    session_id: str
    message: str


class StreamStatsResponse(BaseModel):
    """Response model for streaming statistics."""

    active_sessions: int
    total_connections: int
    sessions: List[StreamSessionResponse]
