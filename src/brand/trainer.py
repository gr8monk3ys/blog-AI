"""
Voice Profile Trainer.

Aggregates sample analyses into a unified voice fingerprint for content generation.
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from src.text_generation.core import GenerationOptions, generate_text, create_provider_from_env
from src.brand.analyzer import VoiceAnalyzer
from src.types.brand import (
    SampleAnalysis,
    VoiceFingerprint,
    VocabularyProfile,
    SentencePatterns,
    ToneDistribution,
    StyleMetrics,
    VoiceSample,
    ContentType,
)


class VoiceTrainer:
    """Trains voice fingerprints from analyzed samples."""

    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        self.provider = create_provider_from_env(provider_type)
        self.analyzer = VoiceAnalyzer(provider_type)
        self.options = GenerationOptions(
            temperature=0.3,
            max_tokens=1500,
            top_p=0.9,
        )

    def train(
        self,
        profile_id: str,
        samples: List[VoiceSample],
    ) -> VoiceFingerprint:
        """Train a voice fingerprint from samples."""
        if not samples:
            return VoiceFingerprint(
                id="",
                profile_id=profile_id,
                sample_count=0,
            )

        # Analyze samples that haven't been analyzed
        analyses: List[SampleAnalysis] = []
        for sample in samples:
            if sample.analysis_result:
                analyses.append(sample.analysis_result)
            else:
                analysis = self.analyzer.analyze(
                    sample.content,
                    sample.content_type,
                )
                analyses.append(analysis)

        # Aggregate analyses
        vocabulary = self._aggregate_vocabulary(analyses)
        sentences = self._aggregate_sentences(analyses)
        tone = self._aggregate_tone(analyses)
        style = self._aggregate_style(analyses)

        # Calculate training quality
        quality_scores = [a.quality_score for a in analyses]
        training_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        # Generate voice summary using LLM
        voice_summary = self._generate_voice_summary(
            vocabulary, sentences, tone, style, samples
        )

        return VoiceFingerprint(
            id="",  # Will be set by database
            profile_id=profile_id,
            vocabulary_profile=vocabulary,
            sentence_patterns=sentences,
            tone_distribution=tone,
            style_metrics=style,
            voice_summary=voice_summary,
            sample_count=len(samples),
            training_quality=round(training_quality, 3),
        )

    def _aggregate_vocabulary(
        self,
        analyses: List[SampleAnalysis],
    ) -> VocabularyProfile:
        """Aggregate vocabulary profiles from multiple samples."""
        all_common_words: List[str] = []
        all_phrases: List[str] = []
        word_lengths: List[float] = []
        richness_scores: List[float] = []
        all_formal: List[str] = []
        all_casual: List[str] = []

        for analysis in analyses:
            v = analysis.vocabulary
            all_common_words.extend(v.common_words)
            all_phrases.extend(v.unique_phrases)
            word_lengths.append(v.avg_word_length)
            richness_scores.append(v.vocabulary_richness)
            all_formal.extend(v.formality_indicators)
            all_casual.extend(v.casual_indicators)

        # Get most common across all samples
        word_counts = Counter(all_common_words)
        phrase_counts = Counter(all_phrases)

        return VocabularyProfile(
            common_words=[w for w, _ in word_counts.most_common(30)],
            unique_phrases=[p for p, _ in phrase_counts.most_common(15)],
            avg_word_length=round(
                sum(word_lengths) / len(word_lengths), 2
            ) if word_lengths else 0.0,
            vocabulary_richness=round(
                sum(richness_scores) / len(richness_scores), 3
            ) if richness_scores else 0.0,
            formality_indicators=list(set(all_formal)),
            casual_indicators=list(set(all_casual)),
        )

    def _aggregate_sentences(
        self,
        analyses: List[SampleAnalysis],
    ) -> SentencePatterns:
        """Aggregate sentence patterns from multiple samples."""
        avg_lengths: List[float] = []
        variances: List[float] = []
        question_freqs: List[float] = []
        exclamation_freqs: List[float] = []
        complex_ratios: List[float] = []
        all_openings: List[str] = []
        all_transitions: List[str] = []

        for analysis in analyses:
            s = analysis.sentences
            avg_lengths.append(s.avg_sentence_length)
            variances.append(s.sentence_length_variance)
            question_freqs.append(s.question_frequency)
            exclamation_freqs.append(s.exclamation_frequency)
            complex_ratios.append(s.complex_sentence_ratio)
            all_openings.extend(s.opening_patterns)
            all_transitions.extend(s.transition_words)

        opening_counts = Counter(all_openings)
        transition_counts = Counter(all_transitions)

        n = len(analyses)
        return SentencePatterns(
            avg_sentence_length=round(sum(avg_lengths) / n, 1) if n else 0.0,
            sentence_length_variance=round(sum(variances) / n, 2) if n else 0.0,
            question_frequency=round(sum(question_freqs) / n, 3) if n else 0.0,
            exclamation_frequency=round(sum(exclamation_freqs) / n, 3) if n else 0.0,
            complex_sentence_ratio=round(sum(complex_ratios) / n, 3) if n else 0.0,
            opening_patterns=[o for o, _ in opening_counts.most_common(10)],
            transition_words=list(set(all_transitions)),
        )

    def _aggregate_tone(
        self,
        analyses: List[SampleAnalysis],
    ) -> ToneDistribution:
        """Aggregate tone distributions from multiple samples."""
        tone_sums: Dict[str, float] = {
            "professional": 0.0,
            "friendly": 0.0,
            "casual": 0.0,
            "authoritative": 0.0,
            "empathetic": 0.0,
            "enthusiastic": 0.0,
            "confident": 0.0,
            "approachable": 0.0,
            "innovative": 0.0,
            "trustworthy": 0.0,
            "playful": 0.0,
            "serious": 0.0,
        }

        for analysis in analyses:
            tone = analysis.tone
            for key in tone_sums:
                tone_sums[key] += getattr(tone, key, 0.0)

        n = len(analyses)
        if n == 0:
            return ToneDistribution()

        return ToneDistribution(**{
            k: round(v / n, 3) for k, v in tone_sums.items()
        })

    def _aggregate_style(
        self,
        analyses: List[SampleAnalysis],
    ) -> StyleMetrics:
        """Aggregate style metrics from multiple samples."""
        style_sums: Dict[str, float] = {
            "formality_score": 0.0,
            "complexity_score": 0.0,
            "engagement_score": 0.0,
            "personality_score": 0.0,
            "consistency_score": 0.0,
        }

        for analysis in analyses:
            style = analysis.style
            for key in style_sums:
                style_sums[key] += getattr(style, key, 0.0)

        n = len(analyses)
        if n == 0:
            return StyleMetrics()

        return StyleMetrics(**{
            k: round(v / n, 3) for k, v in style_sums.items()
        })

    def _generate_voice_summary(
        self,
        vocabulary: VocabularyProfile,
        sentences: SentencePatterns,
        tone: ToneDistribution,
        style: StyleMetrics,
        samples: List[VoiceSample],
    ) -> str:
        """Generate a natural language voice summary for prompting."""
        # Get top tones
        tone_dict = tone.model_dump()
        sorted_tones = sorted(tone_dict.items(), key=lambda x: x[1], reverse=True)
        top_tones = [t[0] for t in sorted_tones[:3] if t[1] > 0.3]

        # Get sample excerpts for context
        sample_excerpts = []
        for sample in samples[:3]:
            if sample.is_primary_example:
                excerpt = sample.content[:500]
                sample_excerpts.append(excerpt)

        # Build prompt
        prompt = f"""Based on this voice analysis, generate a concise, natural language description of the brand voice that can be used as a prompt instruction. The description should capture the essence of how this brand writes.

ANALYSIS:
- Top Tones: {', '.join(top_tones)}
- Formality: {style.formality_score:.2f}/1.0 ({'formal' if style.formality_score > 0.6 else 'casual' if style.formality_score < 0.4 else 'balanced'})
- Common Words: {', '.join(vocabulary.common_words[:10])}
- Common Phrases: {', '.join(vocabulary.unique_phrases[:5])}
- Avg Sentence Length: {sentences.avg_sentence_length} words
- Uses Questions: {'Yes' if sentences.question_frequency > 0.1 else 'Rarely'}
- Transition Words Used: {', '.join(sentences.transition_words[:5])}

{f'SAMPLE EXCERPTS:{chr(10)}{chr(10).join(sample_excerpts)}' if sample_excerpts else ''}

Write a 2-3 sentence voice description that:
1. Captures the primary tone and style
2. Notes distinctive vocabulary or phrasing patterns
3. Describes the overall personality

Start with "This brand voice..." or "The writing style..."
"""

        try:
            summary = generate_text(prompt, self.provider, self.options)
            # Clean up the response
            summary = summary.strip()
            if summary.startswith('"') and summary.endswith('"'):
                summary = summary[1:-1]
            return summary
        except Exception as e:
            logger.warning("Voice summary generation error: %s", e)

        # Fallback summary
        tone_str = " and ".join(top_tones) if top_tones else "balanced"
        formality_str = (
            "formal" if style.formality_score > 0.6
            else "casual" if style.formality_score < 0.4
            else "conversational"
        )
        return (
            f"This brand voice is {tone_str} with a {formality_str} style. "
            f"Sentences average {sentences.avg_sentence_length:.0f} words. "
            f"Frequently uses words like: {', '.join(vocabulary.common_words[:5])}."
        )


def train_voice_profile(
    profile_id: str,
    samples: List[VoiceSample],
    provider_type: str = "openai",
) -> VoiceFingerprint:
    """Convenience function to train a voice profile."""
    trainer = VoiceTrainer(provider_type)
    return trainer.train(profile_id, samples)
