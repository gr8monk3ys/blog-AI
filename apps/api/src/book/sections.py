"""
Section generation for book chapters.
"""

import logging
from typing import Any, List, Optional

from ..blog_sections.conclusion_generator import generate_conclusion
from ..blog_sections.introduction_generator import generate_introduction
from ..text_generation.core import GenerationOptions, LLMProvider, TextGenerationError, generate_text
from ..types.content import Section, SubTopic
from .errors import BookGenerationError

logger = logging.getLogger(__name__)


def generate_introduction_section(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section.
    """
    try:
        introduction = generate_introduction(
            title=title,
            outline="\n".join(subtopics),
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        subtopic = SubTopic(title="", content=introduction.content)
        return Section(title="Introduction", subtopics=[subtopic])
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate introduction section: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for introduction section: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during introduction section generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating introduction section: %s", str(e), exc_info=True
        )
        raise BookGenerationError(
            f"Unexpected error generating introduction section: {str(e)}"
        ) from e


def generate_introduction_section_with_research(
    title: str,
    subtopics: List[str],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section with research.
    """
    try:
        # PROMPT DESIGN: Research-backed chapter introduction. Books need more depth
        # than blog posts, so we push for broader context-setting and richer hooks.
        prompt = f"""Write the introduction for a book chapter.

Chapter title: {title}
Subtopics this chapter covers: {", ".join(subtopics)}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""
RESEARCH CONTEXT (use specific findings):
{str(research_results)[:2000]}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with a compelling finding, scenario, or question drawn from the research.
Ground it in specifics -- numbers, names, real situations. Do NOT use generic
openers like "In today's world..." or "Have you ever wondered..."

Paragraph 2 -- THE CONTEXT:
Establish why this chapter's topic matters. Use research to provide evidence.
Connect it to the broader theme of the book.

Paragraph 3 -- THE ROADMAP:
Tell the reader what this chapter will cover and what they'll understand by the end.
Be specific: "We'll examine X, walk through Y, and explore Z."

CITATION RULES:
- Add [N] at end of sentences that reference a specific source.
- Only cite sources from the research context -- never invent.

STYLE RULES:
- Tone: {tone}
- Write with authority but accessibility -- like a knowledgeable author, not a textbook
- Use contractions and vary sentence length
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "it's worth mentioning", "in conclusion"

Return ONLY the introduction paragraphs. No headings, labels, or commentary."""

        introduction_text = generate_text(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=introduction_text)
        return Section(title="Introduction", subtopics=[subtopic])
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate introduction section with research: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for introduction section with research: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            "Invalid data structure during introduction section with research: "
            f"{str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating introduction section with research: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating introduction section with research: {str(e)}"
        ) from e


def generate_section(
    section_title: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a section.
    """
    try:
        # PROMPT DESIGN: Book section content. Books demand more depth than blogs --
        # we push for richer explanations, multiple examples, and layered analysis.
        prompt = f"""Write the content for a book section.

Section title: {section_title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

CONTENT REQUIREMENTS (4-5 paragraphs):

- Open with a clear framing of what this section addresses and why it matters
  in the context of the chapter. Do NOT open with "When it comes to..." or
  "It's important to understand that..."
- Provide DEPTH: explain the "why" behind concepts, not just the "what."
  A book reader expects more thorough treatment than a blog post skimmer.
- Include at least ONE concrete example, case study, or illustrative scenario.
  Specific is always better than abstract.
- Build each paragraph on the previous one -- there should be a clear thread
  of logic running through the section.
- Close with a thought that bridges to the next section or deepens the reader's
  understanding.

STYLE RULES:
- Write with the authority and depth of a subject-matter expert
- Vary sentence length: short punchy sentences for emphasis, longer ones for nuance
- Use contractions naturally and address the reader with "you" where appropriate
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive,
  multifaceted, aforementioned
- BANNED phrases: "it's important to note", "it's worth mentioning", "when it comes to",
  "in today's world"
"""

        if keywords:
            prompt += "- Weave keywords in naturally -- never force them.\n"

        prompt += """
Return ONLY the section content. No title, no headings, no commentary."""

        section_content = generate_text(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=section_content)
        return Section(title=section_title, subtopics=[subtopic])
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate section: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for section: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during section generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error generating section: %s", str(e), exc_info=True)
        raise BookGenerationError(f"Unexpected error generating section: {str(e)}") from e


def generate_section_with_research(
    section_title: str,
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a section with research.
    """
    try:
        # PROMPT DESIGN: Research-backed book section. We push for evidence-based
        # writing with natural citation flow and deeper analysis than blog sections.
        prompt = f"""Write the content for a research-backed book section.

Section title: {section_title}

RESEARCH CONTEXT (use as evidence, not just summaries):
{str(research_results)[:2000]}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

CONTENT REQUIREMENTS (4-5 paragraphs):

- Open by framing what this section covers and why it matters. Do NOT start
  with "When it comes to..." or "It's important to understand..."
- Use research findings as EVIDENCE to support your analysis -- don't just
  restate what the research says. Interpret it. Explain what it means.
- Include specific data points, expert insights, or case studies from the research.
- Build a clear logical thread: each paragraph should advance the argument.
- Close with a connecting thought that bridges to the next section.

CITATION RULES:
- Add [N] at the end of sentences referencing specific sources.
- Only cite sources from the research context -- NEVER invent citations.
- Aim for 2-4 citations per section, spread naturally across paragraphs.
- Weave citations into prose: "Teams adopting X saw 30% gains [2]" -- not
  "Research shows [1][2] that improvements occur."

STYLE RULES:
- Write with the depth and authority of a subject-matter expert
- Vary sentence length for rhythm and emphasis
- Use contractions naturally and address the reader directly where appropriate
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "it's worth mentioning", "when it comes to"
"""

        if keywords:
            prompt += "- Weave keywords in naturally -- never force them.\n"

        prompt += """
Return ONLY the section content. No title, headings, or commentary."""

        section_content = generate_text(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=section_content)
        return Section(title=section_title, subtopics=[subtopic])
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate section with research: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for section with research: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during section with research: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating section with research: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating section with research: {str(e)}"
        ) from e


def generate_conclusion_section(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a conclusion section.
    """
    try:
        content = f"Title: {title}\n\nSubtopics:\n"
        for subtopic in subtopics:
            content += f"- {subtopic}\n"

        conclusion = generate_conclusion(
            title=title,
            content=content,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        subtopic = SubTopic(title="", content=conclusion.content)
        return Section(title="Conclusion", subtopics=[subtopic])
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate conclusion section: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for conclusion section: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during conclusion section generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating conclusion section: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating conclusion section: {str(e)}"
        ) from e
