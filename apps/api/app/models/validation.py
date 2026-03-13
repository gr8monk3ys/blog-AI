"""
Validation constants for request models.
"""

from typing import Set

# Input validation constants
MAX_TOPIC_LENGTH: int = 500
MAX_KEYWORD_LENGTH: int = 100
MAX_KEYWORDS_COUNT: int = 20
MAX_CHAPTERS: int = 50
MAX_SECTIONS_PER_CHAPTER: int = 20

# Allowed tone values
ALLOWED_TONES: Set[str] = {
    "informative",
    "casual",
    "professional",
    "friendly",
    "formal",
    "conversational",
    "technical",
    "academic",
}
