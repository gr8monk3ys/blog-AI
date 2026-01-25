"""
Content scoring functionality for evaluating generated content.

This module provides scoring algorithms for:
- Readability (Flesch-Kincaid, sentence complexity)
- SEO (keyword density, structure, length)
- Engagement (hooks, CTAs, emotional words)
"""

import math
import re
from typing import Dict, List, Optional, Set

from ..types.scoring import (
    ContentScoreResult,
    EngagementScore,
    ReadabilityScore,
    ScoreLevel,
    SEOScore,
)


# Common emotional/power words for engagement scoring
EMOTIONAL_WORDS: Set[str] = {
    # Urgency
    "now", "today", "immediately", "instant", "hurry", "limited", "deadline",
    "urgent", "fast", "quick", "soon", "expires",
    # Exclusivity
    "exclusive", "secret", "insider", "members", "private", "limited",
    "invitation", "vip", "elite",
    # Value
    "free", "bonus", "save", "discount", "value", "bargain", "cheap",
    "affordable", "priceless", "guarantee",
    # Trust
    "proven", "certified", "guaranteed", "authentic", "official", "verified",
    "trusted", "reliable", "secure", "safe",
    # Emotion
    "amazing", "incredible", "stunning", "breathtaking", "remarkable",
    "extraordinary", "exceptional", "outstanding", "magnificent", "spectacular",
    "shocking", "surprising", "unexpected", "astonishing", "mind-blowing",
    "love", "hate", "fear", "joy", "excited", "thrilled", "passionate",
    # Action
    "discover", "unlock", "transform", "boost", "skyrocket", "master",
    "dominate", "conquer", "achieve", "succeed", "win", "crush", "explode",
}

# CTA phrases
CTA_PATTERNS: List[str] = [
    r"click\s+here",
    r"sign\s+up",
    r"get\s+started",
    r"learn\s+more",
    r"download\s+now",
    r"subscribe",
    r"join\s+(now|us|today)",
    r"buy\s+now",
    r"order\s+now",
    r"try\s+(it\s+)?free",
    r"contact\s+us",
    r"get\s+your",
    r"start\s+your",
    r"claim\s+your",
    r"don'?t\s+miss",
    r"act\s+now",
    r"limited\s+time",
    r"reserve\s+your",
    r"book\s+now",
    r"schedule\s+(a|your)",
]

# Storytelling indicators
STORYTELLING_PATTERNS: List[str] = [
    r"\bonce\s+upon\b",
    r"\bi\s+remember\b",
    r"\blet\s+me\s+tell\s+you\b",
    r"\bimagine\s+(if|this|that|a)\b",
    r"\bpicture\s+this\b",
    r"\bhere'?s\s+(the\s+)?story\b",
    r"\bit\s+all\s+started\b",
    r"\bback\s+in\b",
    r"\byears\s+ago\b",
    r"\bwhen\s+i\s+(first|was)\b",
    r"\bmy\s+journey\b",
    r"\bthe\s+moment\b",
    r"\bturning\s+point\b",
]


def _count_syllables(word: str) -> int:
    """
    Estimate syllable count for a word.

    Uses a simple heuristic based on vowel groups.
    """
    word = word.lower().strip()
    if not word:
        return 0

    # Special cases
    if len(word) <= 3:
        return 1

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Handle silent e
    if word.endswith("e") and count > 1:
        count -= 1

    # Handle special endings
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        count += 1

    return max(1, count)


def _get_level(score: float) -> ScoreLevel:
    """Convert numeric score to level classification."""
    if score >= 80:
        return ScoreLevel.EXCELLENT
    elif score >= 60:
        return ScoreLevel.GOOD
    elif score >= 40:
        return ScoreLevel.FAIR
    else:
        return ScoreLevel.POOR


def _extract_words(text: str) -> List[str]:
    """Extract words from text."""
    # Remove markdown formatting
    text = re.sub(r'[#*_`\[\]()]', ' ', text)
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    return words


def _extract_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty sentences
    return [s.strip() for s in sentences if s.strip()]


def score_readability(text: str) -> ReadabilityScore:
    """
    Score content readability using Flesch-Kincaid metrics.

    Args:
        text: Content to analyze.

    Returns:
        ReadabilityScore with detailed metrics and suggestions.
    """
    words = _extract_words(text)
    sentences = _extract_sentences(text)

    word_count = len(words)
    sentence_count = max(1, len(sentences))

    # Calculate metrics
    total_syllables = sum(_count_syllables(word) for word in words)
    avg_syllables_per_word = total_syllables / max(1, word_count)
    avg_words_per_sentence = word_count / sentence_count
    avg_word_length = sum(len(w) for w in words) / max(1, word_count)

    # Count complex words (3+ syllables)
    complex_words = sum(1 for w in words if _count_syllables(w) >= 3)
    complex_percentage = (complex_words / max(1, word_count)) * 100

    # Flesch Reading Ease: 206.835 - 1.015(words/sentences) - 84.6(syllables/words)
    flesch_ease = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    flesch_ease = max(0, min(100, flesch_ease))

    # Flesch-Kincaid Grade Level: 0.39(words/sentences) + 11.8(syllables/words) - 15.59
    fk_grade = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59
    fk_grade = max(0, fk_grade)

    # Convert Flesch ease to 0-100 score (it's already roughly 0-100)
    score = flesch_ease

    # Generate suggestions
    suggestions = []

    if avg_words_per_sentence > 20:
        suggestions.append(
            f"Shorten sentences. Average is {avg_words_per_sentence:.1f} words; aim for under 20."
        )

    if complex_percentage > 15:
        suggestions.append(
            f"Reduce complex words ({complex_percentage:.1f}% have 3+ syllables). Use simpler alternatives."
        )

    if fk_grade > 12:
        suggestions.append(
            f"Content reads at grade level {fk_grade:.1f}. Consider simplifying for broader audience."
        )

    if avg_word_length > 5:
        suggestions.append(
            "Use shorter words where possible to improve readability."
        )

    if not suggestions:
        suggestions.append("Readability is good. Content is accessible to most readers.")

    return ReadabilityScore(
        score=round(score, 1),
        level=_get_level(score),
        flesch_kincaid_grade=round(fk_grade, 1),
        flesch_reading_ease=round(flesch_ease, 1),
        average_sentence_length=round(avg_words_per_sentence, 1),
        average_word_length=round(avg_word_length, 1),
        complex_word_percentage=round(complex_percentage, 1),
        suggestions=suggestions,
    )


def score_seo(text: str, keywords: Optional[List[str]] = None) -> SEOScore:
    """
    Score content for SEO optimization.

    Args:
        text: Content to analyze.
        keywords: Target keywords to check for.

    Returns:
        SEOScore with detailed metrics and suggestions.
    """
    words = _extract_words(text)
    word_count = len(words)
    text_lower = text.lower()

    # Count headings (markdown style)
    heading_count = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))

    # Keyword analysis
    keyword_density = 0.0
    keyword_placement = {}

    if keywords:
        primary_keyword = keywords[0].lower()
        keyword_occurrences = text_lower.count(primary_keyword)
        keyword_density = (keyword_occurrences / max(1, word_count)) * 100

        # Check keyword placement
        lines = text.split('\n')
        first_100_words = ' '.join(words[:100])

        keyword_placement = {
            "in_title": any(
                primary_keyword in line.lower()
                for line in lines
                if line.strip().startswith('#')
            ),
            "in_first_paragraph": primary_keyword in first_100_words,
            "in_headings": any(
                primary_keyword in line.lower()
                for line in lines
                if re.match(r'^#{1,6}\s', line)
            ),
        }

    # Check for meta-like elements
    has_meta = bool(re.search(r'(meta\s*description|summary|tldr|key\s*takeaways)', text_lower))

    # Count potential internal link opportunities (mentions of concepts)
    link_potential = len(re.findall(r'\b(learn|read|see|check|visit|explore)\s+more\b', text_lower))

    # Calculate score components
    scores = []
    suggestions = []

    # Word count scoring (optimal: 1500-2500 words)
    if word_count < 300:
        scores.append(30)
        suggestions.append(f"Content is too short ({word_count} words). Aim for 1000+ words for SEO.")
    elif word_count < 1000:
        scores.append(60)
        suggestions.append(f"Consider expanding content ({word_count} words). 1500+ words often ranks better.")
    elif word_count <= 2500:
        scores.append(100)
    else:
        scores.append(85)
        suggestions.append("Content may be too long. Consider breaking into multiple articles.")

    # Heading structure scoring
    if heading_count == 0:
        scores.append(20)
        suggestions.append("Add headings (H2, H3) to improve structure and SEO.")
    elif heading_count < 3:
        scores.append(60)
        suggestions.append("Add more headings to break up content and improve scannability.")
    else:
        scores.append(100)

    # Keyword density scoring (optimal: 1-2%)
    if keywords:
        if keyword_density < 0.5:
            scores.append(40)
            suggestions.append(f"Keyword density is low ({keyword_density:.2f}%). Use keywords 1-2% of the time.")
        elif keyword_density <= 2.5:
            scores.append(100)
        else:
            scores.append(60)
            suggestions.append(f"Keyword density is high ({keyword_density:.2f}%). Reduce to avoid keyword stuffing.")

        # Keyword placement scoring
        placement_score = sum(keyword_placement.values()) / max(1, len(keyword_placement)) * 100
        scores.append(placement_score)

        if not keyword_placement.get("in_first_paragraph"):
            suggestions.append("Include primary keyword in the first paragraph.")
        if not keyword_placement.get("in_headings"):
            suggestions.append("Include primary keyword in at least one heading.")

    # Calculate overall score
    score = sum(scores) / max(1, len(scores))

    if not suggestions:
        suggestions.append("SEO structure looks good. Content is well-optimized.")

    return SEOScore(
        score=round(score, 1),
        level=_get_level(score),
        keyword_density=round(keyword_density, 2),
        keyword_placement=keyword_placement,
        word_count=word_count,
        heading_count=heading_count,
        has_meta_elements=has_meta,
        internal_link_potential=link_potential,
        suggestions=suggestions,
    )


def score_engagement(text: str) -> EngagementScore:
    """
    Score content for engagement potential.

    Args:
        text: Content to analyze.

    Returns:
        EngagementScore with detailed metrics and suggestions.
    """
    words = _extract_words(text)
    text_lower = text.lower()
    sentences = _extract_sentences(text)

    # Count emotional/power words
    emotional_count = sum(1 for word in words if word in EMOTIONAL_WORDS)

    # Count questions
    question_count = text.count('?')

    # Count CTAs
    cta_count = sum(
        1 for pattern in CTA_PATTERNS
        if re.search(pattern, text_lower)
    )

    # Count lists (bullet points and numbered lists)
    # Using bounded quantifier to prevent ReDoS with whitespace-heavy input
    list_count = len(re.findall(r'^[ \t]{0,20}[-*+]|^\d+[.)]', text, re.MULTILINE))

    # Count storytelling elements
    storytelling_count = sum(
        1 for pattern in STORYTELLING_PATTERNS
        if re.search(pattern, text_lower)
    )

    # Analyze opening hook (first sentence/paragraph)
    first_sentence = sentences[0] if sentences else ""
    hook_strength = 0

    # Hook scoring criteria
    if '?' in first_sentence:
        hook_strength += 25  # Questions engage readers
    if any(word in first_sentence.lower().split() for word in EMOTIONAL_WORDS):
        hook_strength += 25  # Emotional words
    if len(first_sentence.split()) < 20:
        hook_strength += 25  # Concise opening
    if re.search(r'\b(you|your)\b', first_sentence.lower()):
        hook_strength += 25  # Direct address

    hook_strength = min(100, hook_strength)

    # Calculate score components
    suggestions = []
    scores = []

    # Emotional word density scoring
    emotional_density = (emotional_count / max(1, len(words))) * 100
    if emotional_density < 2:
        scores.append(40)
        suggestions.append("Add more power words to create emotional impact.")
    elif emotional_density <= 5:
        scores.append(100)
    else:
        scores.append(80)

    # Question scoring
    if question_count == 0:
        scores.append(50)
        suggestions.append("Add questions to engage readers and encourage reflection.")
    elif question_count <= 5:
        scores.append(100)
    else:
        scores.append(85)

    # CTA scoring
    if cta_count == 0:
        scores.append(40)
        suggestions.append("Add a call-to-action to guide readers on next steps.")
    else:
        scores.append(100)

    # List scoring
    if list_count == 0 and len(words) > 300:
        scores.append(60)
        suggestions.append("Add bullet points or numbered lists to improve scannability.")
    else:
        scores.append(100)

    # Hook scoring
    scores.append(hook_strength)
    if hook_strength < 50:
        suggestions.append("Strengthen your opening hook with a question, statistic, or bold statement.")

    # Storytelling scoring
    if storytelling_count > 0:
        scores.append(100)
    else:
        scores.append(70)
        suggestions.append("Consider adding personal anecdotes or stories to connect with readers.")

    # Calculate overall score
    score = sum(scores) / max(1, len(scores))

    if not suggestions:
        suggestions.append("Engagement is strong. Content has good hooks and CTAs.")

    return EngagementScore(
        score=round(score, 1),
        level=_get_level(score),
        hook_strength=round(hook_strength, 1),
        cta_count=cta_count,
        emotional_word_count=emotional_count,
        question_count=question_count,
        list_count=list_count,
        storytelling_elements=storytelling_count,
        suggestions=suggestions,
    )


def get_overall_score(
    readability: ReadabilityScore,
    seo: SEOScore,
    engagement: EngagementScore,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculate weighted overall score from component scores.

    Args:
        readability: Readability score result.
        seo: SEO score result.
        engagement: Engagement score result.
        weights: Optional custom weights (must sum to 1.0).

    Returns:
        Weighted overall score (0-100).
    """
    if weights is None:
        weights = {
            "readability": 0.30,
            "seo": 0.40,
            "engagement": 0.30,
        }

    overall = (
        readability.score * weights.get("readability", 0.33) +
        seo.score * weights.get("seo", 0.34) +
        engagement.score * weights.get("engagement", 0.33)
    )

    return round(overall, 1)


def score_content(
    text: str,
    keywords: Optional[List[str]] = None,
    content_type: str = "blog",
) -> ContentScoreResult:
    """
    Comprehensive content scoring.

    Args:
        text: Content to analyze.
        keywords: Target keywords for SEO analysis.
        content_type: Type of content (affects weight distribution).

    Returns:
        ContentScoreResult with all metrics and suggestions.
    """
    # Score each dimension
    readability = score_readability(text)
    seo = score_seo(text, keywords)
    engagement = score_engagement(text)

    # Adjust weights based on content type
    weights = {
        "blog": {"readability": 0.30, "seo": 0.40, "engagement": 0.30},
        "email": {"readability": 0.35, "seo": 0.15, "engagement": 0.50},
        "social": {"readability": 0.25, "seo": 0.20, "engagement": 0.55},
        "business": {"readability": 0.40, "seo": 0.30, "engagement": 0.30},
    }.get(content_type, {"readability": 0.33, "seo": 0.34, "engagement": 0.33})

    # Calculate overall score
    overall = get_overall_score(readability, seo, engagement, weights)
    overall_level = _get_level(overall)

    # Compile top improvements (prioritize lowest scoring areas)
    all_suggestions = []

    # Add suggestions from lowest scoring dimension first
    dimension_scores = [
        (readability.score, "Readability", readability.suggestions),
        (seo.score, "SEO", seo.suggestions),
        (engagement.score, "Engagement", engagement.suggestions),
    ]
    dimension_scores.sort(key=lambda x: x[0])

    for _, dimension, suggestions in dimension_scores:
        for suggestion in suggestions[:2]:
            if not suggestion.startswith(("Good", "Readability is good", "SEO structure looks", "Engagement is strong")):
                all_suggestions.append(f"[{dimension}] {suggestion}")

    top_improvements = all_suggestions[:3]

    # Generate summary
    if overall >= 80:
        summary = "Excellent content! Well-optimized across all dimensions."
    elif overall >= 60:
        summary = "Good content with room for improvement. Focus on the suggestions below."
    elif overall >= 40:
        summary = "Content needs work. Address the top improvements to boost performance."
    else:
        summary = "Content requires significant improvement across multiple areas."

    return ContentScoreResult(
        overall_score=overall,
        overall_level=overall_level,
        readability=readability,
        seo=seo,
        engagement=engagement,
        summary=summary,
        top_improvements=top_improvements,
    )


class ContentScorer:
    """
    Content scorer class for analyzing generated content.

    Provides methods for scoring readability, SEO, and engagement,
    with configurable weights and content type handling.
    """

    def __init__(
        self,
        default_keywords: Optional[List[str]] = None,
        default_content_type: str = "blog",
    ):
        """
        Initialize the content scorer.

        Args:
            default_keywords: Default keywords for SEO analysis.
            default_content_type: Default content type for weight calculation.
        """
        self.default_keywords = default_keywords or []
        self.default_content_type = default_content_type

    def score(
        self,
        text: str,
        keywords: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> ContentScoreResult:
        """
        Score content comprehensively.

        Args:
            text: Content to analyze.
            keywords: Keywords for SEO (uses defaults if not provided).
            content_type: Content type (uses default if not provided).

        Returns:
            Complete content score result.
        """
        return score_content(
            text=text,
            keywords=keywords or self.default_keywords,
            content_type=content_type or self.default_content_type,
        )

    def score_readability(self, text: str) -> ReadabilityScore:
        """Score only readability."""
        return score_readability(text)

    def score_seo(
        self,
        text: str,
        keywords: Optional[List[str]] = None,
    ) -> SEOScore:
        """Score only SEO."""
        return score_seo(text, keywords or self.default_keywords)

    def score_engagement(self, text: str) -> EngagementScore:
        """Score only engagement."""
        return score_engagement(text)
