"""
Structured data generation functionality.
"""
import json
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.seo import StructuredData


class StructuredDataError(Exception):
    """Exception raised for errors in the structured data generation process."""
    pass


def generate_structured_data(
    type: str,
    content: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> StructuredData:
    """
    Generate structured data for a blog post or webpage.
    
    Args:
        type: The type of structured data to generate (e.g., "Article", "FAQPage", "Recipe").
        content: The content of the blog post or webpage.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated structured data.
        
    Raises:
        StructuredDataError: If an error occurs during structured data generation.
    """
    try:
        # Create prompt for structured data generation
        prompt = f"""
        Generate JSON-LD structured data for a {type} based on the following content:
        
        {content[:1000]}...
        
        Requirements:
        - Follow the schema.org guidelines for {type}.
        - Include all required properties for the {type} type.
        - Ensure the JSON is valid and properly formatted.
        - Extract relevant information from the content.
        - Do not include any explanatory text, just return the JSON-LD.
        
        Return the structured data as a JSON-LD object, including the <script type="application/ld+json"> tags.
        """
        
        # Generate structured data
        structured_data_text = generate_text(prompt, provider, options)
        
        # Extract JSON from the response
        json_text = extract_json_from_text(structured_data_text)
        
        # Parse the JSON
        data = json.loads(json_text)
        
        return StructuredData(type=type, data=data)
    except Exception as e:
        raise StructuredDataError(f"Error generating structured data: {str(e)}")


def generate_article_structured_data(
    title: str,
    description: str,
    author: str,
    published_date: str,
    modified_date: Optional[str] = None,
    image_url: Optional[str] = None,
    publisher_name: Optional[str] = None,
    publisher_logo_url: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> StructuredData:
    """
    Generate Article structured data for a blog post.
    
    Args:
        title: The title of the article.
        description: The description of the article.
        author: The author of the article.
        published_date: The date the article was published (ISO 8601 format).
        modified_date: The date the article was last modified (ISO 8601 format).
        image_url: The URL of the article's featured image.
        publisher_name: The name of the publisher.
        publisher_logo_url: The URL of the publisher's logo.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated structured data.
        
    Raises:
        StructuredDataError: If an error occurs during structured data generation.
    """
    try:
        # Create Article structured data
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": {
                "@type": "Person",
                "name": author
            },
            "datePublished": published_date
        }
        
        # Add optional properties
        if modified_date:
            data["dateModified"] = modified_date
        
        if image_url:
            data["image"] = image_url
        
        if publisher_name:
            publisher = {
                "@type": "Organization",
                "name": publisher_name
            }
            
            if publisher_logo_url:
                publisher["logo"] = {
                    "@type": "ImageObject",
                    "url": publisher_logo_url
                }
            
            data["publisher"] = publisher
        
        return StructuredData(type="Article", data=data)
    except Exception as e:
        raise StructuredDataError(f"Error generating Article structured data: {str(e)}")


def generate_faq_structured_data(
    faqs: List[Dict[str, str]],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> StructuredData:
    """
    Generate FAQPage structured data for a blog post.
    
    Args:
        faqs: A list of dictionaries with "question" and "answer" keys.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated structured data.
        
    Raises:
        StructuredDataError: If an error occurs during structured data generation.
    """
    try:
        # Create FAQPage structured data
        data = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        # Add FAQs
        for faq in faqs:
            data["mainEntity"].append({
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"]
                }
            })
        
        return StructuredData(type="FAQPage", data=data)
    except Exception as e:
        raise StructuredDataError(f"Error generating FAQPage structured data: {str(e)}")


def generate_recipe_structured_data(
    title: str,
    description: str,
    author: str,
    image_url: str,
    prep_time: str,
    cook_time: str,
    total_time: str,
    keywords: List[str],
    recipe_yield: str,
    ingredients: List[str],
    instructions: List[str],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> StructuredData:
    """
    Generate Recipe structured data for a recipe blog post.
    
    Args:
        title: The title of the recipe.
        description: The description of the recipe.
        author: The author of the recipe.
        image_url: The URL of the recipe's image.
        prep_time: The preparation time (ISO 8601 duration format).
        cook_time: The cooking time (ISO 8601 duration format).
        total_time: The total time (ISO 8601 duration format).
        keywords: Keywords for the recipe.
        recipe_yield: The yield of the recipe.
        ingredients: A list of ingredients.
        instructions: A list of instructions.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated structured data.
        
    Raises:
        StructuredDataError: If an error occurs during structured data generation.
    """
    try:
        # Create Recipe structured data
        data = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "name": title,
            "description": description,
            "author": {
                "@type": "Person",
                "name": author
            },
            "image": image_url,
            "prepTime": prep_time,
            "cookTime": cook_time,
            "totalTime": total_time,
            "keywords": ", ".join(keywords),
            "recipeYield": recipe_yield,
            "recipeIngredient": ingredients,
            "recipeInstructions": []
        }
        
        # Add instructions
        for instruction in instructions:
            data["recipeInstructions"].append({
                "@type": "HowToStep",
                "text": instruction
            })
        
        return StructuredData(type="Recipe", data=data)
    except Exception as e:
        raise StructuredDataError(f"Error generating Recipe structured data: {str(e)}")


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text.
    
    Args:
        text: The text containing JSON.
        
    Returns:
        The extracted JSON.
        
    Raises:
        StructuredDataError: If an error occurs during JSON extraction.
    """
    try:
        # Try to find JSON-LD script tags
        start_tag = "<script type=\"application/ld+json\">"
        end_tag = "</script>"
        
        if start_tag in text and end_tag in text:
            start_index = text.find(start_tag) + len(start_tag)
            end_index = text.find(end_tag, start_index)
            
            return text[start_index:end_index].strip()
        
        # Try to find JSON object
        start_brace = text.find("{")
        end_brace = text.rfind("}")
        
        if start_brace != -1 and end_brace != -1:
            return text[start_brace:end_brace + 1].strip()
        
        # If no JSON found, return the original text
        return text.strip()
    except Exception as e:
        raise StructuredDataError(f"Error extracting JSON from text: {str(e)}")
