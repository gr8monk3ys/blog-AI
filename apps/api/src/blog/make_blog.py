"""
Blog post generation functionality.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..blog_sections.conclusion_generator import generate_conclusion
from ..blog_sections.faq_generator import generate_faqs
from ..blog_sections.introduction_generator import generate_introduction
from ..planning.content_outline import (
    generate_content_outline,
    generate_content_outline_with_research,
)
from ..post_processing.humanizer import humanize_content
from ..post_processing.proofreader import proofread_content
from ..research.web_researcher import (
    conduct_web_research,
    extract_research_sources,
    format_research_results_for_prompt,
)
from ..seo.meta_description import generate_meta_description
from ..text_generation.core import (
    GenerationOptions,
    LLMProvider,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
    generate_text,
)
from ..types.content import BlogPost, ContentType, Section, SubTopic, SourceCitation
from ..types.providers import ProviderType


class BlogGenerationError(Exception):
    """Exception raised for errors in the blog generation process."""

    pass


def generate_blog_post(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    include_faqs: bool = True,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> BlogPost:
    """
    Generate a blog post.

    Args:
        title: The title of the blog post.
        keywords: The keywords to include in the blog post.
        num_sections: The number of sections to include in the blog post.
        include_faqs: Whether to include FAQs in the blog post.
        tone: The tone of the blog post.
        provider_type: The type of provider to use.
        options: Options for text generation.

    Returns:
        The generated blog post.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)

        # Generate outline
        outline = generate_content_outline(
            title, keywords, num_sections, provider, options
        )

        # Generate sections
        sections = []

        # Generate introduction
        introduction_section = generate_introduction_section(
            title, outline.sections, keywords, tone, brand_voice, provider, options
        )
        sections.append(introduction_section)

        # Generate main sections
        for i, section_title in enumerate(
            outline.sections[1:-1]
        ):  # Skip introduction and conclusion
            section = generate_section(section_title, keywords, tone, brand_voice, provider, options)
            sections.append(section)

        # Generate conclusion
        conclusion_section = generate_conclusion_section(
            title, outline.sections, keywords, tone, brand_voice, provider, options
        )
        sections.append(conclusion_section)

        # Generate FAQs if requested
        if include_faqs:
            # Combine all section content for context
            content = ""
            for section in sections:
                content += section.title + "\n"
                for subtopic in section.subtopics:
                    if subtopic.content:
                        content += subtopic.content + "\n"

            # Generate FAQs
            faq_section = generate_faq_section(
                title, content, keywords, tone, brand_voice, provider, options
            )
            sections.append(faq_section)

        # Generate meta description
        description = generate_meta_description(
            title, keywords or [], provider=provider, options=options
        ).content

        return BlogPost(
            title=title, description=description, sections=sections, tags=keywords or []
        )
    except TextGenerationError as e:
        logger.error(f"Text generation error in blog post: {str(e)}")
        raise BlogGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in blog post generation: {str(e)}")
        raise BlogGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning(f"Invalid input for blog post: {str(e)}")
        raise BlogGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating blog post: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error: {str(e)}") from e


def generate_blog_post_with_research(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    include_faqs: bool = True,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> BlogPost:
    """
    Generate a blog post with research.

    Args:
        title: The title of the blog post.
        keywords: The keywords to include in the blog post.
        num_sections: The number of sections to include in the blog post.
        include_faqs: Whether to include FAQs in the blog post.
        tone: The tone of the blog post.
        provider_type: The type of provider to use.
        options: Options for text generation.

    Returns:
        The generated blog post.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)

        # Conduct research
        research_keywords = [title]
        if keywords:
            research_keywords.extend(keywords)

        research_results = conduct_web_research(research_keywords)
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
            research_results, max_sources=8, max_chars=2200
        )

        # Generate outline
        outline = generate_content_outline_with_research(
            title, keywords, num_sections, provider, options
        )

        # Generate sections
        sections = []

        # Generate introduction
        introduction_section = generate_introduction_section_with_research(
            title,
            outline.sections,
            research_context,
            keywords,
            tone,
            brand_voice,
            provider,
            options,
        )
        sections.append(introduction_section)

        # Generate main sections
        for i, section_title in enumerate(
            outline.sections[1:-1]
        ):  # Skip introduction and conclusion
            section = generate_section_with_research(
                section_title,
                research_context,
                keywords,
                tone,
                brand_voice,
                provider,
                options,
            )
            sections.append(section)

        # Generate conclusion
        conclusion_section = generate_conclusion_section(
            title, outline.sections, keywords, tone, brand_voice, provider, options
        )
        sections.append(conclusion_section)

        # Generate FAQs if requested
        if include_faqs:
            # Combine all section content for context
            content = ""
            for section in sections:
                content += section.title + "\n"
                for subtopic in section.subtopics:
                    if subtopic.content:
                        content += subtopic.content + "\n"

            # Generate FAQs
            faq_section = generate_faq_section(
                title, content, keywords, tone, brand_voice, provider, options
            )
            sections.append(faq_section)

        # Generate meta description
        description = generate_meta_description(
            title, keywords or [], provider=provider, options=options
        ).content

        return BlogPost(
            title=title,
            description=description,
            sections=sections,
            tags=keywords or [],
            sources=sources,
        )
    except TextGenerationError as e:
        logger.error(f"Text generation error in blog post with research: {str(e)}")
        raise BlogGenerationError(f"Failed to generate text: {str(e)}") from e
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in blog post with research: {str(e)}")
        raise BlogGenerationError(f"Rate limit exceeded: {str(e)}") from e
    except ValueError as e:
        logger.warning(f"Invalid input for blog post with research: {str(e)}")
        raise BlogGenerationError(f"Invalid input: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating blog post with research: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error: {str(e)}") from e


def generate_introduction_section(
    title: str,
    outline_sections: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section.

    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction section.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Generate introduction
        introduction = generate_introduction(
            title=title,
            outline="\n".join(outline_sections),
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        # Create subtopic
        subtopic = SubTopic(title="", content=introduction.content)

        # Create section
        section = Section(title="Introduction", subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BlogGenerationError(f"Failed to generate introduction: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for introduction generation: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during introduction generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction section: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating introduction section: {str(e)}") from e


def generate_introduction_section_with_research(
    title: str,
    outline_sections: List[str],
    research_context: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate an introduction section with research.

    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        research_results: The research results.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction section.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: Research-backed introduction with citation support.
        # We front-load a concrete data-driven hook and instruct on natural citation flow.
        prompt = f"""Write the introduction for a research-backed blog post.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Article sections (for context on scope):
{", ".join(outline_sections)}

RESEARCH CONTEXT (cite specific findings from this):
{research_context}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with a concrete finding, statistic, or insight from the research.
Use specific numbers, names, or results -- not vague claims.
Do NOT open with "In today's...", "In the ever-evolving...", or any generic opener.
Add a citation [1] when referencing a specific source.

Paragraph 2 -- THE PROBLEM/CONTEXT:
Establish WHY this topic matters right now using research findings.
Reference specific trends or data. Cite sources with [N] notation.

Paragraph 3 -- THE PROMISE:
Tell the reader exactly what they'll learn. Be specific and actionable.

CITATION RULES:
- Add [N] at the end of sentences that rely on a specific source.
- Only cite sources listed in the research context -- never invent citations.
- Weave citations naturally: "According to recent data, X increased by 40% [2]"
  not "Research shows that [1][2][3]..."

STYLE RULES:
- Write like a knowledgeable friend, not a textbook
- Use contractions naturally (you'll, it's, don't)
- Vary sentence length for rhythm
- Tone: {tone}
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "it's worth mentioning", "in conclusion"

Return ONLY the introduction paragraphs. No headings, labels, or meta-commentary."""

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
        raise BlogGenerationError(f"Failed to generate introduction with research: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for introduction with research: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during introduction with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating introduction section with research: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating introduction section with research: {str(e)}") from e


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

    Args:
        section_title: The title of the section.
        keywords: The keywords to include in the section.
        tone: The tone of the section.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated section.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: Body section generation. Each section needs to deliver real
        # value -- not just pad word count. We push for specific examples, actionable
        # advice, and varied paragraph structures.
        prompt = f"""Write the content for a blog post section.

Section title: {section_title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

CONTENT REQUIREMENTS (3-4 paragraphs):

- Open the section with a clear statement of what this section covers and why
  it matters. Do NOT start with "When it comes to..." or "It's important to..."
- Include at least ONE specific example, case study, data point, or practical tip.
  Vague advice like "consider your options" is worthless -- tell the reader what
  to actually do.
- Each paragraph should advance the reader's understanding. No filler paragraphs
  that just restate the heading in different words.
- Close the section with a transition thought that connects to what comes next.

STYLE RULES:
- Write like a knowledgeable colleague explaining something useful
- Vary sentence length: short (5-8 words), medium (12-18), and occasional long
- Use contractions naturally (you'll, it's, don't, we're)
- Use "you" and "your" to address the reader directly
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive,
  multifaceted, aforementioned
- BANNED phrases: "it's important to note", "it's worth mentioning", "when it comes to",
  "in today's world", "at the end of the day"
"""

        if keywords:
            prompt += "- Weave keywords in naturally where they fit -- never force them.\n"

        prompt += """
Return ONLY the section content. No section title, no headings, no meta-commentary."""

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
        raise BlogGenerationError(f"Failed to generate section '{section_title}': {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for section '{section_title}': {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during section generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating section: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating section: {str(e)}") from e


def generate_section_with_research(
    section_title: str,
    research_context: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
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
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: Research-backed body section. We instruct the model to use
        # research findings as evidence rather than just restating them, and to cite
        # sources naturally within the prose.
        prompt = f"""Write the content for a research-backed blog post section.

Section title: {section_title}

RESEARCH CONTEXT (use specific findings as evidence):
{research_context}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

CONTENT REQUIREMENTS (3-4 paragraphs):

- Open with a clear statement of what this section covers and why it matters.
  Do NOT start with "When it comes to..." or "It's important to..."
- Use research findings as EVIDENCE to support your points -- don't just list
  what the research says. Explain what it means for the reader.
- Include specific data points, examples, or expert insights from the research.
- Each paragraph should advance the reader's understanding. No filler.
- Close with a transition that connects to what comes next.

CITATION RULES:
- Add [N] at the end of sentences that reference a specific source.
- Only cite sources listed in the research context -- NEVER invent citations.
- Spread citations naturally: 2-4 per section is typical. Don't cluster them
  all in one paragraph.
- Weave citations into the prose: "Teams using X saw a 30% improvement [2]"
  not "According to research [1][2], there are improvements."

STYLE RULES:
- Write like a knowledgeable colleague, not a term paper
- Vary sentence length for rhythm
- Use contractions naturally (you'll, it's, don't)
- Address the reader with "you" and "your"
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, comprehensive
- BANNED phrases: "it's important to note", "it's worth mentioning", "when it comes to"
"""

        if keywords:
            prompt += "- Weave keywords in naturally -- never force them.\n"

        prompt += """
Return ONLY the section content. No title, no headings, no meta-commentary."""

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
        raise BlogGenerationError(f"Failed to generate section '{section_title}' with research: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for section with research: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during section with research: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating section with research: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating section with research: {str(e)}") from e


def generate_conclusion_section(
    title: str,
    outline_sections: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a conclusion section.

    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        keywords: The keywords to include in the conclusion.
        tone: The tone of the conclusion.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated conclusion section.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create content from outline sections
        content = f"Title: {title}\n\nSections:\n"
        for section in outline_sections:
            content += f"- {section}\n"

        # Generate conclusion
        conclusion = generate_conclusion(
            title=title,
            content=content,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider=provider,
            options=options,
        )

        # Create subtopic
        subtopic = SubTopic(title="", content=conclusion.content)

        # Create section
        section = Section(title="Conclusion", subtopics=[subtopic])

        return section
    except TextGenerationError as e:
        raise BlogGenerationError(f"Failed to generate conclusion: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for conclusion generation: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during conclusion generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating conclusion section: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating conclusion section: {str(e)}") from e


def generate_faq_section(
    title: str,
    content: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Section:
    """
    Generate a FAQ section.

    Args:
        title: The title of the blog post.
        content: The content of the blog post.
        keywords: The keywords to include in the FAQs.
        tone: The tone of the FAQs.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated FAQ section.

    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Generate FAQs
        faq_result = generate_faqs(
            content=content, count=5, brand_voice=brand_voice, provider=provider, options=options
        )

        # Create subtopics
        subtopics = []

        for faq in faq_result.faqs:
            subtopic = SubTopic(title=faq.question, content=faq.answer)

            subtopics.append(subtopic)

        # Create section
        section = Section(title="Frequently Asked Questions", subtopics=subtopics)

        return section
    except TextGenerationError as e:
        raise BlogGenerationError(f"Failed to generate FAQ section: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters for FAQ generation: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during FAQ generation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error generating FAQ section: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error generating FAQ section: {str(e)}") from e


def post_process_blog_post(
    blog_post: BlogPost,
    proofread: bool = True,
    humanize: bool = True,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> BlogPost:
    """
    Post-process a blog post.

    Args:
        blog_post: The blog post to post-process.
        proofread: Whether to proofread the blog post.
        humanize: Whether to humanize the blog post.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The post-processed blog post.

    Raises:
        BlogGenerationError: If an error occurs during post-processing.
    """
    try:
        # Create a copy of the blog post
        processed_blog_post = BlogPost(
            title=blog_post.title,
            description=blog_post.description,
            sections=[],
            tags=blog_post.tags,
            date=blog_post.date,
            image=blog_post.image,
        )

        # Process each section
        for section in blog_post.sections:
            processed_section = Section(title=section.title, subtopics=[])

            for subtopic in section.subtopics:
                processed_subtopic = SubTopic(
                    title=subtopic.title, content=subtopic.content
                )

                if subtopic.content:
                    # Proofread content if requested
                    if proofread:
                        proofreading_result = proofread_content(
                            subtopic.content,
                            provider=provider,
                            generation_options=options,
                        )
                        if proofreading_result.corrected_text:
                            processed_subtopic.content = (
                                proofreading_result.corrected_text
                            )

                    # Humanize content if requested
                    if humanize:
                        processed_subtopic.content = humanize_content(
                            processed_subtopic.content,
                            provider=provider,
                            generation_options=options,
                        )

                processed_section.subtopics.append(processed_subtopic)

            processed_blog_post.sections.append(processed_section)

        return processed_blog_post
    except TextGenerationError as e:
        raise BlogGenerationError(f"Failed during post-processing: {str(e)}") from e
    except ValueError as e:
        raise BlogGenerationError(f"Invalid parameters during post-processing: {str(e)}") from e
    except AttributeError as e:
        raise BlogGenerationError(f"Invalid data structure during post-processing: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error post-processing blog post: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Unexpected error post-processing blog post: {str(e)}") from e


def save_blog_post_to_markdown(blog_post: BlogPost, file_path: str) -> None:
    """
    Save a blog post to a Markdown file.

    Args:
        blog_post: The blog post to save.
        file_path: The path to save the blog post to.

    Raises:
        BlogGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Create Markdown content
        markdown = f"# {blog_post.title}\n\n"

        # Add metadata
        markdown += "---\n"
        markdown += f"title: {blog_post.title}\n"
        markdown += f"description: {blog_post.description}\n"
        markdown += f"date: {blog_post.date}\n"
        markdown += f"image: {blog_post.image}\n"
        markdown += f"tags: {', '.join(blog_post.tags)}\n"
        markdown += "---\n\n"

        # Add sections
        for section in blog_post.sections:
            markdown += f"## {section.title}\n\n"

            for subtopic in section.subtopics:
                if subtopic.title:
                    markdown += f"### {subtopic.title}\n\n"

                if subtopic.content:
                    markdown += f"{subtopic.content}\n\n"

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    except PermissionError as e:
        raise BlogGenerationError(f"Permission denied writing to {file_path}: {str(e)}") from e
    except OSError as e:
        raise BlogGenerationError(f"File system error saving to {file_path}: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error saving blog post to Markdown: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Error saving blog post to Markdown: {str(e)}") from e


def save_blog_post_to_json(blog_post: BlogPost, file_path: str) -> None:
    """
    Save a blog post to a JSON file.

    Args:
        blog_post: The blog post to save.
        file_path: The path to save the blog post to.

    Raises:
        BlogGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Convert blog post to JSON-serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": [],
        }

        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}

            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}

                section_data["subtopics"].append(subtopic_data)

            blog_post_data["sections"].append(section_data)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(blog_post_data, f, indent=2)
    except PermissionError as e:
        raise BlogGenerationError(f"Permission denied writing to {file_path}: {str(e)}") from e
    except OSError as e:
        raise BlogGenerationError(f"File system error saving to {file_path}: {str(e)}") from e
    except TypeError as e:
        raise BlogGenerationError(f"JSON serialization error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error saving blog post to JSON: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Error saving blog post to JSON: {str(e)}") from e


def load_blog_post_from_json(file_path: str) -> BlogPost:
    """
    Load a blog post from a JSON file.

    Args:
        file_path: The path to load the blog post from.

    Returns:
        The loaded blog post.

    Raises:
        BlogGenerationError: If an error occurs during loading.
    """
    try:
        # Read from file
        with open(file_path, "r", encoding="utf-8") as f:
            blog_post_data = json.load(f)

        # Convert JSON data to BlogPost
        sections = []

        for section_data in blog_post_data["sections"]:
            subtopics = []

            for subtopic_data in section_data["subtopics"]:
                subtopic = SubTopic(
                    title=subtopic_data["title"], content=subtopic_data["content"]
                )

                subtopics.append(subtopic)

            section = Section(title=section_data["title"], subtopics=subtopics)

            sections.append(section)

        blog_post = BlogPost(
            title=blog_post_data["title"],
            description=blog_post_data["description"],
            sections=sections,
            tags=blog_post_data["tags"],
            date=blog_post_data["date"],
            image=blog_post_data["image"],
        )

        return blog_post
    except FileNotFoundError as e:
        raise BlogGenerationError(f"File not found: {file_path}") from e
    except PermissionError as e:
        raise BlogGenerationError(f"Permission denied reading {file_path}: {str(e)}") from e
    except json.JSONDecodeError as e:
        raise BlogGenerationError(f"Invalid JSON format in {file_path}: {str(e)}") from e
    except KeyError as e:
        raise BlogGenerationError(f"Missing required field in JSON: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading blog post from JSON: {str(e)}", exc_info=True)
        raise BlogGenerationError(f"Error loading blog post from JSON: {str(e)}") from e
