"""
Content optimization engine that scores draft content against SERP data.

This module implements a Surfer-SEO-style content scoring system that:
- Compares draft content against SERP analysis data
- Scores topic coverage, NLP term usage, structure, and word count
- Identifies missing topics and terms that competitors cover
- Generates prioritized, actionable improvement suggestions
- Produces full content briefs from SERP analysis
"""

import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.seo import (
    ContentBrief,
    ContentOptimization,
    ContentScore,
    OptimizationSuggestion,
    SERPAnalysis,
    SuggestionPriority,
    SuggestionType,
)

logger = logging.getLogger(__name__)


class ContentOptimizerError(Exception):
    """Exception raised for errors in the content optimization process."""

    pass


def _parse_markdown_heading(line: str) -> Optional[str]:
    """Parse a markdown heading without regex backtracking."""
    candidate = line.strip()
    level = 0
    while level < len(candidate) and level < 6 and candidate[level] == "#":
        level += 1
    if level == 0 or level >= len(candidate) or not candidate[level].isspace():
        return None
    heading = candidate[level:].strip()
    return heading or None


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip markdown formatting."""
    normalized = re.sub(r"[#*_`\[\]()]", " ", text)
    return normalized.lower()


def _extract_words(text: str) -> List[str]:
    """Extract individual words from text."""
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def _extract_headings(text: str) -> List[str]:
    """Extract markdown headings from content."""
    headings: List[str] = []
    for line in text.split("\n"):
        heading = _parse_markdown_heading(line)
        if heading:
            headings.append(heading)
    return headings


def _calculate_topic_coverage(
    content_normalized: str,
    common_topics: List[str],
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate how well the content covers competitor topics.

    Args:
        content_normalized: Lowercase, cleaned content text.
        common_topics: Topics from SERP analysis.

    Returns:
        Tuple of (score, covered_topics, missing_topics).
    """
    if not common_topics:
        return 100.0, [], []

    covered: List[str] = []
    missing: List[str] = []

    for topic in common_topics:
        topic_lower = topic.lower().strip()
        if not topic_lower:
            continue
        if topic_lower in content_normalized:
            covered.append(topic)
        else:
            # Check for partial matches (individual significant words)
            topic_words = [w for w in topic_lower.split() if len(w) > 3]
            if topic_words and all(w in content_normalized for w in topic_words):
                covered.append(topic)
            else:
                missing.append(topic)

    total = len(covered) + len(missing)
    if total == 0:
        return 100.0, covered, missing

    score = (len(covered) / total) * 100
    return round(score, 1), covered, missing


def _calculate_term_usage(
    content_normalized: str,
    nlp_terms: List[str],
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate how well the content uses recommended NLP terms.

    Args:
        content_normalized: Lowercase, cleaned content text.
        nlp_terms: Semantically related terms from SERP analysis.

    Returns:
        Tuple of (score, covered_terms, missing_terms).
    """
    if not nlp_terms:
        return 100.0, [], []

    covered: List[str] = []
    missing: List[str] = []

    for term in nlp_terms:
        term_lower = term.lower().strip()
        if not term_lower:
            continue
        if term_lower in content_normalized:
            covered.append(term)
        else:
            missing.append(term)

    total = len(covered) + len(missing)
    if total == 0:
        return 100.0, covered, missing

    score = (len(covered) / total) * 100
    return round(score, 1), covered, missing


def _calculate_structure_score(
    content_headings: List[str],
    suggested_headings: List[str],
) -> float:
    """
    Score how well the content heading structure aligns with competitor patterns.

    Args:
        content_headings: Headings extracted from the content.
        suggested_headings: Recommended headings from SERP analysis.

    Returns:
        Structure score (0-100).
    """
    if not suggested_headings:
        # No suggestions to compare against; score based on heading count alone
        if len(content_headings) >= 5:
            return 100.0
        elif len(content_headings) >= 3:
            return 75.0
        elif len(content_headings) >= 1:
            return 50.0
        return 25.0

    content_headings_lower = {h.lower() for h in content_headings}
    matches = 0

    for suggested in suggested_headings:
        suggested_lower = suggested.lower()
        # Exact match
        if suggested_lower in content_headings_lower:
            matches += 1
            continue
        # Fuzzy match: check if key words from the suggested heading are in any content heading
        suggested_words = set(
            w for w in suggested_lower.split() if len(w) > 3
        )
        if suggested_words:
            for ch in content_headings_lower:
                ch_words = set(w for w in ch.split() if len(w) > 3)
                overlap = suggested_words & ch_words
                if len(overlap) >= max(1, len(suggested_words) * 0.5):
                    matches += 1
                    break

    score = (matches / len(suggested_headings)) * 100
    return round(min(100.0, score), 1)


def _calculate_word_count_score(
    word_count: int,
    recommended_word_count: int,
) -> float:
    """
    Score how well the content length matches the recommended word count.

    Args:
        word_count: Actual word count of the content.
        recommended_word_count: Target word count from SERP analysis.

    Returns:
        Word count score (0-100).
    """
    if recommended_word_count <= 0:
        return 100.0

    ratio = word_count / recommended_word_count

    # Ideal range: 80% to 120% of recommended
    if 0.8 <= ratio <= 1.2:
        return 100.0
    elif 0.6 <= ratio < 0.8:
        return 70.0
    elif 1.2 < ratio <= 1.5:
        return 80.0
    elif 0.4 <= ratio < 0.6:
        return 50.0
    elif ratio < 0.4:
        return 30.0
    else:
        # ratio > 1.5
        return 60.0


def _calculate_readability_score(content: str) -> float:
    """
    Calculate a basic readability score for the content.

    Uses simplified Flesch Reading Ease estimation.

    Args:
        content: Raw content text.

    Returns:
        Readability score (0-100).
    """
    words = _extract_words(content)
    sentences = [s.strip() for s in re.split(r"[.!?]+", content) if s.strip()]

    word_count = len(words)
    sentence_count = max(1, len(sentences))

    avg_words_per_sentence = word_count / sentence_count

    # Simplified syllable count
    total_syllables = 0
    for word in words:
        # Simple heuristic: count vowel groups
        syllables = len(re.findall(r"[aeiouy]+", word.lower()))
        total_syllables += max(1, syllables)

    avg_syllables_per_word = total_syllables / max(1, word_count)

    # Flesch Reading Ease
    flesch = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    return round(max(0, min(100, flesch)), 1)


def _build_suggestions(
    missing_topics: List[str],
    missing_terms: List[str],
    suggested_headings: List[str],
    content_headings: List[str],
    questions: List[str],
    content_normalized: str,
    word_count: int,
    recommended_word_count: int,
    structure_score: float,
) -> List[OptimizationSuggestion]:
    """
    Build a prioritized list of optimization suggestions.

    Args:
        missing_topics: Topics not covered in the content.
        missing_terms: NLP terms missing from the content.
        suggested_headings: Recommended headings from SERP analysis.
        content_headings: Headings currently in the content.
        questions: Questions the content should answer.
        content_normalized: Normalized content text.
        word_count: Current word count.
        recommended_word_count: Target word count.
        structure_score: Current structure alignment score.

    Returns:
        Sorted list of OptimizationSuggestion objects.
    """
    suggestions: List[OptimizationSuggestion] = []

    # Word count suggestions
    if recommended_word_count > 0:
        ratio = word_count / recommended_word_count
        if ratio < 0.7:
            suggestions.append(
                OptimizationSuggestion(
                    type=SuggestionType.ADJUST_LENGTH,
                    priority=SuggestionPriority.HIGH,
                    description=(
                        f"Content is significantly shorter than top-ranking competitors. "
                        f"Expand to approximately {recommended_word_count} words."
                    ),
                    current_value=f"{word_count} words",
                    recommended_value=f"{recommended_word_count} words",
                )
            )
        elif ratio > 1.5:
            suggestions.append(
                OptimizationSuggestion(
                    type=SuggestionType.ADJUST_LENGTH,
                    priority=SuggestionPriority.MEDIUM,
                    description=(
                        f"Content is significantly longer than competitors. "
                        f"Consider trimming or splitting into multiple articles."
                    ),
                    current_value=f"{word_count} words",
                    recommended_value=f"{recommended_word_count} words",
                )
            )

    # Missing topic suggestions (high priority)
    for topic in missing_topics[:5]:
        suggestions.append(
            OptimizationSuggestion(
                type=SuggestionType.COVER_TOPIC,
                priority=SuggestionPriority.HIGH,
                description=f"Add content covering the topic: {topic}",
                current_value="Not covered",
                recommended_value=f"Cover '{topic}' as top competitors do",
            )
        )

    # Missing heading suggestions
    content_headings_lower = {h.lower() for h in content_headings}
    for heading in suggested_headings:
        heading_lower = heading.lower()
        # Check if a similar heading exists
        heading_words = set(w for w in heading_lower.split() if len(w) > 3)
        found = False
        if heading_words:
            for ch in content_headings_lower:
                ch_words = set(w for w in ch.split() if len(w) > 3)
                if heading_words & ch_words:
                    found = True
                    break
        if not found:
            suggestions.append(
                OptimizationSuggestion(
                    type=SuggestionType.ADD_HEADING,
                    priority=SuggestionPriority.MEDIUM,
                    description=f"Add a section with heading: {heading}",
                    current_value=None,
                    recommended_value=heading,
                )
            )

    # Unanswered question suggestions
    for question in questions[:5]:
        question_lower = question.lower()
        # Check if the question or its key words are addressed in the content
        question_words = set(w for w in question_lower.split() if len(w) > 3)
        if question_words and not all(w in content_normalized for w in question_words):
            suggestions.append(
                OptimizationSuggestion(
                    type=SuggestionType.ANSWER_QUESTION,
                    priority=SuggestionPriority.MEDIUM,
                    description=f"Address the question: {question}",
                    current_value="Not addressed",
                    recommended_value=f"Answer '{question}' in the content",
                )
            )

    # Missing NLP term suggestions (lower priority, but important for topical depth)
    for term in missing_terms[:8]:
        suggestions.append(
            OptimizationSuggestion(
                type=SuggestionType.ADD_TERM,
                priority=SuggestionPriority.LOW,
                description=f"Include the semantically related term: {term}",
                current_value="Not used",
                recommended_value=f"Use '{term}' naturally in the content",
            )
        )

    # Structure suggestion
    if structure_score < 50:
        suggestions.append(
            OptimizationSuggestion(
                type=SuggestionType.IMPROVE_STRUCTURE,
                priority=SuggestionPriority.HIGH,
                description=(
                    "Content structure does not align with top-ranking pages. "
                    "Reorganize headings to match competitor patterns."
                ),
                current_value=f"{len(content_headings)} headings",
                recommended_value=f"Align with {len(suggested_headings)} suggested headings",
            )
        )

    # Sort by priority: HIGH > MEDIUM > LOW
    priority_order = {
        SuggestionPriority.HIGH: 0,
        SuggestionPriority.MEDIUM: 1,
        SuggestionPriority.LOW: 2,
    }
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

    return suggestions


def optimize_content(
    content: str,
    keyword: str,
    serp_analysis: SERPAnalysis,
) -> ContentOptimization:
    """
    Score and optimize content against SERP analysis data.

    This function compares the draft content with competitive intelligence
    extracted from the SERP to produce a detailed score and actionable
    optimization suggestions.

    Args:
        content: The draft content to optimize.
        keyword: The target keyword.
        serp_analysis: SERP analysis data from analyze_serp().

    Returns:
        ContentOptimization with scores, missing items, and suggestions.

    Raises:
        ContentOptimizerError: If optimization fails.
    """
    try:
        content_normalized = _normalize_text(content)
        words = _extract_words(content)
        word_count = len(words)
        content_headings = _extract_headings(content)

        # Calculate individual scores
        topic_score, covered_topics, missing_topics = _calculate_topic_coverage(
            content_normalized, serp_analysis.common_topics
        )
        term_score, covered_terms, missing_terms = _calculate_term_usage(
            content_normalized, serp_analysis.nlp_terms
        )
        structure_score = _calculate_structure_score(
            content_headings, serp_analysis.suggested_headings
        )
        word_count_score = _calculate_word_count_score(
            word_count, serp_analysis.recommended_word_count
        )
        readability_score = _calculate_readability_score(content)

        # Calculate overall score (weighted)
        overall_score = (
            topic_score * 0.30
            + term_score * 0.25
            + structure_score * 0.20
            + word_count_score * 0.15
            + readability_score * 0.10
        )
        overall_score = round(min(100.0, max(0.0, overall_score)), 1)

        score = ContentScore(
            overall_score=overall_score,
            topic_coverage=topic_score,
            term_usage=term_score,
            structure_score=structure_score,
            readability_score=readability_score,
            word_count_score=word_count_score,
        )

        # Build suggestions
        suggestions = _build_suggestions(
            missing_topics=missing_topics,
            missing_terms=missing_terms,
            suggested_headings=serp_analysis.suggested_headings,
            content_headings=content_headings,
            questions=serp_analysis.questions_to_answer,
            content_normalized=content_normalized,
            word_count=word_count,
            recommended_word_count=serp_analysis.recommended_word_count,
            structure_score=structure_score,
        )

        logger.info(
            "Content optimization complete for keyword '%s': "
            "overall=%.1f, topics=%.1f, terms=%.1f, structure=%.1f",
            keyword,
            overall_score,
            topic_score,
            term_score,
            structure_score,
        )

        return ContentOptimization(
            score=score,
            suggestions=suggestions,
            missing_topics=missing_topics,
            missing_terms=missing_terms,
            covered_topics=covered_topics,
            covered_terms=covered_terms,
        )

    except Exception as e:
        logger.exception("Content optimization failed for keyword: %s", keyword)
        raise ContentOptimizerError(
            f"Error optimizing content for '{keyword}': {str(e)}"
        ) from e


def generate_content_brief(
    keyword: str,
    serp_analysis: SERPAnalysis,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> ContentBrief:
    """
    Generate a comprehensive content brief from SERP analysis data.

    Uses LLM analysis to synthesize SERP data into a writer-friendly brief
    with a recommended title, outline, terms to include, and tone guidance.

    Args:
        keyword: The target keyword.
        serp_analysis: SERP analysis data from analyze_serp().
        provider: LLM provider for brief generation.
        options: Generation options for the LLM call.

    Returns:
        ContentBrief with actionable writing guidance.

    Raises:
        ContentOptimizerError: If brief generation fails.
    """
    try:
        # Build context from SERP analysis
        results_context = "\n".join(
            f"- Position {r.position}: {r.title} | {r.snippet}"
            for r in serp_analysis.results[:10]
        )

        topics_context = ", ".join(serp_analysis.common_topics[:15])
        headings_context = "\n".join(
            f"- {h}" for h in serp_analysis.suggested_headings
        )
        questions_context = "\n".join(
            f"- {q}" for q in serp_analysis.questions_to_answer
        )
        terms_context = ", ".join(serp_analysis.nlp_terms[:20])

        prompt = f"""You are an expert SEO content strategist. Generate a comprehensive content brief for the keyword "{keyword}".

Use the following competitive intelligence from the top Google search results:

TOP RESULTS:
{results_context}

COMMON TOPICS: {topics_context}
SUGGESTED HEADINGS:
{headings_context}
QUESTIONS TO ANSWER:
{questions_context}
RECOMMENDED WORD COUNT: {serp_analysis.recommended_word_count}
NLP TERMS TO INCLUDE: {terms_context}

Generate a content brief as a JSON object (return ONLY the JSON, no markdown fencing or explanation):

{{
  "recommended_title": "A compelling, SEO-optimized title that would outrank competitors",
  "recommended_outline": ["List of 8-15 H2/H3 headings forming a logical article structure"],
  "recommended_word_count": <integer>,
  "terms_to_include": ["15-20 most important NLP terms to weave into the content"],
  "questions_to_answer": ["5-8 key questions the article must address"],
  "competitor_insights": "2-3 sentence summary of what competitors do well and content gaps",
  "tone_guidance": "1-2 sentence recommendation on tone and style based on top results"
}}

Guidelines:
- The title should be unique but optimized for the target keyword.
- The outline should form a comprehensive, logically ordered structure.
- Terms should be prioritized by importance to topical authority.
- Competitor insights should highlight gaps and opportunities.
"""

        logger.info("Generating content brief with LLM for keyword: %s", keyword)
        brief_text = generate_text(prompt, provider, options)

        # Parse the LLM response
        brief_data = _parse_brief_json(brief_text)

        return ContentBrief(
            keyword=keyword,
            recommended_title=brief_data.get(
                "recommended_title",
                f"Complete Guide to {keyword.title()}",
            ),
            recommended_outline=brief_data.get("recommended_outline", []),
            recommended_word_count=brief_data.get(
                "recommended_word_count",
                serp_analysis.recommended_word_count,
            ),
            terms_to_include=brief_data.get("terms_to_include", []),
            questions_to_answer=brief_data.get("questions_to_answer", []),
            competitor_insights=brief_data.get("competitor_insights", ""),
            tone_guidance=brief_data.get("tone_guidance", ""),
        )

    except ContentOptimizerError:
        raise
    except Exception as e:
        logger.exception("Content brief generation failed for keyword: %s", keyword)
        raise ContentOptimizerError(
            f"Error generating content brief for '{keyword}': {str(e)}"
        ) from e


def _parse_brief_json(text: str) -> dict:
    """
    Parse JSON from the LLM brief response.

    Args:
        text: Raw LLM output containing a JSON object.

    Returns:
        Parsed dictionary.

    Raises:
        ContentOptimizerError: If JSON parsing fails.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    start_brace = cleaned.find("{")
    end_brace = cleaned.rfind("}")

    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_str = cleaned[start_brace:end_brace + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM brief JSON response: %s", e)
        raise ContentOptimizerError(
            f"Failed to parse content brief from LLM response: {e}"
        ) from e
