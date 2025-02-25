"""
Conclusion generation functionality.
"""
from typing import List, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for conclusion generation
        prompt = f"""
        Generate a compelling conclusion for a blog post with the following details:
        
        Title: {title}
        
        Content Summary:
        {content[:1000]}...
        
        """
        
        if keywords:
            prompt += f"Keywords: {', '.join(keywords)}\n"
        
        prompt += f"""
        Tone: {tone}
        
        Requirements:
        - The conclusion should be 2-3 paragraphs.
        - Summarize the key points from the blog post.
        - Reinforce the main message or thesis.
        - Include at least one of the main keywords naturally.
        - Use a {tone} tone throughout.
        """
        
        if include_call_to_action:
            prompt += """
            - Include a clear and relevant call to action in the final paragraph.
            """
        
        prompt += """
        Return only the conclusion, nothing else.
        """
        
        # Generate conclusion
        conclusion_text = generate_text(prompt, provider, options)
        
        # Clean up the conclusion
        conclusion_text = conclusion_text.strip()
        
        # Extract summary and call to action
        summary, call_to_action = extract_summary_and_cta(conclusion_text, provider, options)
        
        return Conclusion(content=conclusion_text, summary=summary, call_to_action=call_to_action)
    except Exception as e:
        raise ConclusionGenerationError(f"Error generating conclusion: {str(e)}")


def extract_summary_and_cta(
    conclusion: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        raise ConclusionGenerationError(f"Error extracting summary and call to action: {str(e)}")


def generate_conclusion_with_key_points(
    title: str,
    key_points: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    include_call_to_action: bool = True,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for conclusion generation
        prompt = f"""
        Generate a compelling conclusion for a blog post with the following details:
        
        Title: {title}
        
        Key Points:
        """
        
        for i, point in enumerate(key_points):
            prompt += f"{i+1}. {point}\n"
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += f"""
        
        Tone: {tone}
        
        Requirements:
        - The conclusion should be 2-3 paragraphs.
        - Summarize the key points provided.
        - Reinforce the main message or thesis.
        - Include at least one of the main keywords naturally.
        - Use a {tone} tone throughout.
        """
        
        if include_call_to_action:
            prompt += """
            - Include a clear and relevant call to action in the final paragraph.
            """
        
        prompt += """
        Return only the conclusion, nothing else.
        """
        
        # Generate conclusion
        conclusion_text = generate_text(prompt, provider, options)
        
        # Clean up the conclusion
        conclusion_text = conclusion_text.strip()
        
        # Extract summary and call to action
        summary, call_to_action = extract_summary_and_cta(conclusion_text, provider, options)
        
        return Conclusion(content=conclusion_text, summary=summary, call_to_action=call_to_action)
    except Exception as e:
        raise ConclusionGenerationError(f"Error generating conclusion with key points: {str(e)}")
