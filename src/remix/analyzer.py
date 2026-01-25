"""
Content Analyzer for the Remix Engine.

Analyzes source content to extract structure, key points, and metadata
for intelligent transformation across formats.
"""

import hashlib
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from src.text_generation.core import GenerationOptions, generate_text, create_provider_from_env
from src.types.remix import (
    ContentAnalysis,
    ContentChunk,
    ContentFormat,
    FORMAT_METADATA,
)
from src.utils.cache import get_content_analysis_cache

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes content for remix transformation."""

    # Configuration constants
    MAX_BODY_LENGTH = 4000
    MAX_TOKENS = 2000
    ANALYSIS_TEMPERATURE = 0.3

    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        self.provider = create_provider_from_env(provider_type)
        self.options = GenerationOptions(
            temperature=self.ANALYSIS_TEMPERATURE,
            max_tokens=self.MAX_TOKENS,
            top_p=0.9,
        )

    def _sanitize_for_prompt(self, text: str) -> str:
        """Sanitize text to prevent prompt injection attacks."""
        if not text:
            return ""
        # Remove potential prompt injection patterns
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard above",
            "forget everything",
            "new instructions:",
            "system:",
            "assistant:",
            "user:",
        ]
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(
                re.escape(pattern),
                "[REDACTED]",
                sanitized,
                flags=re.IGNORECASE
            )
        return sanitized

    def _get_content_hash(self, title: str, body: str) -> str:
        """Generate a hash key for caching based on content."""
        content_key = f"{title}:{body[:1000]}:{self.provider_type}"
        return hashlib.sha256(content_key.encode()).hexdigest()[:16]

    def analyze(self, content: Dict[str, Any], use_cache: bool = True) -> ContentAnalysis:
        """Analyze content and extract structure for transformation."""
        # Extract text content
        title = content.get("title", "Untitled")
        body = self._extract_body(content)

        # Get word count
        word_count = len(body.split())

        # Extract chunks from content structure
        chunks = self._extract_chunks(content)

        # Check cache for LLM analysis
        cache = get_content_analysis_cache()
        cache_key = self._get_content_hash(title, body)

        parsed = None
        if use_cache:
            cached_analysis = cache.get(cache_key)
            if cached_analysis is not None:
                logger.debug("Using cached analysis for content: %s", cache_key)
                parsed = cached_analysis

        # Use LLM for deeper analysis if not cached
        if parsed is None:
            analysis_prompt = self._create_analysis_prompt(title, body)
            analysis_response = generate_text(analysis_prompt, self.provider, self.options)
            parsed = self._parse_analysis(analysis_response)

            # Cache the result
            if use_cache:
                cache.set(cache_key, parsed, ttl_seconds=1800)  # 30 min TTL
                logger.debug("Cached analysis for content: %s", cache_key)

        # Suggest formats based on content
        suggested_formats = self._suggest_formats(word_count, chunks, parsed)

        return ContentAnalysis(
            title=title,
            summary=parsed.get("summary", body[:500]),
            key_points=parsed.get("key_points", []),
            main_argument=parsed.get("main_argument", ""),
            target_audience=parsed.get("target_audience", "general"),
            tone=parsed.get("tone", "professional"),
            word_count=word_count,
            chunks=chunks,
            keywords=parsed.get("keywords", []),
            suggested_formats=suggested_formats,
        )

    def _extract_body(self, content: Dict[str, Any]) -> str:
        """Extract the main body text from content."""
        # Handle different content structures
        if "body" in content:
            return content["body"]
        if "content" in content:
            return content["content"]
        if "sections" in content:
            sections = content["sections"]
            if isinstance(sections, list):
                return "\n\n".join(
                    s.get("content", "") if isinstance(s, dict) else str(s)
                    for s in sections
                )
        if "text" in content:
            return content["text"]

        # Fallback: concatenate all string values
        texts = []
        for key, value in content.items():
            if isinstance(value, str) and key not in ["title", "id", "slug"]:
                texts.append(value)
        return "\n\n".join(texts)

    def _extract_chunks(self, content: Dict[str, Any]) -> List[ContentChunk]:
        """Extract meaningful chunks from content structure."""
        chunks: List[ContentChunk] = []

        # Extract from sections if available
        if "sections" in content:
            for i, section in enumerate(content["sections"]):
                if isinstance(section, dict):
                    chunk = ContentChunk(
                        id=str(uuid.uuid4()),
                        type="section",
                        content=section.get("content", ""),
                        importance=1.0 - (i * 0.1),  # Earlier sections slightly more important
                        word_count=len(section.get("content", "").split()),
                        source_section=section.get("title", f"Section {i+1}"),
                    )
                    chunks.append(chunk)

        # Extract from body text using structure detection
        body = self._extract_body(content)
        if body and not chunks:
            chunks = self._chunk_by_structure(body)

        return chunks

    def _chunk_by_structure(self, text: str) -> List[ContentChunk]:
        """Split text into chunks based on structural elements."""
        chunks: List[ContentChunk] = []

        # Split by headers (Markdown style)
        # Using non-greedy quantifier to prevent ReDoS
        header_pattern = r'^(#{1,3})\s+(.+?)$'
        current_section = None
        current_content = []

        for line in text.split('\n'):
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save previous section
                if current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        chunks.append(ContentChunk(
                            id=str(uuid.uuid4()),
                            type="heading" if len(current_content) == 1 else "paragraph",
                            content=content_text,
                            importance=0.8,
                            word_count=len(content_text.split()),
                            source_section=current_section,
                        ))
                current_section = header_match.group(2)
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                chunks.append(ContentChunk(
                    id=str(uuid.uuid4()),
                    type="paragraph",
                    content=content_text,
                    importance=0.7,
                    word_count=len(content_text.split()),
                    source_section=current_section,
                ))

        # If no structure found, chunk by paragraphs
        if not chunks:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for i, para in enumerate(paragraphs):
                importance = 1.0 if i == 0 else (0.9 if i < 3 else 0.7)
                chunks.append(ContentChunk(
                    id=str(uuid.uuid4()),
                    type="paragraph",
                    content=para,
                    importance=importance,
                    word_count=len(para.split()),
                    source_section=None,
                ))

        # Score chunks for key points
        chunks = self._score_chunks(chunks)

        return chunks

    def _score_chunks(self, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """Score chunks for importance based on content analysis."""
        key_indicators = [
            "important", "key", "crucial", "essential", "remember",
            "note that", "in summary", "the main", "ultimately",
            "first", "second", "third", "finally",
        ]

        for chunk in chunks:
            content_lower = chunk.content.lower()

            # Boost score for chunks with key indicators
            for indicator in key_indicators:
                if indicator in content_lower:
                    chunk.importance = min(1.0, chunk.importance + 0.1)

            # Boost for list items (likely key points)
            if re.search(r'^[\d\-\*\•]', chunk.content.strip()):
                chunk.type = "list"
                chunk.importance = min(1.0, chunk.importance + 0.15)

            # Boost for quotes
            if chunk.content.startswith('"') or chunk.content.startswith("'"):
                chunk.type = "quote"
                chunk.importance = min(1.0, chunk.importance + 0.1)

        return chunks

    def _create_analysis_prompt(self, title: str, body: str) -> str:
        """Create prompt for LLM content analysis."""
        # Truncate body if too long
        truncated_body = body[:self.MAX_BODY_LENGTH] + "..." if len(body) > self.MAX_BODY_LENGTH else body

        # Sanitize inputs to prevent prompt injection
        sanitized_title = self._sanitize_for_prompt(title)
        sanitized_body = self._sanitize_for_prompt(truncated_body)

        return f"""Analyze this content and extract structured information.

TITLE: {sanitized_title}

CONTENT:
{sanitized_body}

Provide analysis in this exact JSON format:
{{
    "summary": "2-3 sentence summary of the main content",
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
    "main_argument": "The central thesis or main argument being made",
    "target_audience": "Who this content is written for",
    "tone": "The writing tone (professional, casual, educational, etc.)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}

Return ONLY the JSON, no other text."""

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM analysis response."""
        import json

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback: return empty analysis
        return {
            "summary": "",
            "key_points": [],
            "main_argument": "",
            "target_audience": "general",
            "tone": "professional",
            "keywords": [],
        }

    def _suggest_formats(
        self,
        word_count: int,
        chunks: List[ContentChunk],
        parsed: Dict[str, Any],
    ) -> List[ContentFormat]:
        """Suggest appropriate output formats based on content analysis."""
        suggestions: List[ContentFormat] = []

        # Always suggest these popular formats
        suggestions.append(ContentFormat.TWITTER_THREAD)
        suggestions.append(ContentFormat.LINKEDIN_POST)

        # Email newsletter for longer content
        if word_count > 500:
            suggestions.append(ContentFormat.EMAIL_NEWSLETTER)

        # YouTube script for educational/how-to content
        tone = parsed.get("tone", "").lower()
        if "educational" in tone or "tutorial" in tone or word_count > 1000:
            suggestions.append(ContentFormat.YOUTUBE_SCRIPT)

        # Instagram for content with clear visual points
        if len(parsed.get("key_points", [])) >= 5:
            suggestions.append(ContentFormat.INSTAGRAM_CAROUSEL)

        # Podcast notes for in-depth content
        if word_count > 1500:
            suggestions.append(ContentFormat.PODCAST_NOTES)

        # TikTok for short, punchy content
        if word_count < 500 or "casual" in tone:
            suggestions.append(ContentFormat.TIKTOK_SCRIPT)

        # Executive summary for business content
        audience = parsed.get("target_audience", "").lower()
        if "executive" in audience or "business" in audience or "professional" in audience:
            suggestions.append(ContentFormat.EXECUTIVE_SUMMARY)

        return suggestions[:6]  # Limit to 6 suggestions


def analyze_content(
    content: Dict[str, Any],
    provider_type: str = "openai",
) -> ContentAnalysis:
    """Convenience function to analyze content."""
    analyzer = ContentAnalyzer(provider_type)
    return analyzer.analyze(content)
