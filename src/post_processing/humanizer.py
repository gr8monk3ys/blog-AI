"""
Humanization functionality.
"""
from typing import Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.post_processing import HumanizationOptions


class HumanizationError(Exception):
    """Exception raised for errors in the humanization process."""
    pass


def humanize_content(
    content: str,
    options: Optional[HumanizationOptions] = None,
    provider: Optional[LLMProvider] = None,
    generation_options: Optional[GenerationOptions] = None
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
        
        # Create prompt for humanization
        prompt = f"""
        Rewrite the following content to make it sound more natural and human-written:
        
        {content}
        
        Requirements:
        - Maintain the same meaning and information.
        - Use a {options.tone} tone.
        - Use a {options.formality} level of formality.
        - Incorporate a {options.personality} personality.
        - Vary sentence structure and length.
        - Use natural transitions between ideas.
        - Avoid repetitive phrases and sentence structures.
        - Include occasional colloquialisms or idioms where appropriate.
        - Maintain the original organization and flow of ideas.
        
        Return only the rewritten content, nothing else.
        """
        
        # Generate humanized content
        humanized_content = generate_text(prompt, provider, generation_options)
        
        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content: {str(e)}")


def humanize_with_style(
    content: str,
    writing_style: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for humanization with style
        prompt = f"""
        Rewrite the following content in the style of {writing_style}, while making it sound more natural and human-written:
        
        {content}
        
        Requirements:
        - Maintain the same meaning and information.
        - Emulate the {writing_style} writing style.
        - Vary sentence structure and length.
        - Use natural transitions between ideas.
        - Avoid repetitive phrases and sentence structures.
        - Include stylistic elements characteristic of {writing_style}.
        - Maintain the original organization and flow of ideas.
        
        Return only the rewritten content, nothing else.
        """
        
        # Generate humanized content
        humanized_content = generate_text(prompt, provider, options)
        
        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content with style: {str(e)}")


def humanize_for_audience(
    content: str,
    target_audience: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for humanization for audience
        prompt = f"""
        Rewrite the following content to make it more engaging and appropriate for {target_audience}, while making it sound more natural and human-written:
        
        {content}
        
        Requirements:
        - Maintain the same meaning and information.
        - Adapt the language, tone, and complexity for {target_audience}.
        - Use vocabulary and examples that resonate with {target_audience}.
        - Vary sentence structure and length.
        - Use natural transitions between ideas.
        - Avoid repetitive phrases and sentence structures.
        - Include references or analogies that would be familiar to {target_audience}.
        - Maintain the original organization and flow of ideas.
        
        Return only the rewritten content, nothing else.
        """
        
        # Generate humanized content
        humanized_content = generate_text(prompt, provider, options)
        
        return humanized_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error humanizing content for audience: {str(e)}")


def add_personal_anecdotes(
    content: str,
    persona: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for adding anecdotes
        prompt = f"""
        Rewrite the following content to include personal anecdotes from the perspective of a {persona}:
        
        {content}
        
        Requirements:
        - Maintain the same meaning and information.
        - Add 2-3 brief personal anecdotes or experiences that illustrate key points.
        - Write the anecdotes from a first-person perspective.
        - Make the anecdotes sound authentic and relatable.
        - Ensure the anecdotes flow naturally with the surrounding content.
        - Vary sentence structure and length.
        - Use natural transitions between ideas.
        - Maintain the original organization and flow of ideas.
        
        Return only the rewritten content, nothing else.
        """
        
        # Generate content with anecdotes
        anecdotal_content = generate_text(prompt, provider, options)
        
        return anecdotal_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error adding personal anecdotes: {str(e)}")


def add_humor(
    content: str,
    humor_style: str = "light",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for adding humor
        prompt = f"""
        Rewrite the following content to include {humor_style} humor:
        
        {content}
        
        Requirements:
        - Maintain the same meaning and information.
        - Add {humor_style} humor throughout the content.
        - Include 2-3 jokes, puns, or humorous observations that relate to the topic.
        - Ensure the humor is appropriate for a general audience.
        - Make the humor flow naturally with the surrounding content.
        - Vary sentence structure and length.
        - Use natural transitions between ideas.
        - Maintain the original organization and flow of ideas.
        
        Return only the rewritten content, nothing else.
        """
        
        # Generate content with humor
        humorous_content = generate_text(prompt, provider, options)
        
        return humorous_content.strip()
    except Exception as e:
        raise HumanizationError(f"Error adding humor: {str(e)}")
