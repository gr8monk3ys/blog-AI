"""
Chapter generation for books.
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, TextGenerationError, generate_text
from ..types.content import Chapter, Section, SubTopic, Topic
from .errors import BookGenerationError
from .sections import (
    generate_conclusion_section,
    generate_introduction_section,
    generate_introduction_section_with_research,
    generate_section,
    generate_section_with_research,
)

logger = logging.getLogger(__name__)

MAX_SECTION_WORKERS = int(os.environ.get("BOOK_SECTION_WORKERS", "4"))


async def _run_section_jobs_async(jobs: List[Callable[[], Section]]) -> List[Section]:
    tasks = [asyncio.to_thread(job) for job in jobs]
    return await asyncio.gather(*tasks)


def _run_section_jobs(jobs: List[Callable[[], Section]]) -> List[Section]:
    if not jobs:
        return []
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        max_workers = min(MAX_SECTION_WORKERS, len(jobs))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(lambda job: job(), jobs))

    return asyncio.run(_run_section_jobs_async(jobs))


def generate_chapter(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    concurrent_sections: bool = True,
    introduction_section_func: Optional[Callable[..., Section]] = None,
    section_func: Optional[Callable[..., Section]] = None,
    conclusion_section_func: Optional[Callable[..., Section]] = None,
) -> Chapter:
    """
    Generate a chapter.
    """
    try:
        intro_func = introduction_section_func or generate_introduction_section
        sec_func = section_func or generate_section
        conclusion_func = conclusion_section_func or generate_conclusion_section

        introduction_section = intro_func(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        section_jobs = [
            partial(
                sec_func,
                section_title=subtopic,
                keywords=keywords,
                tone=tone,
                brand_voice=brand_voice,
                provider=provider,
                options=options,
            )
            for subtopic in subtopics
        ]
        if concurrent_sections:
            main_sections = _run_section_jobs(section_jobs)
        else:
            main_sections = [job() for job in section_jobs]

        conclusion_section = conclusion_func(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        sections = [introduction_section] + main_sections + [conclusion_section]

        topics = []
        for section in sections:
            for subtopic in section.subtopics:
                topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=1, title=title, topics=topics)
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate chapter '{title}': {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for chapter '{title}': {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during chapter generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error generating chapter: %s", str(e), exc_info=True)
        raise BookGenerationError(
            f"Unexpected error generating chapter: {str(e)}"
        ) from e


def generate_chapter_with_research(
    title: str,
    subtopics: List[str],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    concurrent_sections: bool = True,
    introduction_section_func: Optional[Callable[..., Section]] = None,
    section_func: Optional[Callable[..., Section]] = None,
    conclusion_section_func: Optional[Callable[..., Section]] = None,
) -> Chapter:
    """
    Generate a chapter with research.
    """
    try:
        intro_func = (
            introduction_section_func or generate_introduction_section_with_research
        )
        sec_func = section_func or generate_section_with_research
        conclusion_func = conclusion_section_func or generate_conclusion_section

        introduction_section = intro_func(
            title=title,
            subtopics=subtopics,
            research_results=research_results,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        section_jobs = [
            partial(
                sec_func,
                section_title=subtopic,
                research_results=research_results,
                keywords=keywords,
                tone=tone,
                brand_voice=brand_voice,
                provider=provider,
                options=options,
            )
            for subtopic in subtopics
        ]
        if concurrent_sections:
            main_sections = _run_section_jobs(section_jobs)
        else:
            main_sections = [job() for job in section_jobs]

        conclusion_section = conclusion_func(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        sections = [introduction_section] + main_sections + [conclusion_section]

        topics = []
        for section in sections:
            for subtopic in section.subtopics:
                topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=1, title=title, topics=topics)
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate chapter '{title}' with research: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for chapter with research: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during chapter with research: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating chapter with research: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating chapter with research: {str(e)}"
        ) from e


def generate_introduction_chapter(
    title: str,
    chapters: List[Chapter],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate an introduction chapter.
    """
    try:
        # PROMPT DESIGN: Book introduction chapter. This sets the tone for the
        # entire book. We push for a compelling narrative frame and clear reader
        # benefit statement rather than a dry table-of-contents summary.
        prompt = f"""Write the introduction chapter for a book titled '{title}'.

This book contains the following chapters:
"""

        for chapter in chapters:
            prompt += f"- {chapter.title}\n"

        if keywords:
            prompt += f"\nTarget keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with a compelling scenario, question, or insight that captures why this
book's topic matters RIGHT NOW. Make the reader feel the urgency or excitement.
Do NOT open with "In today's..." or "Welcome to this book..."

Paragraph 2 -- THE PROMISE:
What will the reader be able to do, understand, or achieve after reading this
book? Be specific and concrete. Frame it as a transformation: "By the time you
finish, you'll go from X to Y."

Paragraph 3 -- THE ROADMAP:
Give a brief, engaging preview of the book's journey. Don't just list chapter
titles -- describe the narrative arc. What do they learn first and why? How do
the chapters build on each other? Make it feel like a path, not a checklist.

Optional Paragraph 4 -- WHO THIS IS FOR:
If appropriate, briefly describe who will get the most value from this book.
Be specific: "This is for mid-level engineers who..." not "This book is for anyone
interested in..."

STYLE RULES:
- Write with warmth and authority -- you're welcoming the reader into a journey
- Use contractions and address the reader directly ("you'll", "your")
- Vary sentence length for rhythm
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "in today's fast-paced world"

Return ONLY the introduction content. No headings, labels, or commentary."""

        text_func = generate_text_func or generate_text
        introduction_content = text_func(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=introduction_content)
        section = Section(title="Introduction", subtopics=[subtopic])

        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=0, title="Introduction", topics=topics)
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate introduction chapter: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for introduction chapter: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during introduction chapter generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating introduction chapter: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating introduction chapter: {str(e)}"
        ) from e


def generate_introduction_chapter_with_research(
    title: str,
    chapters: List[Chapter],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate an introduction chapter with research.
    """
    try:
        # PROMPT DESIGN: Research-backed book introduction. We lead with research
        # findings to establish authority and use citations to ground the narrative.
        prompt = f"""Write the introduction chapter for a research-backed book titled '{title}'.

This book contains the following chapters:
"""

        for chapter in chapters:
            prompt += f"- {chapter.title}\n"

        if keywords:
            prompt += f"\nTarget keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""
RESEARCH CONTEXT (use to ground your introduction in evidence):
{str(research_results)[:2000]}

Tone: {tone}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with a striking finding, trend, or data point from the research that
captures why this book's topic matters urgently. Be specific -- use numbers
or concrete examples. Do NOT open with "In today's..." or "Welcome to..."

Paragraph 2 -- THE PROMISE:
What will the reader achieve after finishing this book? Frame it as a concrete
transformation backed by the research: "The data shows X is possible -- this
book shows you exactly how."

Paragraph 3 -- THE ROADMAP:
Preview the book's journey. Don't just list chapters -- describe the arc.
Reference research findings that informed the structure.

CITATION RULES:
- Add [N] at the end of sentences referencing specific sources.
- Only cite sources from the research context -- never invent.
- Use 2-3 citations total, placed naturally.

STYLE RULES:
- Write with warmth and authority
- Use contractions and address the reader directly
- Vary sentence length for rhythm
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "in today's fast-paced world"

Return ONLY the introduction content. No headings, labels, or commentary."""

        text_func = generate_text_func or generate_text
        introduction_content = text_func(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=introduction_content)
        section = Section(title="Introduction", subtopics=[subtopic])

        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=0, title="Introduction", topics=topics)
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate introduction chapter with research: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for introduction chapter with research: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            "Invalid data structure during introduction chapter generation: "
            f"{str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating introduction chapter with research: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating introduction chapter with research: {str(e)}"
        ) from e


def generate_conclusion_chapter(
    title: str,
    chapters: List[Chapter],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate a conclusion chapter.
    """
    try:
        # PROMPT DESIGN: Book conclusion chapter. This is the reader's final
        # impression. We push for synthesis and forward momentum rather than
        # mechanical recap.
        prompt = f"""Write the conclusion chapter for a book titled '{title}'.

This book covered the following chapters:
"""

        for chapter in chapters:
            prompt += f"- {chapter.title}\n"

        if keywords:
            prompt += f"\nTarget keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE SYNTHESIS:
Do NOT start with "In conclusion" or mechanically recap each chapter.
Instead, connect the chapters' themes into a unified insight. What's the
bigger picture that emerges? What should the reader understand differently
about the topic now compared to when they started?

Paragraph 2 -- THE FORWARD LOOK:
Where is this field, practice, or topic heading? What trends or shifts
should the reader watch for? Give them something to think about beyond
what the book covered.

Paragraph 3 -- THE CALL TO ACTION:
Give the reader a specific, motivating next step. Not "go forth and apply
what you've learned" but something concrete they can do THIS WEEK.
Frame it as an invitation, not an order.

Final sentence: End with something memorable -- a bold claim, an inspiring
thought, or a callback to the book's opening hook.

STYLE RULES:
- Write with conviction and warmth -- this is your farewell to the reader
- Use contractions and "you" language
- Vary sentence length for emotional rhythm
- BANNED openers: "In conclusion", "To sum up", "In summary", "As we've explored"
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "it's worth mentioning"

Return ONLY the conclusion content. No headings, labels, or commentary."""

        text_func = generate_text_func or generate_text
        conclusion_content = text_func(prompt, provider, options).strip()
        subtopic = SubTopic(title="", content=conclusion_content)
        section = Section(title="Conclusion", subtopics=[subtopic])

        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=99, title="Conclusion", topics=topics)
    except TextGenerationError as e:
        raise BookGenerationError(
            f"Failed to generate conclusion chapter: {str(e)}"
        ) from e
    except ValueError as e:
        raise BookGenerationError(
            f"Invalid parameters for conclusion chapter: {str(e)}"
        ) from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during conclusion chapter generation: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error generating conclusion chapter: %s",
            str(e),
            exc_info=True,
        )
        raise BookGenerationError(
            f"Unexpected error generating conclusion chapter: {str(e)}"
        ) from e
