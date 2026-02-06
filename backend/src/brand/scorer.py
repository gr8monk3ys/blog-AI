"""
Voice Consistency Scorer.

Scores generated content against a trained brand voice fingerprint.
"""

import re
import json
from typing import Any, Dict, List, Optional

from src.text_generation.core import GenerationOptions, generate_text, create_provider_from_env
from src.brand.analyzer import VoiceAnalyzer
from src.types.brand import (
    VoiceFingerprint,
    VoiceScore,
    SampleAnalysis,
    ContentType,
)


class VoiceScorer:
    """Scores content for consistency with a brand voice fingerprint."""

    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        self.provider = create_provider_from_env(provider_type)
        self.analyzer = VoiceAnalyzer(provider_type)
        self.options = GenerationOptions(
            temperature=0.2,
            max_tokens=1500,
            top_p=0.9,
        )

    def score(
        self,
        content: str,
        fingerprint: VoiceFingerprint,
        content_type: ContentType = ContentType.TEXT,
    ) -> VoiceScore:
        """Score content against the voice fingerprint."""
        # Analyze the content
        analysis = self.analyzer.analyze(content, content_type)

        # Calculate component scores
        vocabulary_match = self._score_vocabulary(analysis, fingerprint)
        tone_match = self._score_tone(analysis, fingerprint)
        style_match = self._score_style(analysis, fingerprint)

        # Overall score (weighted average)
        overall_score = (
            vocabulary_match * 0.25 +
            tone_match * 0.40 +
            style_match * 0.35
        )

        # Identify deviations and suggestions
        deviations, suggestions = self._identify_improvements(
            analysis, fingerprint, content
        )

        # Get detailed feedback from LLM
        feedback = self._get_llm_feedback(
            content, fingerprint, analysis, overall_score
        )

        return VoiceScore(
            overall_score=round(overall_score, 3),
            tone_match=round(tone_match, 3),
            vocabulary_match=round(vocabulary_match, 3),
            style_match=round(style_match, 3),
            feedback=feedback,
            deviations=deviations,
            suggestions=suggestions,
        )

    def _score_vocabulary(
        self,
        analysis: SampleAnalysis,
        fingerprint: VoiceFingerprint,
    ) -> float:
        """Score vocabulary consistency."""
        fp_vocab = fingerprint.vocabulary_profile
        content_vocab = analysis.vocabulary

        score = 0.0

        # Word length similarity (within 0.5 of target = full points)
        length_diff = abs(fp_vocab.avg_word_length - content_vocab.avg_word_length)
        if length_diff <= 0.5:
            score += 0.25
        elif length_diff <= 1.0:
            score += 0.15

        # Vocabulary richness similarity
        richness_diff = abs(fp_vocab.vocabulary_richness - content_vocab.vocabulary_richness)
        if richness_diff <= 0.1:
            score += 0.25
        elif richness_diff <= 0.2:
            score += 0.15

        # Uses common words from fingerprint
        fp_common = set(fp_vocab.common_words)
        content_words = set(content_vocab.common_words)
        if fp_common:
            overlap = len(fp_common & content_words) / len(fp_common)
            score += overlap * 0.25

        # Formality alignment
        fp_has_formal = len(fp_vocab.formality_indicators) > 0
        fp_has_casual = len(fp_vocab.casual_indicators) > 0
        content_has_formal = len(content_vocab.formality_indicators) > 0
        content_has_casual = len(content_vocab.casual_indicators) > 0

        if fp_has_formal == content_has_formal and fp_has_casual == content_has_casual:
            score += 0.25
        elif fp_has_formal == content_has_formal or fp_has_casual == content_has_casual:
            score += 0.15

        return min(1.0, score)

    def _score_tone(
        self,
        analysis: SampleAnalysis,
        fingerprint: VoiceFingerprint,
    ) -> float:
        """Score tone consistency."""
        fp_tone = fingerprint.tone_distribution.model_dump()
        content_tone = analysis.tone.model_dump()

        # Calculate cosine-like similarity
        dot_product = 0.0
        fp_magnitude = 0.0
        content_magnitude = 0.0

        for key in fp_tone:
            fp_val = fp_tone[key]
            content_val = content_tone.get(key, 0.0)

            dot_product += fp_val * content_val
            fp_magnitude += fp_val ** 2
            content_magnitude += content_val ** 2

        if fp_magnitude == 0 or content_magnitude == 0:
            return 0.5  # Neutral if no data

        similarity = dot_product / ((fp_magnitude ** 0.5) * (content_magnitude ** 0.5))
        return similarity

    def _score_style(
        self,
        analysis: SampleAnalysis,
        fingerprint: VoiceFingerprint,
    ) -> float:
        """Score style consistency."""
        fp_style = fingerprint.style_metrics
        content_style = analysis.style

        score = 0.0

        # Formality alignment (within 0.2 = good)
        formality_diff = abs(fp_style.formality_score - content_style.formality_score)
        if formality_diff <= 0.15:
            score += 0.3
        elif formality_diff <= 0.3:
            score += 0.2

        # Complexity alignment
        complexity_diff = abs(fp_style.complexity_score - content_style.complexity_score)
        if complexity_diff <= 0.2:
            score += 0.25
        elif complexity_diff <= 0.4:
            score += 0.15

        # Engagement alignment
        engagement_diff = abs(fp_style.engagement_score - content_style.engagement_score)
        if engagement_diff <= 0.2:
            score += 0.25
        elif engagement_diff <= 0.4:
            score += 0.15

        # Sentence structure similarity
        fp_sentences = fingerprint.sentence_patterns
        content_sentences = analysis.sentences

        length_diff = abs(
            fp_sentences.avg_sentence_length - content_sentences.avg_sentence_length
        )
        if length_diff <= 3:
            score += 0.2
        elif length_diff <= 6:
            score += 0.1

        return min(1.0, score)

    def _identify_improvements(
        self,
        analysis: SampleAnalysis,
        fingerprint: VoiceFingerprint,
        content: str,
    ) -> tuple[List[str], List[str]]:
        """Identify deviations and generate improvement suggestions."""
        deviations: List[str] = []
        suggestions: List[str] = []

        fp_style = fingerprint.style_metrics
        fp_tone = fingerprint.tone_distribution
        fp_sentences = fingerprint.sentence_patterns

        content_style = analysis.style
        content_tone = analysis.tone
        content_sentences = analysis.sentences

        # Check formality
        if abs(fp_style.formality_score - content_style.formality_score) > 0.3:
            if fp_style.formality_score > content_style.formality_score:
                deviations.append("Content is more casual than brand voice")
                suggestions.append("Use more formal language and professional terminology")
            else:
                deviations.append("Content is more formal than brand voice")
                suggestions.append("Use more conversational language and contractions")

        # Check sentence length
        if abs(fp_sentences.avg_sentence_length - content_sentences.avg_sentence_length) > 5:
            if fp_sentences.avg_sentence_length > content_sentences.avg_sentence_length:
                deviations.append("Sentences are shorter than typical brand content")
                suggestions.append("Combine some short sentences for more flow")
            else:
                deviations.append("Sentences are longer than typical brand content")
                suggestions.append("Break up long sentences for better readability")

        # Check engagement elements
        if fp_sentences.question_frequency > 0.1 and content_sentences.question_frequency < 0.05:
            deviations.append("Missing engaging questions")
            suggestions.append("Add rhetorical questions to engage readers")

        # Check tone alignment
        top_fp_tones = sorted(
            fp_tone.model_dump().items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        for tone_name, fp_value in top_fp_tones:
            content_value = getattr(content_tone, tone_name, 0.0)
            if fp_value > 0.5 and content_value < 0.3:
                deviations.append(f"Missing {tone_name} tone")
                suggestions.append(f"Add more {tone_name} elements to match brand voice")

        return deviations, suggestions

    def _get_llm_feedback(
        self,
        content: str,
        fingerprint: VoiceFingerprint,
        analysis: SampleAnalysis,
        overall_score: float,
    ) -> Dict[str, Any]:
        """Get detailed feedback from LLM."""
        # Truncate content if needed
        content_excerpt = content[:1500] if len(content) > 1500 else content

        prompt = f"""Analyze this content for brand voice consistency and provide specific feedback.

BRAND VOICE SUMMARY:
{fingerprint.voice_summary}

CONTENT TO REVIEW:
{content_excerpt}

SCORE: {overall_score:.0%}

Provide feedback in this JSON format:
{{
    "strengths": ["What the content does well matching the voice"],
    "improvements": ["Specific things to change"],
    "example_rewrites": [
        {{
            "original": "A sentence from the content",
            "suggested": "How it could be rewritten to match voice"
        }}
    ],
    "grade": "A/B/C/D/F"
}}

Return ONLY the JSON."""

        try:
            response = generate_text(prompt, self.provider, self.options)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Feedback generation error: {e}")

        # Fallback feedback
        grade = (
            "A" if overall_score >= 0.85
            else "B" if overall_score >= 0.7
            else "C" if overall_score >= 0.5
            else "D"
        )
        return {
            "strengths": ["Content analyzed"],
            "improvements": [],
            "example_rewrites": [],
            "grade": grade,
        }


def score_content(
    content: str,
    fingerprint: VoiceFingerprint,
    content_type: ContentType = ContentType.TEXT,
    provider_type: str = "openai",
) -> VoiceScore:
    """Convenience function to score content."""
    scorer = VoiceScorer(provider_type)
    return scorer.score(content, fingerprint, content_type)
