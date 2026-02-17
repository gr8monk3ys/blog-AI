"""
Introduction generation functionality.
"""

from typing import List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.blog_sections import Introduction


class IntroductionGenerationError(Exception):
    """Exception raised for errors in the introduction generation process."""

    pass


def generate_introduction(
    title: str,
    outline: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    target_audience: Optional[str] = None,
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Introduction:
    """
    Generate an introduction for a blog post.

    Args:
        title: The title of the blog post.
        outline: The outline of the blog post.
        keywords: The target keywords.
        tone: The desired tone for the introduction.
        target_audience: The target audience for the blog post.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction.

    Raises:
        IntroductionGenerationError: If an error occurs during introduction generation.
    """
    try:
        # PROMPT DESIGN: The introduction is the most critical section -- it determines
        # whether a reader stays or bounces. We front-load a concrete hook requirement,
        # ban common AI-slop openers, and demand specificity over generalities.
        prompt = f"""Write the introduction for a blog post.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if outline:
            prompt += f"Article outline (for context on scope):\n{outline}\n"

        if target_audience:
            prompt += f"Target audience: {target_audience}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with ONE of these proven hook types (pick the best fit):
- A surprising statistic or data point relevant to the topic
- A brief, specific anecdote or scenario the reader can relate to
- A provocative question that challenges a common assumption
- A concrete before/after contrast that shows stakes

Do NOT open with any of these (they are generic AI filler):
- "In today's fast-paced world..."
- "In the ever-evolving landscape of..."
- "Have you ever wondered..."
- "In today's digital age..."
- Any sentence starting with "In today's..."

Paragraph 2 -- THE PROBLEM/CONTEXT:
Ground the reader in WHY this topic matters right now. Be specific.
Reference a real trend, pain point, or shift -- not vague generalizations.

Paragraph 3 -- THE PROMISE:
Tell the reader exactly what they'll walk away with after reading.
Be concrete: "You'll learn X, understand Y, and be able to do Z."
Do NOT say "this comprehensive guide will delve into..."

STYLE RULES:
- Write like a knowledgeable friend, not a textbook or a press release
- Vary sentence length: mix short punchy sentences with longer explanatory ones
- Use contractions naturally (you'll, it's, don't, we're)
- Weave in keywords where they fit naturally -- never force them
- Every sentence must earn its place. Cut filler ruthlessly.
- Do NOT use these overused words: delve, landscape, leverage, robust, seamless, utilize, aforementioned, comprehensive, multifaceted
- Do NOT use the phrase "it's important to note that" or "it's worth mentioning that"

Return ONLY the introduction paragraphs. No headings, no labels, no meta-commentary."""

        # Generate introduction
        introduction_text = generate_text(prompt, provider, options)

        # Clean up the introduction
        introduction_text = introduction_text.strip()

        # Extract hook and thesis
        hook, thesis = extract_hook_and_thesis(introduction_text, provider, options)

        return Introduction(content=introduction_text, hook=hook, thesis=thesis)
    except Exception as e:
        raise IntroductionGenerationError(f"Error generating introduction: {str(e)}")


def extract_hook_and_thesis(
    introduction: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> tuple:
    """
    Extract the hook and thesis from an introduction.

    Args:
        introduction: The introduction text.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A tuple containing the hook and thesis.

    Raises:
        IntroductionGenerationError: If an error occurs during extraction.
    """
    try:
        # Create prompt for extraction
        prompt = f"""
        Analyze the following blog post introduction and extract:
        1. The hook (the attention-grabbing first sentence or statement)
        2. The thesis (the main point or purpose of the blog post)
        
        Introduction:
        {introduction}
        
        Return your analysis in the following format:
        
        Hook: [The hook]
        Thesis: [The thesis]
        
        Be concise and extract only the exact text from the introduction.
        """

        # Generate extraction
        extraction = generate_text(prompt, provider, options)

        # Parse the extraction
        hook = ""
        thesis = ""

        lines = extraction.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Hook:"):
                hook = line[5:].strip()
            elif line.startswith("Thesis:"):
                thesis = line[7:].strip()

        return hook, thesis
    except Exception as e:
        raise IntroductionGenerationError(f"Error extracting hook and thesis: {str(e)}")


def generate_introduction_with_research(
    title: str,
    research_results: dict,
    outline: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    target_audience: Optional[str] = None,
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Introduction:
    """
    Generate an introduction for a blog post using research results.

    Args:
        title: The title of the blog post.
        research_results: The research results to use for the introduction.
        outline: The outline of the blog post.
        keywords: The target keywords.
        tone: The desired tone for the introduction.
        target_audience: The target audience for the blog post.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated introduction.

    Raises:
        IntroductionGenerationError: If an error occurs during introduction generation.
    """
    try:
        # PROMPT DESIGN: Research-backed introduction. We instruct the model to lead
        # with a concrete data point from the research and weave citations naturally.
        prompt = f"""Write the introduction for a research-backed blog post.

Title: {title}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if outline:
            prompt += f"Article outline (for context on scope):\n{outline}\n"

        if target_audience:
            prompt += f"Target audience: {target_audience}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

RESEARCH CONTEXT (use specific findings from this):
{str(research_results)[:1000]}

STRUCTURE (3-4 paragraphs):

Paragraph 1 -- THE HOOK:
Open with a specific finding, statistic, or insight from the research above.
Ground it in concrete numbers or real examples -- not vague claims.
Do NOT open with "In today's...", "In the ever-evolving...", or any generic opener.

Paragraph 2 -- THE PROBLEM/CONTEXT:
Use research findings to establish WHY this topic matters right now.
Reference specific trends, data, or expert perspectives from the sources.

Paragraph 3 -- THE PROMISE:
Tell the reader exactly what they'll learn. Be specific and actionable.
Connect it back to the research -- "Based on [finding], we'll show you how to..."

STYLE RULES:
- Write like a knowledgeable friend, not a textbook or press release
- Vary sentence length: mix short punchy sentences with longer ones
- Use contractions naturally (you'll, it's, don't, we're)
- Weave keywords in where they fit -- never force them
- Every sentence must earn its place. Cut filler ruthlessly.
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, aforementioned, comprehensive, multifaceted
- BANNED phrases: "it's important to note that", "it's worth mentioning that", "in conclusion"

Return ONLY the introduction paragraphs. No headings, labels, or meta-commentary."""

        # Generate introduction
        introduction_text = generate_text(prompt, provider, options)

        # Clean up the introduction
        introduction_text = introduction_text.strip()

        # Extract hook and thesis
        hook, thesis = extract_hook_and_thesis(introduction_text, provider, options)

        return Introduction(content=introduction_text, hook=hook, thesis=thesis)
    except Exception as e:
        raise IntroductionGenerationError(
            f"Error generating introduction with research: {str(e)}"
        )
