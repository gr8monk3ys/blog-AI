"""
Book generation functionality.
"""

import argparse
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..blog_sections.conclusion_generator import generate_conclusion
from ..blog_sections.introduction_generator import generate_introduction
from ..planning.content_outline import (
    generate_content_outline,
    generate_content_outline_with_research,
)
from ..planning.topic_clusters import (
    generate_topic_clusters,
    generate_topic_clusters_with_research,
)
from ..post_processing.file_saver import save_book
from ..post_processing.format_converter import convert_format
from ..post_processing.humanizer import humanize_content
from ..post_processing.proofreader import proofread_content
from ..research.web_researcher import conduct_web_research
from ..text_generation.core import (
    GenerationOptions,
    LLMProvider,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
    generate_text,
)
from ..types.content import Book, Chapter, ContentType, Section, SubTopic, Topic
from ..types.post_processing import FormatConversionOptions, OutputFormat, SaveOptions
from ..types.providers import ProviderType


class BookGenerationError(Exception):
    """Exception raised for errors in the book generation process."""

    pass


def generate_book(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> Book:
    """
    Generate a book.

    Args:
        title: The title of the book.
        num_chapters: The number of chapters to include in the book.
        sections_per_chapter: The number of sections per chapter.
        keywords: The keywords to include in the book.
        tone: The tone of the book.
        provider_type: The type of provider to use.
        options: Options for text generation.

    Returns:
        The generated book.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)

        # Generate topic clusters for chapters
        clusters = generate_topic_clusters(
            title, num_chapters, sections_per_chapter, provider, options
        )

        # Generate chapters
        chapters = []

        for i, cluster in enumerate(clusters):
            # Generate chapter
            chapter = generate_chapter(
                title=cluster.main_topic,
                subtopics=cluster.subtopics,
                keywords=cluster.keywords,
                tone=tone,
                provider=provider,
                options=options,
            )

            chapters.append(chapter)

        # Generate introduction chapter
        introduction_chapter = generate_introduction_chapter(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Generate conclusion chapter
        conclusion_chapter = generate_conclusion_chapter(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Combine all chapters
        all_chapters = [introduction_chapter] + chapters + [conclusion_chapter]

        return Book(title=title, chapters=all_chapters, tags=keywords or [])
    except TextGenerationError as e:
        logger.error(f"Text generation error in book: {str(e)}")
        raise BookGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in book generation: {str(e)}")
        raise BookGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning(f"Invalid input for book: {str(e)}")
        raise BookGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating book: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error: {str(e)}") from e


def generate_book_with_research(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> Book:
    """
    Generate a book with research.

    Args:
        title: The title of the book.
        num_chapters: The number of chapters to include in the book.
        sections_per_chapter: The number of sections per chapter.
        keywords: The keywords to include in the book.
        tone: The tone of the book.
        provider_type: The type of provider to use.
        options: Options for text generation.

    Returns:
        The generated book.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)

        # Conduct research
        research_keywords = [title]
        if keywords:
            research_keywords.extend(keywords)

        research_results = conduct_web_research(research_keywords)

        # Generate topic clusters for chapters
        clusters = generate_topic_clusters_with_research(
            title, num_chapters, sections_per_chapter, provider, options
        )

        # Generate chapters
        chapters = []

        for i, cluster in enumerate(clusters):
            # Generate chapter
            chapter = generate_chapter_with_research(
                title=cluster.main_topic,
                subtopics=cluster.subtopics,
                research_results=research_results,
                keywords=cluster.keywords,
                tone=tone,
                provider=provider,
                options=options,
            )

            chapters.append(chapter)

        # Generate introduction chapter
        introduction_chapter = generate_introduction_chapter_with_research(
            title=title,
            chapters=chapters,
            research_results=research_results,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Generate conclusion chapter
        conclusion_chapter = generate_conclusion_chapter(
            title=title,
            chapters=chapters,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Combine all chapters
        all_chapters = [introduction_chapter] + chapters + [conclusion_chapter]

        return Book(title=title, chapters=all_chapters, tags=keywords or [])
    except TextGenerationError as e:
        logger.error(f"Text generation error in book with research: {str(e)}")
        raise BookGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in book with research: {str(e)}")
        raise BookGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning(f"Invalid input for book with research: {str(e)}")
        raise BookGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating book with research: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error: {str(e)}") from e


def generate_chapter(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Chapter:
    """
    Generate a chapter.

    Args:
        title: The title of the chapter.
        subtopics: The subtopics to include in the chapter.
        keywords: The keywords to include in the chapter.
        tone: The tone of the chapter.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated chapter.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Generate sections
        sections = []

        # Generate introduction section
        introduction_section = generate_introduction_section(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )
        sections.append(introduction_section)

        # Generate main sections
        for subtopic in subtopics:
            section = generate_section(
                section_title=subtopic,
                keywords=keywords,
                tone=tone,
                provider=provider,
                options=options,
            )
            sections.append(section)

        # Generate conclusion section
        conclusion_section = generate_conclusion_section(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )
        sections.append(conclusion_section)

        # Convert sections to topics
        topics = []
        for section in sections:
            for subtopic in section.subtopics:
                topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=1, title=title, topics=topics)  # Default chapter number
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate chapter '{title}': {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for chapter '{title}': {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during chapter generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating chapter: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating chapter: {str(e)}") from e


def generate_chapter_with_research(
    title: str,
    subtopics: List[str],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Chapter:
    """
    Generate a chapter with research.

    Args:
        title: The title of the chapter.
        subtopics: The subtopics to include in the chapter.
        research_results: The research results.
        keywords: The keywords to include in the chapter.
        tone: The tone of the chapter.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated chapter.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Generate sections
        sections = []

        # Generate introduction section
        introduction_section = generate_introduction_section_with_research(
            title=title,
            subtopics=subtopics,
            research_results=research_results,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )
        sections.append(introduction_section)

        # Generate main sections
        for subtopic in subtopics:
            section = generate_section_with_research(
                section_title=subtopic,
                research_results=research_results,
                keywords=keywords,
                tone=tone,
                provider=provider,
                options=options,
            )
            sections.append(section)

        # Generate conclusion section
        conclusion_section = generate_conclusion_section(
            title=title,
            subtopics=subtopics,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )
        sections.append(conclusion_section)

        # Convert sections to topics
        topics = []
        for section in sections:
            for subtopic in section.subtopics:
                topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(number=1, title=title, topics=topics)  # Default chapter number
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate chapter '{title}' with research: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for chapter with research: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during chapter with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating chapter with research: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating chapter with research: {str(e)}") from e


def generate_introduction_chapter(
    title: str,
    chapters: List[Chapter],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Chapter:
    """
    Generate an introduction chapter.

    Args:
        title: The title of the book.
        chapters: The chapters in the book.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction chapter.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for introduction chapter generation
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

        # Generate introduction content
        introduction_content = generate_text(prompt, provider, options)

        # Clean up the introduction content
        introduction_content = introduction_content.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=introduction_content)

        # Create section
        section = Section(title="Introduction", subtopics=[subtopic])

        # Convert section to topics
        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(
            number=0,  # Introduction chapter is chapter 0
            title="Introduction",
            topics=topics,
        )
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate introduction chapter: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for introduction chapter: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during introduction chapter generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction chapter: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating introduction chapter: {str(e)}") from e


def generate_introduction_chapter_with_research(
    title: str,
    chapters: List[Chapter],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Chapter:
    """
    Generate an introduction chapter with research.

    Args:
        title: The title of the book.
        chapters: The chapters in the book.
        research_results: The research results.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction chapter.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for introduction chapter generation
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

        # Generate introduction content
        introduction_content = generate_text(prompt, provider, options)

        # Clean up the introduction content
        introduction_content = introduction_content.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=introduction_content)

        # Create section
        section = Section(title="Introduction", subtopics=[subtopic])

        # Convert section to topics
        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(
            number=0,  # Introduction chapter is chapter 0
            title="Introduction",
            topics=topics,
        )
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate introduction chapter with research: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for introduction chapter with research: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during introduction chapter with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction chapter with research: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating introduction chapter with research: {str(e)}") from e


def generate_conclusion_chapter(
    title: str,
    chapters: List[Chapter],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Chapter:
    """
    Generate a conclusion chapter.

    Args:
        title: The title of the book.
        chapters: The chapters in the book.
        keywords: The keywords to include in the conclusion.
        tone: The tone of the conclusion.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated conclusion chapter.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for conclusion chapter generation
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

        # Generate conclusion content
        conclusion_content = generate_text(prompt, provider, options)

        # Clean up the conclusion content
        conclusion_content = conclusion_content.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=conclusion_content)

        # Create section
        section = Section(title="Conclusion", subtopics=[subtopic])

        # Convert section to topics
        topics = []
        for subtopic in section.subtopics:
            topics.append(Topic(title=section.title, content=subtopic.content))

        return Chapter(
            number=99,  # Conclusion chapter is the last chapter
            title="Conclusion",
            topics=topics,
        )
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate conclusion chapter: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for conclusion chapter: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during conclusion chapter generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating conclusion chapter: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating conclusion chapter: {str(e)}") from e


def generate_introduction_section(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section.

    Args:
        title: The title of the chapter.
        subtopics: The subtopics in the chapter.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction section.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Generate introduction
        introduction = generate_introduction(
            title=title,
            outline="\n".join(subtopics),
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Create subtopic
        subtopic = SubTopic(title="", content=introduction.content)

        # Create section
        section = Section(title="Introduction", subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate introduction section: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for introduction section: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during introduction section generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction section: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating introduction section: {str(e)}") from e


def generate_introduction_section_with_research(
    title: str,
    subtopics: List[str],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section with research.

    Args:
        title: The title of the chapter.
        subtopics: The subtopics in the chapter.
        research_results: The research results.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction section.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for introduction generation
        prompt = f"""
        Generate an engaging introduction for a chapter titled '{title}' with the following subtopics:
        
        {", ".join(subtopics)}
        """

        if keywords:
            prompt += f"\n\nKeywords: {', '.join(keywords)}"

        prompt += f"""
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        
        Requirements:
        - The introduction should be 3-4 paragraphs.
        - Include a compelling hook in the first paragraph to grab the reader's attention.
        - Clearly state the purpose or thesis of the chapter.
        - Include at least one of the main keywords naturally.
        - Incorporate insights from the research.
        - Set the tone and expectations for the rest of the chapter.
        - Use a {tone} tone throughout.
        
        Return only the introduction, nothing else.
        """

        # Generate introduction
        introduction_text = generate_text(prompt, provider, options)

        # Clean up the introduction
        introduction_text = introduction_text.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=introduction_text)

        # Create section
        section = Section(title="Introduction", subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate introduction section with research: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for introduction section with research: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during introduction section with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction section with research: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating introduction section with research: {str(e)}") from e


def generate_section(
    section_title: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a section.

    Args:
        section_title: The title of the section.
        keywords: The keywords to include in the section.
        tone: The tone of the section.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated section.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for section generation
        prompt = f"""
        Generate content for a book section with the following title:
        
        {section_title}
        """

        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"

        prompt += f"""
        
        Requirements:
        - The content should be 4-5 paragraphs.
        - Include relevant information, examples, and insights.
        - Use a {tone} tone throughout.
        - Write in a clear, engaging style.
        """

        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the content.
            """

        prompt += """
        Return only the section content, nothing else.
        """

        # Generate section content
        section_content = generate_text(prompt, provider, options)

        # Clean up the section content
        section_content = section_content.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=section_content)

        # Create section
        section = Section(title=section_title, subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate section: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for section: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during section generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating section: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating section: {str(e)}") from e


def generate_section_with_research(
    section_title: str,
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a section with research.

    Args:
        section_title: The title of the section.
        research_results: The research results.
        keywords: The keywords to include in the section.
        tone: The tone of the section.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated section.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for section generation
        prompt = f"""
        Generate content for a book section with the following title:
        
        {section_title}
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        """

        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"

        prompt += f"""
        
        Requirements:
        - The content should be 4-5 paragraphs.
        - Include relevant information, examples, and insights from the research.
        - Use a {tone} tone throughout.
        - Write in a clear, engaging style.
        """

        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the content.
            """

        prompt += """
        Return only the section content, nothing else.
        """

        # Generate section content
        section_content = generate_text(prompt, provider, options)

        # Clean up the section content
        section_content = section_content.strip()

        # Create subtopic
        subtopic = SubTopic(title="", content=section_content)

        # Create section
        section = Section(title=section_title, subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate section with research: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for section with research: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during section with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating section with research: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating section with research: {str(e)}") from e


def generate_conclusion_section(
    title: str,
    subtopics: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a conclusion section.

    Args:
        title: The title of the chapter.
        subtopics: The subtopics in the chapter.
        keywords: The keywords to include in the conclusion.
        tone: The tone of the conclusion.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated conclusion section.

    Raises:
        BookGenerationError: If an error occurs during generation.
    """
    try:
        # Create content from subtopics
        content = f"Title: {title}\n\nSubtopics:\n"
        for subtopic in subtopics:
            content += f"- {subtopic}\n"

        # Generate conclusion
        conclusion = generate_conclusion(
            title=title,
            content=content,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options,
        )

        # Create subtopic
        subtopic = SubTopic(title="", content=conclusion.content)

        # Create section
        section = Section(title="Conclusion", subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed to generate conclusion section: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters for conclusion section: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during conclusion section generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating conclusion section: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error generating conclusion section: {str(e)}") from e


def post_process_book(
    book: Book,
    proofread: bool = True,
    humanize: bool = True,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Book:
    """
    Post-process a book.

    Args:
        book: The book to post-process.
        proofread: Whether to proofread the book.
        humanize: Whether to humanize the book.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The post-processed book.

    Raises:
        BookGenerationError: If an error occurs during post-processing.
    """
    try:
        # Create a copy of the book
        processed_book = Book(title=book.title, chapters=[])

        # Process each chapter
        for i, chapter in enumerate(book.chapters):
            # Process each topic
            processed_topics = []
            for topic in chapter.topics:
                processed_topic = Topic(title=topic.title, content=topic.content)

                if topic.content:
                    # Proofread content if requested
                    if proofread:
                        proofreading_result = proofread_content(
                            topic.content, provider=provider, options=options
                        )
                        if proofreading_result.corrected_text:
                            processed_topic.content = proofreading_result.corrected_text

                    # Humanize content if requested
                    if humanize:
                        processed_topic.content = humanize_content(
                            processed_topic.content, provider=provider, options=options
                        )

                processed_topics.append(processed_topic)

            # Create processed chapter
            processed_chapter = Chapter(
                number=i, title=chapter.title, topics=processed_topics
            )

            processed_book.chapters.append(processed_chapter)

        return processed_book
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed during post-processing: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters during post-processing: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(f"Invalid data structure during post-processing: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error post-processing book: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error post-processing book: {str(e)}") from e


def save_book_to_markdown(book: Book, file_path: str) -> None:
    """
    Save a book to a Markdown file.

    Args:
        book: The book to save.
        file_path: The path to save the book to.

    Raises:
        BookGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Create Markdown content
        markdown = f"# {book.title}\n\n"

        # Add metadata
        markdown += "---\n"
        markdown += f"title: {book.title}\n"

        # Add optional metadata if available
        if hasattr(book, "date"):
            markdown += f"date: {book.date}\n"

        if hasattr(book, "tags") and book.tags:
            markdown += f"tags: {', '.join(book.tags)}\n"

        markdown += "---\n\n"

        # Add chapters
        for chapter in book.chapters:
            markdown += f"## {chapter.title}\n\n"

            # Group topics by title to recreate sections
            sections = {}
            for topic in chapter.topics:
                if topic.title not in sections:
                    sections[topic.title] = []
                sections[topic.title].append(topic.content)

            # Add sections
            for section_title, contents in sections.items():
                markdown += f"### {section_title}\n\n"

                for content in contents:
                    if content:
                        markdown += f"{content}\n\n"

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    except PermissionError as e:
        raise BookGenerationError(f"Permission denied writing book to Markdown: {str(e)}") from e
    except OSError as e:
        raise BookGenerationError(f"File system error saving book to Markdown: {str(e)}") from e
    except TypeError as e:
        raise BookGenerationError(f"Invalid data type during Markdown serialization: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error saving book to Markdown: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error saving book to Markdown: {str(e)}") from e


def save_book_to_json(book: Book, file_path: str) -> None:
    """
    Save a book to a JSON file.

    Args:
        book: The book to save.
        file_path: The path to save the book to.

    Raises:
        BookGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Convert book to JSON-serializable format
        book_data = {"title": book.title, "chapters": []}

        # Add optional metadata if available
        if hasattr(book, "date"):
            book_data["date"] = book.date

        if hasattr(book, "tags") and book.tags:
            book_data["tags"] = book.tags

        for chapter in book.chapters:
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "topics": [],
            }

            for topic in chapter.topics:
                topic_data = {"title": topic.title, "content": topic.content}

                chapter_data["topics"].append(topic_data)

            book_data["chapters"].append(chapter_data)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2)
    except PermissionError as e:
        raise BookGenerationError(f"Permission denied writing book to JSON: {str(e)}") from e
    except OSError as e:
        raise BookGenerationError(f"File system error saving book to JSON: {str(e)}") from e
    except TypeError as e:
        raise BookGenerationError(f"JSON serialization error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error saving book to JSON: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error saving book to JSON: {str(e)}") from e


def load_book_from_json(file_path: str) -> Book:
    """
    Load a book from a JSON file.

    Args:
        file_path: The path to load the book from.

    Returns:
        The loaded book.

    Raises:
        BookGenerationError: If an error occurs during loading.
    """
    try:
        # Read from file
        with open(file_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        # Convert JSON data to Book
        chapters = []

        for chapter_data in book_data["chapters"]:
            # Check if the JSON is in the new format (with topics) or old format (with sections)
            if "topics" in chapter_data:
                # New format
                topics = []
                for topic_data in chapter_data["topics"]:
                    topic = Topic(
                        title=topic_data["title"], content=topic_data["content"]
                    )
                    topics.append(topic)

                chapter = Chapter(
                    number=chapter_data.get("number", 0),
                    title=chapter_data["title"],
                    topics=topics,
                )
            else:
                # Old format (for backward compatibility)
                topics = []
                for section_data in chapter_data.get("sections", []):
                    for subtopic_data in section_data.get("subtopics", []):
                        topic = Topic(
                            title=section_data["title"],
                            content=subtopic_data.get("content", ""),
                        )
                        topics.append(topic)

                chapter = Chapter(
                    number=0,  # Default number for old format
                    title=chapter_data["title"],
                    topics=topics,
                )

            chapters.append(chapter)

        # Create book
        book_args = {"title": book_data["title"], "chapters": chapters}

        # Add optional fields if present
        if "tags" in book_data:
            book_args["tags"] = book_data["tags"]

        if "date" in book_data:
            book_args["date"] = book_data["date"]

        book = Book(**book_args)

        return book
    except FileNotFoundError as e:
        raise BookGenerationError(f"Book file not found: {file_path}") from e
    except PermissionError as e:
        raise BookGenerationError(f"Permission denied reading book from JSON: {str(e)}") from e
    except json.JSONDecodeError as e:
        raise BookGenerationError(f"Invalid JSON format in book file: {str(e)}") from e
    except KeyError as e:
        raise BookGenerationError(f"Missing required field in book JSON: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading book from JSON: {str(e)}", exc_info=True)
        raise BookGenerationError(f"Unexpected error loading book from JSON: {str(e)}") from e


def main():
    """
    Main function for the book generation module.
    """
    parser = argparse.ArgumentParser(description="Generate a book")
    parser.add_argument("title", help="The title of the book")
    parser.add_argument("--output", help="The output file path", default="book.md")
    parser.add_argument(
        "--chapters", help="The number of chapters", type=int, default=5
    )
    parser.add_argument(
        "--sections", help="The number of sections per chapter", type=int, default=3
    )
    parser.add_argument(
        "--keywords", help="The keywords to include in the book", nargs="+"
    )
    parser.add_argument("--tone", help="The tone of the book", default="informative")
    parser.add_argument(
        "--research", help="Whether to use research", action="store_true"
    )
    parser.add_argument(
        "--proofread", help="Whether to proofread the book", action="store_true"
    )
    parser.add_argument(
        "--humanize", help="Whether to humanize the book", action="store_true"
    )
    parser.add_argument("--provider", help="The provider to use", default="openai")

    args = parser.parse_args()

    try:
        # Generate book
        if args.research:
            book = generate_book_with_research(
                title=args.title,
                num_chapters=args.chapters,
                sections_per_chapter=args.sections,
                keywords=args.keywords,
                tone=args.tone,
                provider_type=args.provider,
            )
        else:
            book = generate_book(
                title=args.title,
                num_chapters=args.chapters,
                sections_per_chapter=args.sections,
                keywords=args.keywords,
                tone=args.tone,
                provider_type=args.provider,
            )

        # Post-process book
        if args.proofread or args.humanize:
            book = post_process_book(
                book=book,
                proofread=args.proofread,
                humanize=args.humanize,
                provider=create_provider_from_env(args.provider),
            )

        # Save book
        if args.output.endswith(".md"):
            save_book_to_markdown(book, args.output)
        elif args.output.endswith(".json"):
            save_book_to_json(book, args.output)
        else:
            save_options = SaveOptions(
                file_path=args.output, format=OutputFormat.MARKDOWN
            )
            save_book(book, save_options)

        print(f"Book generated successfully: {args.output}")
    except Exception as e:
        print(f"Error generating book: {str(e)}")
        raise


if __name__ == "__main__":
    main()
