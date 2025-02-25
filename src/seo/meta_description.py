"""
Meta description generation functionality.
"""
from typing import List, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
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
    options: Optional[GenerationOptions] = None
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
        # Create prompt for meta description generation
        prompt = f"""
        Generate a compelling and SEO-friendly meta description for a blog post with the following details:
        
        Title: {title}
        Keywords: {', '.join(keywords)}
        Tone: {tone}
        
        Requirements:
        - The meta description should be between 150-160 characters.
        - Include at least one of the main keywords naturally.
        - Make it compelling and encourage clicks.
        - Accurately represent the content.
        - Do not use quotes or special characters.
        
        Return only the meta description text, nothing else.
        """
        
        if content:
            # Add a summary of the content to the prompt
            content_summary = content[:500] + "..." if len(content) > 500 else content
            prompt += f"\n\nContent Summary: {content_summary}"
        
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
    options: Optional[GenerationOptions] = None
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
        # Create prompt for meta description generation
        prompt = f"""
        Generate {count} compelling and SEO-friendly meta descriptions for a blog post with the following details:
        
        Title: {title}
        Keywords: {', '.join(keywords)}
        Tone: {tone}
        
        Requirements:
        - Each meta description should be between 150-160 characters.
        - Include at least one of the main keywords naturally.
        - Make them compelling and encourage clicks.
        - Accurately represent the content.
        - Do not use quotes or special characters.
        - Each description should be different in approach and wording.
        
        Return the meta descriptions as a numbered list, with each description on a new line.
        """
        
        if content:
            # Add a summary of the content to the prompt
            content_summary = content[:500] + "..." if len(content) > 500 else content
            prompt += f"\n\nContent Summary: {content_summary}"
        
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
            if line[0].isdigit() and len(line) > 2 and line[1] == "." and line[2] == " ":
                line = line[3:]
            
            # Clean up the description
            description_text = line.strip()
            
            # Ensure the description is not too long
            if len(description_text) > 160:
                description_text = description_text[:157] + "..."
            
            descriptions.append(MetaDescription(content=description_text))
        
        # Ensure we have the requested number of descriptions
        while len(descriptions) < count:
            descriptions.append(generate_meta_description(title, keywords, content, tone, provider, options))
        
        return descriptions[:count]
    except Exception as e:
        raise MetaDescriptionError(f"Error generating meta descriptions: {str(e)}")
