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
        prompt = f"""
        Generate an engaging introduction for a chapter titled '{title}' with the following subtopics:
        
        {", ".join(subtopics)}
        """

        if keywords:
            prompt += f"\n\nKeywords: {', '.join(keywords)}"

        if brand_voice:
            prompt += f"\n\nBRAND VOICE SUMMARY (follow strictly):\n{brand_voice}\n"

        prompt += f"""
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        
        Requirements:
        - The introduction should be 3-4 paragraphs.
        - Include a compelling hook in the first paragraph to grab the reader's attention.
        - Clearly state the purpose or thesis of the chapter.
        - Include at least one of the main keywords naturally.
        - Incorporate insights from the research.
        - Add citations like [1] at the end of sentences that rely on a source.
        - Only cite sources provided in the Sources list; do not invent citations.
        - Set the tone and expectations for the rest of the chapter.
        - Use a {tone} tone throughout.
        
        Return only the introduction, nothing else.
        """

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
        prompt = f"""
        Generate content for a book section with the following title:
        
        {section_title}
        """

        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"

        if brand_voice:
            prompt += f"\n\nBRAND VOICE SUMMARY (follow strictly):\n{brand_voice}\n"

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
        prompt = f"""
        Generate content for a book section with the following title:
        
        {section_title}
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        """

        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"

        if brand_voice:
            prompt += f"\n\nBRAND VOICE SUMMARY (follow strictly):\n{brand_voice}\n"

        prompt += f"""
        
        Requirements:
        - The content should be 4-5 paragraphs.
        - Include relevant information, examples, and insights from the research.
        - Add citations like [1] at the end of sentences that rely on a source.
        - Only cite sources provided in the Sources list; do not invent citations.
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
