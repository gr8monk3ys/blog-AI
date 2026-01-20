"""Pydantic models for the Blog AI application."""

from .requests import (
    BlogGenerationRequest,
    BookGenerationRequest,
    WebSocketMessage,
)
from .validation import (
    ALLOWED_TONES,
    MAX_CHAPTERS,
    MAX_KEYWORD_LENGTH,
    MAX_KEYWORDS_COUNT,
    MAX_SECTIONS_PER_CHAPTER,
    MAX_TOPIC_LENGTH,
)

__all__ = [
    "BlogGenerationRequest",
    "BookGenerationRequest",
    "WebSocketMessage",
    "MAX_TOPIC_LENGTH",
    "MAX_KEYWORD_LENGTH",
    "MAX_KEYWORDS_COUNT",
    "MAX_CHAPTERS",
    "MAX_SECTIONS_PER_CHAPTER",
    "ALLOWED_TONES",
]
