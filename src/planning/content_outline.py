"""
Content outline generation functionality.
"""
import os
import json
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.planning import (
    ContentOutline,
    ContentTopic
)
from ..research.web_researcher import conduct_web_research


class ContentOutlineError(Exception):
    """Exception raised for errors in the content outline generation process."""
    pass


def generate_content_outline(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for outline generation
        prompt = f"""
        Generate a detailed outline for a blog post or article with the following title:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += f"""
        
        Requirements:
        - Include {num_sections} main sections.
        - Each section should have a clear, descriptive heading.
        - The outline should follow a logical flow.
        - Include an introduction and conclusion.
        """
        
        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the outline.
            """
        
        prompt += """
        Return your outline in the following format:
        
        # Introduction
        
        # [Section 1 Heading]
        
        # [Section 2 Heading]
        
        # [Section 3 Heading]
        
        # [Section 4 Heading]
        
        # [Section 5 Heading]
        
        # Conclusion
        """
        
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
            title=title,
            sections=sections,
            keywords=keywords or []
        )
    except Exception as e:
        raise ContentOutlineError(f"Error generating content outline: {str(e)}")


def generate_detailed_content_outline(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for outline generation
        prompt = f"""
        Generate a detailed outline for a blog post or article with the following title:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += f"""
        
        Requirements:
        - Include {num_sections} main sections.
        - Each section should have a clear, descriptive heading.
        - Each section should have 3-5 bullet points outlining the key points to cover.
        - The outline should follow a logical flow.
        - Include an introduction and conclusion.
        """
        
        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the outline.
            """
        
        prompt += """
        Return your outline in the following format:
        
        # Introduction
        - [Key point 1]
        - [Key point 2]
        - [Key point 3]
        
        # [Section 1 Heading]
        - [Key point 1]
        - [Key point 2]
        - [Key point 3]
        - [Key point 4]
        - [Key point 5]
        
        # [Section 2 Heading]
        - [Key point 1]
        - [Key point 2]
        - [Key point 3]
        - [Key point 4]
        
        And so on.
        """
        
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
            title=title,
            sections=sections,
            keywords=keywords or []
        )
    except Exception as e:
        raise ContentOutlineError(f"Error generating detailed content outline: {str(e)}")


def generate_content_outline_with_research(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        
        # Create prompt for outline generation
        prompt = f"""
        Generate a detailed outline for a blog post or article with the following title:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += f"""
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        
        Requirements:
        - Include {num_sections} main sections.
        - Each section should have a clear, descriptive heading.
        - The outline should follow a logical flow.
        - Include an introduction and conclusion.
        - Incorporate insights from the research.
        """
        
        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the outline.
            """
        
        prompt += """
        Return your outline in the following format:
        
        # Introduction
        
        # [Section 1 Heading]
        
        # [Section 2 Heading]
        
        # [Section 3 Heading]
        
        # [Section 4 Heading]
        
        # [Section 5 Heading]
        
        # Conclusion
        """
        
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
            title=title,
            sections=sections,
            keywords=keywords or []
        )
    except Exception as e:
        raise ContentOutlineError(f"Error generating content outline with research: {str(e)}")


def generate_content_outline_from_topic(
    topic: ContentTopic,
    num_sections: int = 5,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
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
        # Create prompt for outline generation
        prompt = f"""
        Generate a detailed outline for a blog post or article with the following details:
        
        Title: {topic.title}
        Keywords: {', '.join(topic.keywords)}
        """
        
        if topic.description:
            prompt += f"\nDescription: {topic.description}"
        
        prompt += f"""
        
        Requirements:
        - Include {num_sections} main sections.
        - Each section should have a clear, descriptive heading.
        - The outline should follow a logical flow.
        - Include an introduction and conclusion.
        - Incorporate the keywords naturally throughout the outline.
        """
        
        prompt += """
        Return your outline in the following format:
        
        # Introduction
        
        # [Section 1 Heading]
        
        # [Section 2 Heading]
        
        # [Section 3 Heading]
        
        # [Section 4 Heading]
        
        # [Section 5 Heading]
        
        # Conclusion
        """
        
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
            title=topic.title,
            sections=sections,
            keywords=topic.keywords
        )
    except Exception as e:
        raise ContentOutlineError(f"Error generating content outline from topic: {str(e)}")


def save_content_outline_to_json(
    outline: ContentOutline,
    file_path: str
) -> None:
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
            "keywords": outline.keywords
        }
        
        # Write outline to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, indent=2)
    except Exception as e:
        raise ContentOutlineError(f"Error saving content outline to JSON: {str(e)}")


def load_content_outline_from_json(
    file_path: str
) -> ContentOutline:
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
            keywords=outline_data["keywords"]
        )
    except Exception as e:
        raise ContentOutlineError(f"Error loading content outline from JSON: {str(e)}")
