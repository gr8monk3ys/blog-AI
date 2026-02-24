"""
SEO optimization loop -- iteratively improves content until score thresholds are met.
"""

import logging
from typing import Optional

from src.seo.content_optimizer import optimize_content
from src.text_generation.core import GenerationOptions, create_provider_from_env, generate_text
from src.types.content import Section, SubTopic as SubTopicModel
from src.types.seo import (
    ContentScore,
    OptimizationSuggestion,
    SEOOptimizationResult,
    SEOThresholds,
    SERPAnalysis,
    SuggestionPriority,
)

logger = logging.getLogger(__name__)


def _check_thresholds(score: ContentScore, thresholds: SEOThresholds) -> bool:
    """Return True if all dimension scores meet their thresholds."""
    return (
        score.overall_score >= thresholds.overall_minimum
        and score.topic_coverage >= thresholds.topic_coverage_minimum
        and score.term_usage >= thresholds.term_usage_minimum
        and score.structure_score >= thresholds.structure_minimum
        and score.readability_score >= thresholds.readability_minimum
        and score.word_count_score >= thresholds.word_count_minimum
    )


def _build_rewrite_prompt(
    content: str,
    suggestions: list[OptimizationSuggestion],
    keyword: str,
) -> str:
    """Build an LLM prompt that asks for content improvements based on SEO suggestions."""
    suggestion_lines = "\n".join(
        f"- [{s.type.value}] {s.description}"
        + (
            f" (current: {s.current_value}, recommended: {s.recommended_value})"
            if s.recommended_value
            else ""
        )
        for s in suggestions
    )
    return (
        f"You are an SEO content editor. Rewrite the following blog post to improve its SEO score "
        f'for the target keyword "{keyword}".\n\n'
        f"Apply these specific improvements:\n{suggestion_lines}\n\n"
        f"Rules:\n"
        f"- Preserve the overall structure (headings marked with ## and ###).\n"
        f"- Keep the same tone and voice.\n"
        f"- Naturally incorporate suggested terms and topics -- do not keyword-stuff.\n"
        f"- Return ONLY the rewritten blog post content, no commentary.\n\n"
        f"--- BLOG POST ---\n{content}"
    )


def _blog_post_to_text(blog_post) -> str:
    """Convert a BlogPost object to plain text for scoring and rewriting."""
    parts = [f"# {blog_post.title}\n"]
    if blog_post.description:
        parts.append(f"{blog_post.description}\n")
    for section in blog_post.sections:
        parts.append(f"\n## {section.title}\n")
        for subtopic in section.subtopics:
            if subtopic.title:
                parts.append(f"### {subtopic.title}\n")
            if subtopic.content:
                parts.append(f"{subtopic.content}\n")
    return "\n".join(parts)


def _text_to_sections(text: str, blog_post):
    """Parse rewritten text back into the blog post's section structure (best-effort)."""
    sections: list[Section] = []
    current_section_title = ""
    current_subtopics: list[SubTopicModel] = []
    current_subtopic_title = ""
    current_content_lines: list[str] = []

    def flush_subtopic():
        nonlocal current_subtopic_title, current_content_lines
        content = "\n".join(current_content_lines).strip()
        if content or current_subtopic_title:
            current_subtopics.append(
                SubTopicModel(title=current_subtopic_title, content=content)
            )
        current_subtopic_title = ""
        current_content_lines = []

    def flush_section():
        nonlocal current_section_title, current_subtopics
        flush_subtopic()
        if current_section_title or current_subtopics:
            sections.append(Section(title=current_section_title, subtopics=current_subtopics))
        current_section_title = ""
        current_subtopics = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            flush_section()
            current_section_title = stripped[3:].strip()
        elif stripped.startswith("### "):
            flush_subtopic()
            current_subtopic_title = stripped[4:].strip()
        elif stripped.startswith("# "):
            # Skip title line
            continue
        else:
            current_content_lines.append(line)

    flush_section()

    if sections:
        blog_post.sections = sections
    return blog_post


def optimize_until_threshold(
    blog_post,
    keyword: str,
    serp_analysis: Optional[SERPAnalysis] = None,
    thresholds: Optional[SEOThresholds] = None,
    provider_type: str = "openai",
    options: Optional[GenerationOptions] = None,
) -> SEOOptimizationResult:
    """
    Score content and iteratively optimize until thresholds are met.

    Args:
        blog_post: The BlogPost object to optimize.
        keyword: Target SEO keyword.
        serp_analysis: Optional pre-computed SERP analysis.
        thresholds: Score thresholds (defaults used if None).
        provider_type: LLM provider for rewrites.
        options: LLM generation options.

    Returns:
        SEOOptimizationResult with final score, pass/fail, and stats.
    """
    thresholds = thresholds or SEOThresholds()
    content_text = _blog_post_to_text(blog_post)
    suggestions_applied = 0

    for pass_num in range(thresholds.max_optimization_passes):
        optimization = optimize_content(content_text, keyword, serp_analysis)
        score = optimization.score

        if _check_thresholds(score, thresholds):
            logger.info(
                "SEO optimization passed on pass %d with score %.1f",
                pass_num + 1,
                score.overall_score,
            )
            return SEOOptimizationResult(
                score=score,
                passed=True,
                suggestions_applied=suggestions_applied,
                passes_used=pass_num + 1,
                final_suggestions=optimization.suggestions,
            )

        # Pick top-3 HIGH priority suggestions for the rewrite prompt
        high_suggestions = [
            s for s in optimization.suggestions if s.priority == SuggestionPriority.HIGH
        ][:3]
        if not high_suggestions:
            high_suggestions = optimization.suggestions[:3]

        if not high_suggestions:
            logger.info("No suggestions to apply, stopping optimization loop")
            return SEOOptimizationResult(
                score=score,
                passed=False,
                suggestions_applied=suggestions_applied,
                passes_used=pass_num + 1,
                final_suggestions=optimization.suggestions,
            )

        prompt = _build_rewrite_prompt(content_text, high_suggestions, keyword)
        provider = create_provider_from_env(provider_type)
        rewritten = generate_text(prompt, provider, options)
        suggestions_applied += len(high_suggestions)

        # Update blog_post sections from rewritten text
        blog_post = _text_to_sections(rewritten, blog_post)
        content_text = _blog_post_to_text(blog_post)

    # Final scoring after all passes
    final_optimization = optimize_content(content_text, keyword, serp_analysis)
    final_score = final_optimization.score
    passed = _check_thresholds(final_score, thresholds)

    logger.info(
        "SEO optimization %s after %d passes with score %.1f",
        "passed" if passed else "did not pass",
        thresholds.max_optimization_passes,
        final_score.overall_score,
    )
    return SEOOptimizationResult(
        score=final_score,
        passed=passed,
        suggestions_applied=suggestions_applied,
        passes_used=thresholds.max_optimization_passes,
        final_suggestions=final_optimization.suggestions,
    )
