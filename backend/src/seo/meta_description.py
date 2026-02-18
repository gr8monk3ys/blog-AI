"""
Meta description generation functionality.
"""

from typing import List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.seo import MetaDescription


class MetaDescriptionError(Exception):
    """Exception raised for errors in the meta description generation process."""

    pass


def generate_meta_description(
    title: str,
    keywords: List[str],
    content: Optional[str] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> MetaDescription:
    """
    Generate a meta description for a blog post or webpage.

    Args:
        title: The title of the blog post or webpage.
        keywords: The target keywords.
        content: The content of the blog post or webpage.
        tone: The desired tone for the meta description.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated meta description.

    Raises:
        MetaDescriptionError: If an error occurs during meta description generation.
    """
    try:
        # PROMPT DESIGN: Meta descriptions are ad copy for search results. We optimize
        # for click-through rate: front-load the value prop, include a keyword, and
        # create urgency or curiosity -- all within the strict character limit.
        prompt = f"""Write a meta description for a blog post.

Title: {title}
Primary keywords: {', '.join(keywords)}
Tone: {tone}

STRICT RULES:
- EXACTLY 150-160 characters (this is critical -- count carefully).
- Front-load the most compelling benefit or hook in the first 70 characters
  (this is all that shows on mobile).
- Include at least one primary keyword naturally within the first half.
- Create a reason to click: promise a specific outcome, ask a question, or
  hint at something surprising.
- Do NOT use generic filler like "Learn everything you need to know about..."
  or "Discover the ultimate guide to..."
- Do NOT use quotation marks, special characters, or HTML entities.
- Do NOT use the words: comprehensive, ultimate, robust, leverage, delve.
- Write in active voice. Use "you" to address the reader directly.

GOOD EXAMPLES:
- "Python decorators cut boilerplate code by 40%. Here's how to use them in your next project -- with patterns most tutorials skip."
- "Your CI pipeline shouldn't take 45 minutes. These 7 caching strategies brought ours down to under 5."

BAD EXAMPLES (do NOT write like these):
- "In this comprehensive guide, we delve into the world of Python decorators and explore their many uses."
- "Discover everything you need to know about CI/CD pipelines in this ultimate guide."

Return ONLY the meta description text. No quotes, no labels, nothing else."""

        if content:
            content_summary = content[:500] + "..." if len(content) > 500 else content
            prompt += f"\n\nContent summary (use for accuracy):\n{content_summary}"

        # Generate meta description
        description_text = generate_text(prompt, provider, options)

        # Clean up the description
        description_text = description_text.strip()

        # Ensure the description is not too long
        if len(description_text) > 160:
            description_text = description_text[:157] + "..."

        return MetaDescription(content=description_text)
    except Exception as e:
        raise MetaDescriptionError(f"Error generating meta description: {str(e)}")


def generate_multiple_meta_descriptions(
    title: str,
    keywords: List[str],
    content: Optional[str] = None,
    tone: str = "informative",
    count: int = 3,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> List[MetaDescription]:
    """
    Generate multiple meta descriptions for a blog post or webpage.

    Args:
        title: The title of the blog post or webpage.
        keywords: The target keywords.
        content: The content of the blog post or webpage.
        tone: The desired tone for the meta description.
        count: The number of meta descriptions to generate.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated meta descriptions.

    Raises:
        MetaDescriptionError: If an error occurs during meta description generation.
    """
    try:
        # PROMPT DESIGN: Multiple meta description variants for A/B selection.
        # Each should take a different angle to give meaningful choice.
        prompt = f"""Write {count} different meta descriptions for a blog post.

Title: {title}
Primary keywords: {', '.join(keywords)}
Tone: {tone}

STRICT RULES FOR EACH:
- EXACTLY 150-160 characters (count carefully).
- Include at least one primary keyword naturally.
- Front-load the most compelling element in the first 70 characters.
- Each description must use a DIFFERENT angle:
  1. Benefit-focused (what the reader gains)
  2. Curiosity/question-based (provoke interest)
  3. Data/proof-based (lead with a number or result)
  (Adapt as needed for {count} variants)
- Do NOT use quotation marks, special characters, or HTML entities.
- Do NOT use generic phrases like "Learn everything...", "Discover the ultimate..."
- Do NOT use: comprehensive, ultimate, robust, leverage, delve, seamless.
- Write in active voice using "you" to address the reader.

Return as a numbered list. One description per line. No extra commentary."""

        if content:
            content_summary = content[:500] + "..." if len(content) > 500 else content
            prompt += f"\n\nContent summary (use for accuracy):\n{content_summary}"

        # Generate meta descriptions
        descriptions_text = generate_text(prompt, provider, options)

        # Parse the descriptions
        descriptions = []
        lines = descriptions_text.strip().split("\n")

        for line in lines:
            # Remove numbering and whitespace
            line = line.strip()
            if not line:
                continue

            # Remove numbering (e.g., "1. ", "2. ", etc.)
            if (
                line[0].isdigit()
                and len(line) > 2
                and line[1] == "."
                and line[2] == " "
            ):
                line = line[3:]

            # Clean up the description
            description_text = line.strip()

            # Ensure the description is not too long
            if len(description_text) > 160:
                description_text = description_text[:157] + "..."

            descriptions.append(MetaDescription(content=description_text))

        # Ensure we have the requested number of descriptions
        while len(descriptions) < count:
            descriptions.append(
                generate_meta_description(
                    title, keywords, content, tone, provider, options
                )
            )

        return descriptions[:count]
    except Exception as e:
        raise MetaDescriptionError(f"Error generating meta descriptions: {str(e)}")
