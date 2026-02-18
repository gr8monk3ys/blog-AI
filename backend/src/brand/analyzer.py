"""
Voice Sample Analyzer.

Extracts vocabulary, sentence patterns, tone, and style from content samples.
"""

import hashlib
import json
import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional

from src.utils.cache import get_voice_analysis_cache

logger = logging.getLogger(__name__)

from src.text_generation.core import GenerationOptions, generate_text, create_provider_from_env
from src.types.brand import (
    SampleAnalysis,
    VocabularyProfile,
    SentencePatterns,
    ToneDistribution,
    StyleMetrics,
    ContentType,
)


class VoiceAnalyzer:
    """Analyzes content samples to extract voice characteristics."""

    # Configuration constants
    MAX_CONTENT_LENGTH = 3000
    MAX_TOKENS = 2000
    ANALYSIS_TEMPERATURE = 0.2

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

    def _get_content_hash(self, content: str, content_type: ContentType) -> str:
        """Generate a hash key for caching based on content."""
        content_key = f"{content[:500]}:{content_type.value}:{self.provider_type}"
        return hashlib.sha256(content_key.encode()).hexdigest()[:16]

    def analyze(
        self,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        use_cache: bool = True,
    ) -> SampleAnalysis:
        """Analyze a content sample for voice characteristics."""
        # Basic text analysis (fast, local)
        vocabulary = self._analyze_vocabulary(content)
        sentences = self._analyze_sentences(content)

        # Check cache for LLM analysis
        cache = get_voice_analysis_cache()
        cache_key = self._get_content_hash(content, content_type)

        llm_analysis = None
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Using cached voice analysis: %s", cache_key)
                llm_analysis = cached_result

        # LLM-powered deep analysis if not cached
        if llm_analysis is None:
            llm_analysis = self._llm_analyze(content, content_type)
            if use_cache:
                cache.set(cache_key, llm_analysis, ttl_seconds=3600)  # 1 hour TTL
                logger.debug("Cached voice analysis: %s", cache_key)

        # Merge results
        tone = llm_analysis.get("tone", ToneDistribution())
        style = llm_analysis.get("style", StyleMetrics())
        key_characteristics = llm_analysis.get("key_characteristics", [])

        # Calculate quality score based on sample richness
        quality_score = self._calculate_quality_score(
            content, vocabulary, sentences
        )

        return SampleAnalysis(
            vocabulary=vocabulary,
            sentences=sentences,
            tone=tone,
            style=style,
            key_characteristics=key_characteristics,
            quality_score=quality_score,
        )

    def _analyze_vocabulary(self, content: str) -> VocabularyProfile:
        """Analyze vocabulary patterns."""
        # Tokenize
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        if not words:
            return VocabularyProfile()

        # Word frequency
        word_counts = Counter(words)
        common_words = [word for word, _ in word_counts.most_common(20)]

        # Unique phrases (2-3 word combinations)
        phrases = self._extract_phrases(content)

        # Calculate metrics
        avg_word_length = sum(len(w) for w in words) / len(words)
        unique_words = len(set(words))
        vocabulary_richness = unique_words / len(words) if words else 0

        # Detect formality indicators
        formal_words = [
            "therefore", "consequently", "furthermore", "however",
            "nevertheless", "accordingly", "moreover", "hence",
            "whereas", "notwithstanding", "thus", "regarding"
        ]
        casual_words = [
            "gonna", "wanna", "kinda", "sorta", "cool", "awesome",
            "yeah", "nope", "hey", "stuff", "thing", "guys"
        ]

        formality_found = [w for w in words if w in formal_words]
        casual_found = [w for w in words if w in casual_words]

        return VocabularyProfile(
            common_words=common_words,
            unique_phrases=phrases[:10],
            avg_word_length=round(avg_word_length, 2),
            vocabulary_richness=round(vocabulary_richness, 3),
            formality_indicators=list(set(formality_found)),
            casual_indicators=list(set(casual_found)),
        )

    def _extract_phrases(self, content: str) -> List[str]:
        """Extract meaningful 2-3 word phrases."""
        # Simple n-gram extraction
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        phrases: List[str] = []

        # Bigrams
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                phrases.append(phrase)

        # Count and get most common
        phrase_counts = Counter(phrases)
        return [p for p, c in phrase_counts.most_common(15) if c > 1]

    def _analyze_sentences(self, content: str) -> SentencePatterns:
        """Analyze sentence structure patterns."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return SentencePatterns()

        # Calculate metrics
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)

        # Variance
        variance = sum(
            (l - avg_length) ** 2 for l in sentence_lengths
        ) / len(sentence_lengths) if len(sentence_lengths) > 1 else 0

        # Question and exclamation frequency
        question_count = content.count('?')
        exclamation_count = content.count('!')
        total_sentences = len(sentences)

        question_freq = question_count / total_sentences if total_sentences else 0
        exclamation_freq = exclamation_count / total_sentences if total_sentences else 0

        # Complex sentences (with commas, semicolons)
        complex_count = sum(1 for s in sentences if ',' in s or ';' in s)
        complex_ratio = complex_count / total_sentences if total_sentences else 0

        # Opening patterns
        openings = []
        for s in sentences[:20]:  # First 20 sentences
            words = s.split()[:3]
            if words:
                openings.append(' '.join(words))

        # Common transition words
        transitions = [
            "however", "therefore", "moreover", "furthermore",
            "additionally", "consequently", "meanwhile", "similarly",
            "in contrast", "on the other hand", "for example",
            "in addition", "as a result", "in conclusion"
        ]
        content_lower = content.lower()
        found_transitions = [t for t in transitions if t in content_lower]

        return SentencePatterns(
            avg_sentence_length=round(avg_length, 1),
            sentence_length_variance=round(variance, 2),
            question_frequency=round(question_freq, 3),
            exclamation_frequency=round(exclamation_freq, 3),
            complex_sentence_ratio=round(complex_ratio, 3),
            opening_patterns=list(set(openings))[:10],
            transition_words=found_transitions,
        )

    def _llm_analyze(
        self,
        content: str,
        content_type: ContentType,
    ) -> Dict[str, Any]:
        """Use LLM for deep tone and style analysis."""
        # Truncate if too long
        truncated = content[:self.MAX_CONTENT_LENGTH] + "..." if len(content) > self.MAX_CONTENT_LENGTH else content

        # Sanitize to prevent prompt injection
        sanitized = self._sanitize_for_prompt(truncated)

        prompt = f"""Analyze this {content_type.value} content for voice and style characteristics.

CONTENT:
{sanitized}

Provide analysis in this exact JSON format:
{{
    "tone": {{
        "professional": 0.0-1.0,
        "friendly": 0.0-1.0,
        "casual": 0.0-1.0,
        "authoritative": 0.0-1.0,
        "empathetic": 0.0-1.0,
        "enthusiastic": 0.0-1.0,
        "confident": 0.0-1.0,
        "approachable": 0.0-1.0,
        "innovative": 0.0-1.0,
        "trustworthy": 0.0-1.0,
        "playful": 0.0-1.0,
        "serious": 0.0-1.0
    }},
    "style": {{
        "formality_score": 0.0-1.0 (0=casual, 1=formal),
        "complexity_score": 0.0-1.0 (reading level),
        "engagement_score": 0.0-1.0 (hooks, CTAs, questions),
        "personality_score": 0.0-1.0 (distinctiveness),
        "consistency_score": 0.0-1.0 (internal consistency)
    }},
    "key_characteristics": [
        "characteristic 1",
        "characteristic 2",
        "characteristic 3"
    ]
}}

Return ONLY the JSON, no other text."""

        try:
            response = generate_text(prompt, self.provider, self.options)
        except Exception as e:
            # Brand voice analysis should degrade gracefully when LLM calls fail
            # (e.g., missing keys, network issues, or mocked providers in tests).
            logger.warning("LLM analysis failed: %s", e)
            return {}

        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return {}

            data = json.loads(json_match.group())

            # Parse tone
            tone_data = data.get("tone", {})
            tone = ToneDistribution(**{
                k: float(v) for k, v in tone_data.items()
                if k in ToneDistribution.model_fields
            })

            # Parse style
            style_data = data.get("style", {})
            style = StyleMetrics(**{
                k: float(v) for k, v in style_data.items()
                if k in StyleMetrics.model_fields
            })

            return {
                "tone": tone,
                "style": style,
                "key_characteristics": data.get("key_characteristics", []),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("LLM analysis parse error: %s", e)
            return {}

    def _calculate_quality_score(
        self,
        content: str,
        vocabulary: VocabularyProfile,
        sentences: SentencePatterns,
    ) -> float:
        """Calculate sample quality score for training."""
        score = 0.0

        # Word count (50-2000 words is ideal)
        word_count = len(content.split())
        if 50 <= word_count <= 2000:
            score += 0.3
        elif 30 <= word_count < 50 or 2000 < word_count <= 3000:
            score += 0.15

        # Vocabulary richness (higher is better)
        if vocabulary.vocabulary_richness > 0.4:
            score += 0.2
        elif vocabulary.vocabulary_richness > 0.3:
            score += 0.1

        # Has variety in sentence structure
        if sentences.sentence_length_variance > 10:
            score += 0.15
        elif sentences.sentence_length_variance > 5:
            score += 0.1

        # Has engagement elements
        if sentences.question_frequency > 0.1:
            score += 0.1

        # Has transition words (coherent writing)
        if len(sentences.transition_words) >= 2:
            score += 0.15
        elif len(sentences.transition_words) >= 1:
            score += 0.1

        # Reasonable sentence length (not too short or long)
        if 10 <= sentences.avg_sentence_length <= 25:
            score += 0.1

        return min(1.0, score)


def analyze_sample(
    content: str,
    content_type: ContentType = ContentType.TEXT,
    provider_type: str = "openai",
) -> SampleAnalysis:
    """Convenience function to analyze a sample."""
    analyzer = VoiceAnalyzer(provider_type)
    return analyzer.analyze(content, content_type)
