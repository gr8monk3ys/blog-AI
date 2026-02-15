"""
Book generation orchestration.
"""

import logging
from typing import List, Optional

from ..planning.topic_clusters import (
    generate_topic_clusters,
    generate_topic_clusters_with_research,
)
from ..research.web_researcher import (
    conduct_web_research,
    extract_research_sources,
    format_research_results_for_prompt,
)
from ..text_generation.core import (
    GenerationOptions,
    LLMProvider,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
)
from ..types.content import Book, SourceCitation
from ..types.providers import ProviderType
from .chapters import (
    generate_chapter,
    generate_chapter_with_research,
    generate_conclusion_chapter,
    generate_introduction_chapter,
    generate_introduction_chapter_with_research,
)
from .errors import BookGenerationError

logger = logging.getLogger(__name__)


def generate_book(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
    concurrent_sections: bool = True,
    provider_factory=create_provider_from_env,
    topic_cluster_generator=generate_topic_clusters,
    chapter_generator=generate_chapter,
    introduction_chapter_generator=generate_introduction_chapter,
    conclusion_chapter_generator=generate_conclusion_chapter,
) -> Book:
    """
    Generate a book.
    """
    try:
        provider = provider_factory(provider_type)

        clusters = topic_cluster_generator(
            title, num_chapters, sections_per_chapter, provider, options
        )

        chapters = []
        for cluster in clusters:
            chapter = chapter_generator(
                title=cluster.main_topic,
                subtopics=cluster.subtopics,
                keywords=cluster.keywords,
                tone=tone,
                brand_voice=brand_voice,
                provider=provider,
                options=options,
                concurrent_sections=concurrent_sections,
            )
            chapters.append(chapter)

        introduction_chapter = introduction_chapter_generator(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        conclusion_chapter = conclusion_chapter_generator(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        all_chapters = [introduction_chapter] + chapters + [conclusion_chapter]
        return Book(title=title, chapters=all_chapters, tags=keywords or [])
    except TextGenerationError as e:
        logger.error("Text generation error in book: %s", str(e))
        raise BookGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning("Rate limit exceeded in book generation: %s", str(e))
        raise BookGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning("Invalid input for book: %s", str(e))
        raise BookGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error("Unexpected error generating book: %s", str(e), exc_info=True)
        raise BookGenerationError(f"Unexpected error: {str(e)}") from e


def generate_book_with_research(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
    concurrent_sections: bool = True,
    provider_factory=create_provider_from_env,
    research_func=conduct_web_research,
    topic_cluster_generator=generate_topic_clusters_with_research,
    chapter_generator=generate_chapter_with_research,
    introduction_chapter_generator=generate_introduction_chapter_with_research,
    conclusion_chapter_generator=generate_conclusion_chapter,
) -> Book:
    """
    Generate a book with research.
    """
    try:
        provider = provider_factory(provider_type)

        research_keywords = [title]
        if keywords:
            research_keywords.extend(keywords)

        research_results = research_func(research_keywords)
        raw_sources = extract_research_sources(research_results, max_sources=8)
        sources = [
            SourceCitation(
                id=int(s.get("id", 0) or 0),
                title=str(s.get("title") or ""),
                url=str(s.get("url") or ""),
                snippet=str(s.get("snippet") or ""),
                provider=str(s.get("provider") or ""),
            )
            for s in raw_sources
        ]
        research_context = format_research_results_for_prompt(
            research_results, max_sources=8, max_chars=2400
        )

        clusters = topic_cluster_generator(
            title, num_chapters, sections_per_chapter, provider, options
        )

        chapters = []
        for cluster in clusters:
            chapter = chapter_generator(
                title=cluster.main_topic,
                subtopics=cluster.subtopics,
                research_results=research_context,
                keywords=cluster.keywords,
                tone=tone,
                brand_voice=brand_voice,
                provider=provider,
                options=options,
                concurrent_sections=concurrent_sections,
            )
            chapters.append(chapter)

        introduction_chapter = introduction_chapter_generator(
            title=title,
            chapters=chapters,
            research_results=research_context,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        conclusion_chapter = conclusion_chapter_generator(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        all_chapters = [introduction_chapter] + chapters + [conclusion_chapter]
        return Book(title=title, chapters=all_chapters, tags=keywords or [], sources=sources)
    except TextGenerationError as e:
        logger.error("Text generation error in book with research: %s", str(e))
        raise BookGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning("Rate limit exceeded in book with research: %s", str(e))
        raise BookGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning("Invalid input for book with research: %s", str(e))
        raise BookGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error(
            "Unexpected error generating book with research: %s", str(e), exc_info=True
        )
        raise BookGenerationError(f"Unexpected error: {str(e)}") from e
