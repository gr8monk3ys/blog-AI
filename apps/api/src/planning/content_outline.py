"""
Content outline generation functionality.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..research.web_researcher import ResearchError, conduct_web_research
from ..text_generation.core import GenerationOptions, LLMProvider, TextGenerationError, generate_text
from ..types.planning import ContentOutline, ContentTopic


class ContentOutlineError(Exception):
    """Exception raised for errors in the content outline generation process."""

    pass


def generate_content_outline(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> ContentOutline:
    """
    Generate a content outline for a specific title.

    Args:
        title: The title to generate an outline for.
        keywords: The keywords to include in the outline.
        num_sections: The number of sections to include in the outline.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated content outline.

    Raises:
        ContentOutlineError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: The outline determines the entire article's structure and
        # reading experience. We push for search-intent alignment, logical progression,
        # and headings that are specific enough to be useful on their own.
        prompt = f"""Create a blog post outline.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        prompt += f"""
Number of main sections: {num_sections}

OUTLINE RULES:
- Start with "# Introduction" and end with "# Conclusion".
- Between them, create exactly {num_sections} section headings.
- Each heading must be SPECIFIC and descriptive -- a reader should understand
  what that section covers just from the heading alone.
- BAD headings: "Understanding the Basics", "Key Considerations", "Best Practices"
  (too vague -- could apply to any article)
- GOOD headings: "Why React Re-Renders More Than You Think", "3 Caching Patterns
  That Cut Load Time in Half" (specific, promise clear value)
- Sections must follow a logical progression: context/problem first, then
  solutions/how-to, then advanced tips or forward-looking content.
- Do NOT use these words in headings: comprehensive, ultimate, leverage, delve,
  robust, landscape, seamless, unlock, harness, navigate, empower.
"""

        if keywords:
            prompt += """- Work keywords into headings naturally where they fit -- but NEVER
  force a keyword into a heading where it reads awkwardly.
"""

        prompt += """
OUTPUT FORMAT (follow exactly -- one heading per line, no bullet points):

# Introduction

# [Section 1 Heading]

# [Section 2 Heading]

# [Section 3 Heading]

# [Section 4 Heading]

# [Section 5 Heading]

# Conclusion

Return ONLY the outline in the format above. No descriptions, no bullet points, no commentary."""

        # Generate outline
        outline_text = generate_text(prompt, provider, options)

        # Parse the outline
        sections = []

        lines = outline_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Extract section heading
                section = line[1:].strip()
                sections.append(section)

        return ContentOutline(title=title, sections=sections, keywords=keywords or [])
    except TextGenerationError as e:
        raise ContentOutlineError(f"Failed to generate content outline: {str(e)}") from e
    except ValueError as e:
        raise ContentOutlineError(f"Invalid parameters for content outline: {str(e)}") from e
    except AttributeError as e:
        raise ContentOutlineError(f"Invalid data structure during outline generation: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to generate content outline")
        raise ContentOutlineError(f"Unexpected error generating content outline: {str(e)}") from e


def generate_detailed_content_outline(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> ContentOutline:
    """
    Generate a detailed content outline for a specific title.

    Args:
        title: The title to generate an outline for.
        keywords: The keywords to include in the outline.
        num_sections: The number of sections to include in the outline.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated content outline.

    Raises:
        ContentOutlineError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: Detailed outline with key points per section. These bullet
        # points serve as a content brief for each section generator, so they need to
        # be specific and actionable, not generic placeholders.
        prompt = f"""Create a detailed blog post outline with key points for each section.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        prompt += f"""
Number of main sections: {num_sections}

OUTLINE RULES:
- Start with "# Introduction" and end with "# Conclusion".
- Create exactly {num_sections} section headings between them.
- Under each heading, list 3-5 bullet points describing SPECIFIC content to cover.
- Bullet points should be concrete and actionable, not vague.
  BAD: "- Discuss the benefits" (vague)
  GOOD: "- Compare response times: cached vs uncached queries (include benchmarks)" (specific)
- Headings must be specific and descriptive -- avoid generic titles.
- Follow a logical progression: problem/context, then solutions, then advanced/future.
- Do NOT use these words in headings: comprehensive, ultimate, leverage, delve,
  robust, landscape, seamless, unlock, harness.
"""

        if keywords:
            prompt += "- Weave keywords into headings and bullet points naturally -- never force them.\n"

        prompt += """
OUTPUT FORMAT:

# Introduction
- [Specific point about what the hook should cover]
- [Key context to establish]
- [What the reader will learn]

# [Section 1 Heading]
- [Specific point 1]
- [Specific point 2]
- [Specific point 3]

# [Section 2 Heading]
- [Specific point 1]
- [Specific point 2]
- [Specific point 3]
- [Specific point 4]

(continue for all sections)

# Conclusion
- [Key synthesis point]
- [Actionable takeaway]

Return ONLY the outline. No extra commentary."""

        # Generate outline
        outline_text = generate_text(prompt, provider, options)

        # Parse the outline
        sections = []

        lines = outline_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Extract section heading
                section = line[1:].strip()
                sections.append(section)

        return ContentOutline(title=title, sections=sections, keywords=keywords or [])
    except TextGenerationError as e:
        raise ContentOutlineError(f"Failed to generate detailed content outline: {str(e)}") from e
    except ValueError as e:
        raise ContentOutlineError(f"Invalid parameters for detailed content outline: {str(e)}") from e
    except AttributeError as e:
        raise ContentOutlineError(f"Invalid data structure during detailed outline generation: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to generate detailed content outline")
        raise ContentOutlineError(f"Unexpected error generating detailed content outline: {str(e)}") from e


def generate_content_outline_with_research(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> ContentOutline:
    """
    Generate a content outline for a specific title using web research.

    Args:
        title: The title to generate an outline for.
        keywords: The keywords to include in the outline.
        num_sections: The number of sections to include in the outline.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated content outline.

    Raises:
        ContentOutlineError: If an error occurs during generation.
    """
    try:
        # Conduct web research
        research_keywords = [title]
        if keywords:
            research_keywords.extend(keywords)

        research_results = conduct_web_research(research_keywords)

        # PROMPT DESIGN: Research-informed outline. We instruct the model to identify
        # gaps in existing coverage and structure the outline to add unique value.
        prompt = f"""Create a research-informed blog post outline.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        prompt += f"""
RESEARCH FINDINGS (use these to inform structure and identify gaps):
{str(research_results)[:2000]}

Number of main sections: {num_sections}

OUTLINE RULES:
- Start with "# Introduction" and end with "# Conclusion".
- Create exactly {num_sections} section headings between them.
- Use the research to identify what EXISTING content covers -- then structure
  your outline to add unique value. Cover angles others miss.
- Headings must be specific and descriptive (not "Understanding X" or "Key Benefits").
- Follow a logical progression informed by the research: what does the reader
  need to understand first before they can grasp later sections?
- Do NOT use these words in headings: comprehensive, ultimate, leverage, delve,
  robust, landscape, seamless, unlock, harness.
"""

        if keywords:
            prompt += "- Weave keywords into headings naturally -- never force them.\n"

        prompt += """
OUTPUT FORMAT (follow exactly):

# Introduction

# [Section 1 Heading]

# [Section 2 Heading]

# [Section 3 Heading]

# [Section 4 Heading]

# [Section 5 Heading]

# Conclusion

Return ONLY the outline. No bullet points, no descriptions, no commentary."""

        # Generate outline
        outline_text = generate_text(prompt, provider, options)

        # Parse the outline
        sections = []

        lines = outline_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Extract section heading
                section = line[1:].strip()
                sections.append(section)

        return ContentOutline(title=title, sections=sections, keywords=keywords or [])
    except TextGenerationError as e:
        raise ContentOutlineError(f"Failed to generate content outline with research: {str(e)}") from e
    except ResearchError as e:
        raise ContentOutlineError(f"Research failed during outline generation: {str(e)}") from e
    except ValueError as e:
        raise ContentOutlineError(f"Invalid parameters for content outline with research: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to generate content outline with research")
        raise ContentOutlineError(f"Unexpected error generating content outline with research: {str(e)}") from e


def generate_content_outline_from_topic(
    topic: ContentTopic,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> ContentOutline:
    """
    Generate a content outline from a content topic.

    Args:
        topic: The content topic to generate an outline from.
        num_sections: The number of sections to include in the outline.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated content outline.

    Raises:
        ContentOutlineError: If an error occurs during generation.
    """
    try:
        # PROMPT DESIGN: Topic-based outline. The topic object provides richer context
        # (description + keywords) so we use it to generate more targeted headings.
        prompt = f"""Create a blog post outline from a content topic brief.

Title: {topic.title}
Target keywords: {', '.join(topic.keywords)}
"""

        if topic.description:
            prompt += f"Topic brief: {topic.description}\n"

        prompt += f"""
Number of main sections: {num_sections}

OUTLINE RULES:
- Start with "# Introduction" and end with "# Conclusion".
- Create exactly {num_sections} section headings between them.
- Align headings with the topic brief and keywords -- each section should
  advance the reader's understanding in a clear, logical way.
- Headings must be specific and descriptive (avoid generic titles like
  "Understanding X" or "Key Considerations").
- Do NOT use these words in headings: comprehensive, ultimate, leverage, delve,
  robust, landscape, seamless, unlock, harness.
- Weave keywords into headings naturally -- never force them.

OUTPUT FORMAT (follow exactly):

# Introduction

# [Section 1 Heading]

# [Section 2 Heading]

# [Section 3 Heading]

# [Section 4 Heading]

# [Section 5 Heading]

# Conclusion

Return ONLY the outline. No bullet points, descriptions, or commentary."""

        # Generate outline
        outline_text = generate_text(prompt, provider, options)

        # Parse the outline
        sections = []

        lines = outline_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Extract section heading
                section = line[1:].strip()
                sections.append(section)

        return ContentOutline(
            title=topic.title, sections=sections, keywords=topic.keywords
        )
    except TextGenerationError as e:
        raise ContentOutlineError(f"Failed to generate content outline from topic: {str(e)}") from e
    except ValueError as e:
        raise ContentOutlineError(f"Invalid topic parameters: {str(e)}") from e
    except AttributeError as e:
        raise ContentOutlineError(f"Invalid topic data structure: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to generate content outline from topic")
        raise ContentOutlineError(f"Unexpected error generating content outline from topic: {str(e)}") from e


def save_content_outline_to_json(outline: ContentOutline, file_path: str) -> None:
    """
    Save a content outline to a JSON file.

    Args:
        outline: The content outline to save.
        file_path: The path to save the outline to.

    Raises:
        ContentOutlineError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Convert outline to JSON-serializable format
        outline_data = {
            "title": outline.title,
            "sections": outline.sections,
            "keywords": outline.keywords,
        }

        # Write outline to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, indent=2)
    except PermissionError as e:
        raise ContentOutlineError(f"Permission denied writing outline to {file_path}: {str(e)}") from e
    except OSError as e:
        raise ContentOutlineError(f"File system error saving outline: {str(e)}") from e
    except TypeError as e:
        raise ContentOutlineError(f"JSON serialization error: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to save content outline to JSON")
        raise ContentOutlineError(f"Unexpected error saving content outline to JSON: {str(e)}") from e


def load_content_outline_from_json(file_path: str) -> ContentOutline:
    """
    Load a content outline from a JSON file.

    Args:
        file_path: The path to load the outline from.

    Returns:
        The loaded content outline.

    Raises:
        ContentOutlineError: If an error occurs during loading.
    """
    try:
        # Read outline from JSON
        with open(file_path, "r", encoding="utf-8") as f:
            outline_data = json.load(f)

        # Convert JSON data to ContentOutline
        return ContentOutline(
            title=outline_data["title"],
            sections=outline_data["sections"],
            keywords=outline_data["keywords"],
        )
    except FileNotFoundError as e:
        raise ContentOutlineError(f"Outline file not found: {file_path}") from e
    except PermissionError as e:
        raise ContentOutlineError(f"Permission denied reading outline from {file_path}: {str(e)}") from e
    except json.JSONDecodeError as e:
        raise ContentOutlineError(f"Invalid JSON format in outline file: {str(e)}") from e
    except KeyError as e:
        raise ContentOutlineError(f"Missing required field in outline JSON: {str(e)}") from e
    except Exception as e:
        logger.exception("Failed to load content outline from JSON")
        raise ContentOutlineError(f"Unexpected error loading content outline from JSON: {str(e)}") from e
