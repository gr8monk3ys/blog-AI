"""
Introduction generation functionality.
"""
from typing import List, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for introduction generation
        prompt = f"""
        Generate an engaging introduction for a blog post with the following details:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        if outline:
            prompt += f"\nOutline: {outline}"
        
        if target_audience:
            prompt += f"\nTarget Audience: {target_audience}"
        
        prompt += f"""
        Tone: {tone}
        
        Requirements:
        - The introduction should be 3-4 paragraphs.
        - Include a compelling hook in the first paragraph to grab the reader's attention.
        - Clearly state the purpose or thesis of the blog post.
        - Include at least one of the main keywords naturally.
        - Set the tone and expectations for the rest of the blog post.
        - Use a {tone} tone throughout.
        
        Return only the introduction, nothing else.
        """
        
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
    options: Optional[GenerationOptions] = None
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
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for introduction generation
        prompt = f"""
        Generate an engaging introduction for a blog post with the following details:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        if outline:
            prompt += f"\nOutline: {outline}"
        
        if target_audience:
            prompt += f"\nTarget Audience: {target_audience}"
        
        prompt += f"""
        Tone: {tone}
        
        Research Results:
        {str(research_results)[:1000]}...
        
        Requirements:
        - The introduction should be 3-4 paragraphs.
        - Include a compelling hook in the first paragraph to grab the reader's attention.
        - Clearly state the purpose or thesis of the blog post.
        - Include at least one of the main keywords naturally.
        - Incorporate relevant information from the research results.
        - Set the tone and expectations for the rest of the blog post.
        - Use a {tone} tone throughout.
        
        Return only the introduction, nothing else.
        """
        
        # Generate introduction
        introduction_text = generate_text(prompt, provider, options)
        
        # Clean up the introduction
        introduction_text = introduction_text.strip()
        
        # Extract hook and thesis
        hook, thesis = extract_hook_and_thesis(introduction_text, provider, options)
        
        return Introduction(content=introduction_text, hook=hook, thesis=thesis)
    except Exception as e:
        raise IntroductionGenerationError(f"Error generating introduction with research: {str(e)}")
