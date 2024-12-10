"""
Humanization functionality.
"""

from typing import Optional

from ..text_generation.core import GenerationOptions, LLMProvider, generate_text
from ..types.post_processing import HumanizationOptions


class HumanizationError(Exception):
    """Exception raised for errors in the humanization process."""

    pass


def humanize_content(
    content: str,
    options: Optional[HumanizationOptions] = None,
    provider: Optional[LLMProvider] = None,
    generation_options: Optional[GenerationOptions] = None,
) -> str:
    """
    Humanize content to make it sound more natural and less AI-generated.

    Args:
        content: The content to humanize.
        options: Options for humanization.
        provider: The LLM provider to use.
        generation_options: Options for text generation.

    Returns:
        The humanized content.

    Raises:
        HumanizationError: If an error occurs during humanization.
    """
    try:
        options = options or HumanizationOptions()

        # PROMPT DESIGN: This is the most critical post-processing step. The goal is
        # to transform text that "smells like AI" into text that reads like a real
        # person wrote it. We give the model a concrete checklist of AI tells to fix
        # and specific techniques for making prose feel human.
        prompt = f"""Rewrite this content so it reads like a skilled human writer wrote it.

CONTENT TO REWRITE:
{content}

YOUR GOAL: Make this indistinguishable from content written by a knowledgeable human.

VOICE SETTINGS:
- Tone: {options.tone}
- Formality: {options.formality}
- Personality: {options.personality}

SPECIFIC CHANGES TO MAKE:

1. FIX SENTENCE RHYTHM:
   AI writing uses monotonous sentence patterns. Break this up.
   Mix short sentences (5-8 words) with medium (12-18) and occasional long ones (20+).
   Start some sentences with "But", "And", "So", or "Still" -- real writers do this.

2. REMOVE AI TELLS:
   Find and replace these dead giveaways:
   - "It's important to note that..." -> just state the thing
   - "In today's [adjective] world..." -> cut entirely or replace with a specific reference
   - "Furthermore" / "Moreover" / "Additionally" -> use "Also", "Plus", "And", or just start a new thought
   - "Utilize" -> "use"
   - "Leverage" -> pick a specific verb (apply, use, build on, take advantage of)
   - "Robust" / "Seamless" / "Comprehensive" -> pick a concrete adjective
   - "Delve" / "Landscape" / "Navigate" -> use plain language
   - "In order to" -> "to"
   - Semicolons used every other sentence -> use periods or dashes instead (keep rare semicolons)

3. ADD HUMAN TEXTURE:
   - Use contractions: "it is" -> "it's", "do not" -> "don't", "you will" -> "you'll"
   - Add brief parenthetical asides where natural (like this one)
   - Use the occasional dash -- for emphasis or to insert a thought
   - Include a concrete example, analogy, or specific detail where the original is vague
   - Use "you" and "your" to speak directly to the reader

4. FIX TRANSITIONS:
   AI loves formal connectors. Replace with conversational ones:
   - "However" (overused) -> "But", "That said", "The flip side", or restructure
   - "Therefore" -> "So", "Which means", or drop it
   - "Consequently" -> "As a result" or restructure
   - "Nevertheless" -> "Still", "Even so"

5. PRESERVE MEANING:
   - Keep all factual information, data points, and key arguments intact.
   - Maintain the same organizational structure and flow.
   - Do NOT add new claims or information.
   - Do NOT remove important points.

Return ONLY the rewritten content. No labels, no commentary, no "Here's the rewritten version:"."""

        # Generate humanized content
        humanized_content = generate_text(prompt, provider, generation_options)

        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content: {str(e)}") from e


def humanize_with_style(
    content: str,
    writing_style: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> str:
    """
    Humanize content with a specific writing style.

    Args:
        content: The content to humanize.
        writing_style: The writing style to emulate (e.g., "Hemingway", "Academic", "Conversational").
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The humanized content.

    Raises:
        HumanizationError: If an error occurs during humanization.
    """
    try:
        # PROMPT DESIGN: Style-specific humanization. We ask the model to identify
        # concrete stylistic traits of the target style and apply them, rather than
        # just saying "write like X" which produces superficial mimicry.
        prompt = f"""Rewrite this content in the {writing_style} writing style.

CONTENT TO REWRITE:
{content}

YOUR TASK:
Rewrite so it authentically reflects the {writing_style} style. This means adopting
the characteristic sentence structures, vocabulary choices, pacing, and rhetorical
patterns associated with {writing_style} writing.

RULES:
- Preserve all factual information, data points, and key arguments.
- Maintain the same organizational structure.
- Apply the {writing_style} style CONSISTENTLY throughout -- not just in the first paragraph.
- Vary sentence length and structure (this is essential for any good writing).
- Use natural, conversational transitions -- avoid stiff connectors like "Furthermore"
  and "Moreover" unless they fit the target style.
- Remove AI-sounding phrases: "it's important to note", "in today's world",
  "delve", "landscape", "leverage", "robust", "seamless", "comprehensive."
- Use contractions where the target style would.

Return ONLY the rewritten content. No preamble, labels, or commentary."""

        # Generate humanized content
        humanized_content = generate_text(prompt, provider, options)

        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content with style: {str(e)}") from e


def humanize_for_audience(
    content: str,
    target_audience: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> str:
    """
    Humanize content for a specific target audience.

    Args:
        content: The content to humanize.
        target_audience: The target audience (e.g., "Technical professionals", "Beginners", "Teenagers").
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The humanized content.

    Raises:
        HumanizationError: If an error occurs during humanization.
    """
    try:
        # PROMPT DESIGN: Audience-targeted humanization. We push for concrete
        # audience-specific adaptations rather than generic "make it appropriate."
        prompt = f"""Rewrite this content for a specific audience: {target_audience}.

CONTENT TO REWRITE:
{content}

YOUR TASK:
Adapt the language, examples, and complexity so this content resonates with
{target_audience} while still sounding like a real human wrote it.

SPECIFIC ADAPTATIONS:
- Vocabulary: Use terms and jargon that {target_audience} actually use day-to-day.
  Drop jargon they wouldn't know; keep or add jargon they'd expect.
- Examples: Replace generic examples with ones from the world of {target_audience}.
  Use scenarios, tools, and references they'd recognize immediately.
- Complexity: Match the depth to what {target_audience} needs. Don't over-explain
  what they already know. Don't under-explain what's new to them.
- Tone: Write the way a trusted peer in {target_audience} would explain this --
  not like a teacher lecturing down, and not like a marketer selling up.

GENERAL RULES:
- Preserve all factual information and key arguments.
- Maintain the same organizational structure.
- Vary sentence length and structure.
- Use contractions and conversational transitions.
- Remove AI tells: "it's important to note", "in today's world", "delve",
  "landscape", "leverage", "robust", "seamless", "comprehensive."

Return ONLY the rewritten content. No preamble, labels, or commentary."""

        # Generate humanized content
        humanized_content = generate_text(prompt, provider, options)

        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content for audience: {str(e)}") from e


def add_personal_anecdotes(
    content: str,
    persona: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> str:
    """
    Add personal anecdotes to content to make it more human.

    Args:
        content: The content to add anecdotes to.
        persona: The persona to use for the anecdotes (e.g., "Experienced developer", "Marketing professional").
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The content with added anecdotes.

    Raises:
        HumanizationError: If an error occurs during anecdote addition.
    """
    try:
        # PROMPT DESIGN: Anecdote injection. We give specific guidance on what makes
        # an anecdote feel authentic vs. fabricated -- sensory details, specific
        # moments, and honest reactions rather than neat morals.
        prompt = f"""Add personal anecdotes to this content from the perspective of a {persona}.

CONTENT TO ENHANCE:
{content}

YOUR TASK:
Weave in 2-3 brief first-person anecdotes from a {persona}'s experience that
illustrate key points in the content.

WHAT MAKES A GOOD ANECDOTE:
- It describes a SPECIFIC moment, not a general pattern ("Last quarter, when we
  migrated to..." not "In my experience, migrations usually...")
- It includes one sensory or emotional detail ("I remember staring at the error
  log at 2am..." not "It was a challenging experience")
- It admits imperfection -- real stories include mistakes, surprises, and lessons
  learned the hard way
- It's SHORT -- 2-4 sentences max. Weave it into the existing flow, don't create
  a separate narrative block
- It transitions naturally: "I learned this firsthand when...", "This reminds me
  of a time when...", "We ran into exactly this problem..."

WHAT TO AVOID:
- Generic anecdotes that could apply to anyone ("In my years of experience...")
- Anecdotes that feel like humble-brags
- Long tangential stories that derail the article's flow
- Starting every anecdote the same way

RULES:
- Preserve all factual information and key arguments.
- Keep the same organizational structure.
- Use natural, varied sentence structures and contractions.
- Remove AI tells: "delve", "landscape", "leverage", "robust", "seamless."

Return ONLY the enhanced content. No preamble, labels, or commentary."""

        # Generate content with anecdotes
        anecdotal_content = generate_text(prompt, provider, options)

        return anecdotal_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error adding personal anecdotes: {str(e)}") from e


def add_humor(
    content: str,
    humor_style: str = "light",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
) -> str:
    """
    Add humor to content to make it more engaging and human.

    Args:
        content: The content to add humor to.
        humor_style: The style of humor to add (e.g., "light", "dry", "sarcastic").
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        The content with added humor.

    Raises:
        HumanizationError: If an error occurs during humor addition.
    """
    try:
        # PROMPT DESIGN: Humor injection. We emphasize subtlety and topic-relevance
        # over forced jokes. The humor should enhance, not distract.
        prompt = f"""Add {humor_style} humor to this content.

CONTENT TO ENHANCE:
{content}

HUMOR STYLE: {humor_style}

YOUR TASK:
Weave {humor_style} humor naturally into the existing content. The humor should
enhance the reading experience without undermining the information.

WHAT WORKS:
- Witty observations that show genuine understanding of the topic
- Unexpected comparisons or analogies that also clarify a point
- Self-aware asides about the topic's quirks (e.g., "Yes, another acronym. Tech
  loves those.")
- Brief, well-placed one-liners -- not extended comedy bits
- Humor that rewards the reader for paying attention

WHAT DOESN'T WORK:
- Forced puns that derail the paragraph
- "As they say..." followed by a cliche -- this is lazy comedy
- Humor that requires a disclaimer ("just kidding!")
- Jokes that mock the reader or the topic itself
- Comedy that breaks the informational flow

RULES:
- Add 2-3 humorous moments, spaced throughout (not clustered)
- Preserve all factual information and key arguments
- Keep the same organizational structure
- Humor must be appropriate for a professional audience
- Use contractions and varied sentence structures

Return ONLY the enhanced content. No preamble, labels, or commentary."""

        # Generate content with humor
        humorous_content = generate_text(prompt, provider, options)

        return humorous_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error adding humor: {str(e)}") from e
