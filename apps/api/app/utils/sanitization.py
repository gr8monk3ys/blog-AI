"""
Input sanitization utilities for preventing prompt injection and other attacks.
"""

import logging
import re
from typing import List, Pattern

logger = logging.getLogger(__name__)

# Patterns commonly used in prompt injection attacks
PROMPT_INJECTION_PATTERNS: List[str] = [
    # System prompt override attempts
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"override\s+(system|previous|prior)\s+(prompt|instructions?|rules?)",
    r"new\s+system\s+prompt",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"human\s*:\s*",
    r"user\s*:\s*",
    # Role manipulation
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+)?(you\s+are\s+)?",
    r"pretend\s+(to\s+be|you\s+are)",
    r"roleplay\s+as",
    r"simulate\s+being",
    # Delimiter abuse
    r"```+",
    r"---+",
    r"===+",
    r"\[\[.*?\]\]",
    # Output manipulation
    r"print\s+the\s+(system\s+)?prompt",
    r"reveal\s+(your|the)\s+(system\s+)?prompt",
    r"show\s+(your|the)\s+(system\s+)?prompt",
    r"output\s+(your|the)\s+instructions",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS: List[Pattern] = [
    re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
]


def sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent prompt injection.

    This function:
    1. Strips and normalizes whitespace
    2. Detects and neutralizes common prompt injection patterns
    3. Escapes potentially dangerous characters

    Args:
        text: The text to sanitize.

    Returns:
        The sanitized text.
    """
    if not text:
        return ""

    # Strip and normalize whitespace
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Check for injection patterns and log warnings
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"Potential prompt injection detected and neutralized: {text[:100]}..."
            )
            # Replace the matched pattern with a neutralized version
            text = pattern.sub("[FILTERED]", text)

    # Escape angle brackets to prevent HTML/XML injection in prompts
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return text


def contains_injection_attempt(text: str) -> bool:
    """
    Check if text contains potential prompt injection attempts.

    Args:
        text: The text to check.

    Returns:
        True if injection patterns are detected, False otherwise.
    """
    if not text:
        return False

    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_for_log(text: str, max_length: int = 30) -> str:
    """
    Sanitize text for logging - truncate and remove sensitive patterns.

    Args:
        text: The text to sanitize.
        max_length: Maximum length before truncation.

    Returns:
        The sanitized text suitable for logging.
    """
    if not text:
        return "[empty]"
    # Truncate and add ellipsis
    sanitized = text[:max_length] + "..." if len(text) > max_length else text
    # Remove newlines and excessive whitespace
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized
