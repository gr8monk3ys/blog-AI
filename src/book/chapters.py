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
            provider=provider,
            options=options,
        )

        section_jobs = [
            partial(
                sec_func,
                section_title=subtopic,
                keywords=keywords,
                tone=tone,
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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate an introduction chapter.
    """
    try:
        prompt = f"""
        Generate an introduction chapter for a book titled '{title}'.
        
        The book contains the following chapters:
        """

        for chapter in chapters:
            prompt += f"\n- {chapter.title}"

        if keywords:
            prompt += f"\n\nKeywords: {', '.join(keywords)}"

        prompt += f"""
        
        Requirements:
        - The introduction should be engaging and set the stage for the book.
        - Explain the purpose and scope of the book.
        - Provide an overview of what readers will learn.
        - Use a {tone} tone throughout.
        - The introduction should be 3-4 paragraphs.
        
        Return only the introduction content, nothing else.
        """

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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate an introduction chapter with research.
    """
    try:
        prompt = f"""
        Generate an introduction chapter for a book titled '{title}'.
        
        The book contains the following chapters:
        """

        for chapter in chapters:
            prompt += f"\n- {chapter.title}"

        if keywords:
            prompt += f"\n\nKeywords: {', '.join(keywords)}"

        prompt += f"""
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        
        Requirements:
        - The introduction should be engaging and set the stage for the book.
        - Explain the purpose and scope of the book.
        - Provide an overview of what readers will learn.
        - Incorporate insights from the research.
        - Use a {tone} tone throughout.
        - The introduction should be 3-4 paragraphs.
        
        Return only the introduction content, nothing else.
        """

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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    generate_text_func: Optional[Callable[..., str]] = None,
) -> Chapter:
    """
    Generate a conclusion chapter.
    """
    try:
        prompt = f"""
        Generate a conclusion chapter for a book titled '{title}'.
        
        The book contains the following chapters:
        """

        for chapter in chapters:
            prompt += f"\n- {chapter.title}"

        if keywords:
            prompt += f"\n\nKeywords: {', '.join(keywords)}"

        prompt += f"""
        
        Requirements:
        - The conclusion should summarize the key points from the book.
        - Reinforce the main message or thesis.
        - Provide final thoughts and recommendations.
        - Include a call to action for the reader.
        - Use a {tone} tone throughout.
        - The conclusion should be 3-4 paragraphs.
        
        Return only the conclusion content, nothing else.
        """

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
