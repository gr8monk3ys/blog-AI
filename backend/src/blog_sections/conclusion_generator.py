"""
Conclusion generation functionality.
"""

from typing import List, Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.blog_sections import Conclusion


class ConclusionGenerationError(Exception):
    """Exception raised for errors in the conclusion generation process."""

    pass


def generate_conclusion(
    title: str,
    content: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    include_call_to_action: bool = True,
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Conclusion:
    """
    Generate a conclusion for a blog post.

    Args:
        title: The title of the blog post.
        content: The content of the blog post.
        keywords: The target keywords.
        tone: The desired tone for the conclusion.
        include_call_to_action: Whether to include a call to action.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated conclusion.

    Raises:
        ConclusionGenerationError: If an error occurs during conclusion generation.
    """
    try:
        # PROMPT DESIGN: Conclusions are where most AI content falls flat -- they just
        # restate the intro. We push for a "so what?" synthesis and a forward-looking
        # final thought rather than mechanical summarization.
        prompt = f"""Write the conclusion for a blog post.

Title: {title}

Content covered in this post:
{content[:1000]}
"""

        if keywords:
            prompt += f"Target keywords: {', '.join(keywords)}\n"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""Tone: {tone}

STRUCTURE (2-3 paragraphs):

Paragraph 1 -- THE SYNTHESIS (not a summary):
Do NOT start with "In conclusion," "To sum up," "In summary," or "As we've seen."
Instead, connect the dots between the key ideas in the article. What's the bigger
picture? What pattern or insight emerges when you put all the pieces together?
Give the reader a fresh "aha" -- not a recap they already read.

Paragraph 2 -- THE FORWARD LOOK:
What should the reader do NEXT? Be specific and actionable.
"""

        if include_call_to_action:
            prompt += """Give one clear, concrete next step the reader can take today.
Frame it as an invitation, not a sales pitch. Make it feel natural.
"""

        prompt += """
Final sentence: End with something memorable -- a thought-provoking question,
a bold statement, or a vivid image that sticks with the reader.

STYLE RULES:
- Do NOT mechanically restate every point from the article
- Write with conviction -- this is your parting thought, make it count
- Use contractions naturally (you'll, it's, don't)
- Vary sentence length for rhythm
- BANNED openers: "In conclusion", "To sum up", "In summary", "As we've seen", "As we've discussed"
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, aforementioned, multifaceted
- BANNED phrases: "it's important to note that", "it's worth mentioning that"
- Include keywords naturally -- do not force them

Return ONLY the conclusion paragraphs. No headings, labels, or meta-commentary."""

        # Generate conclusion
        conclusion_text = generate_text(prompt, provider, options)

        # Clean up the conclusion
        conclusion_text = conclusion_text.strip()

        # Extract summary and call to action
        summary, call_to_action = extract_summary_and_cta(
            conclusion_text, provider, options
        )

        return Conclusion(
            content=conclusion_text, summary=summary, call_to_action=call_to_action
        )
    except Exception as e:
        raise ConclusionGenerationError(f"Error generating conclusion: {str(e)}")


def extract_summary_and_cta(
    conclusion: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> tuple:
    """
    Extract the summary and call to action from a conclusion.

    Args:
        conclusion: The conclusion text.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A tuple containing the summary and call to action.

    Raises:
        ConclusionGenerationError: If an error occurs during extraction.
    """
    try:
        # Create prompt for extraction
        prompt = f"""
        Analyze the following blog post conclusion and extract:
        1. The summary (the recap of key points from the blog post)
        2. The call to action (the specific action the reader is encouraged to take)
        
        Conclusion:
        {conclusion}
        
        Return your analysis in the following format:
        
        Summary: [The summary]
        Call to Action: [The call to action]
        
        Be concise and extract only the exact text from the conclusion. If there is no clear call to action, return "None" for that field.
        """

        # Generate extraction
        extraction = generate_text(prompt, provider, options)

        # Parse the extraction
        summary = ""
        call_to_action = None

        lines = extraction.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Summary:"):
                summary = line[8:].strip()
            elif line.startswith("Call to Action:"):
                cta = line[15:].strip()
                if cta.lower() != "none":
                    call_to_action = cta

        return summary, call_to_action
    except Exception as e:
        raise ConclusionGenerationError(
            f"Error extracting summary and call to action: {str(e)}"
        )


def generate_conclusion_with_key_points(
    title: str,
    key_points: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    include_call_to_action: bool = True,
    brand_voice: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> Conclusion:
    """
    Generate a conclusion for a blog post using key points.

    Args:
        title: The title of the blog post.
        key_points: The key points from the blog post.
        keywords: The target keywords.
        tone: The desired tone for the conclusion.
        include_call_to_action: Whether to include a call to action.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The generated conclusion.

    Raises:
        ConclusionGenerationError: If an error occurs during conclusion generation.
    """
    try:
        # PROMPT DESIGN: Key-points conclusion variant. Synthesize the points into
        # an insight rather than just listing them back.
        prompt = f"""Write the conclusion for a blog post.

Title: {title}

Key points covered in this post:
"""

        for i, point in enumerate(key_points):
            prompt += f"- {point}\n"

        if keywords:
            prompt += f"\nTarget keywords: {', '.join(keywords)}"

        if brand_voice:
            prompt += f"\nBRAND VOICE (match this voice exactly):\n{brand_voice}\n"

        prompt += f"""
Tone: {tone}

STRUCTURE (2-3 paragraphs):

Paragraph 1 -- THE SYNTHESIS:
Do NOT start with "In conclusion" or mechanically restate each point.
Instead, weave the key points together into a cohesive insight. What's the
bigger takeaway when you connect these ideas? Give the reader a fresh perspective.

Paragraph 2 -- WHAT NOW:
Provide a specific, actionable next step the reader can take.
"""

        if include_call_to_action:
            prompt += """Frame the call to action as a natural invitation, not a hard sell.
Be concrete: tell them exactly what to do, not just "take action."
"""

        prompt += """
End with a memorable final sentence -- a thought-provoking question, bold claim,
or vivid image that stays with the reader.

STYLE RULES:
- BANNED openers: "In conclusion", "To sum up", "In summary", "As we've seen"
- BANNED words: delve, landscape, leverage, robust, seamless, utilize, aforementioned
- Use contractions naturally and vary sentence length
- Include keywords naturally -- never force them

Return ONLY the conclusion paragraphs. No headings, labels, or meta-commentary."""

        # Generate conclusion
        conclusion_text = generate_text(prompt, provider, options)

        # Clean up the conclusion
        conclusion_text = conclusion_text.strip()

        # Extract summary and call to action
        summary, call_to_action = extract_summary_and_cta(
            conclusion_text, provider, options
        )

        return Conclusion(
            content=conclusion_text, summary=summary, call_to_action=call_to_action
        )
    except Exception as e:
        raise ConclusionGenerationError(
            f"Error generating conclusion with key points: {str(e)}"
        )
