"""
Image alt text generation functionality.
"""
from typing import List, Optional, Dict

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.seo import ImageAltText


class ImageAltTextError(Exception):
    """Exception raised for errors in the image alt text generation process."""
    pass


def generate_image_alt_text(
    image_path: str,
    context: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> ImageAltText:
    """
    Generate alt text for an image.
    
    Args:
        image_path: The path to the image.
        context: The context in which the image appears.
        keywords: The target keywords.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated image alt text.
        
    Raises:
        ImageAltTextError: If an error occurs during image alt text generation.
    """
    try:
        # Extract image name from path
        image_name = image_path.split("/")[-1].split("\\")[-1]
        
        # Create prompt for alt text generation
        prompt = f"""
        Generate a concise and descriptive alt text for an image with the following details:
        
        Image filename: {image_name}
        """
        
        if context:
            prompt += f"\nContext: {context}"
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += """
        
        Requirements:
        - The alt text should be concise (8-10 words maximum).
        - Be descriptive and specific about what the image shows.
        - Include a relevant keyword if it fits naturally.
        - Do not start with phrases like "Image of" or "Picture of".
        - Focus on the main subject of the image.
        
        Return only the alt text, nothing else.
        """
        
        # Generate alt text
        alt_text = generate_text(prompt, provider, options)
        
        # Clean up the alt text
        alt_text = alt_text.strip()
        
        # Remove any quotes
        alt_text = alt_text.replace('"', '').replace("'", "")
        
        return ImageAltText(image_path=image_path, alt_text=alt_text)
    except Exception as e:
        raise ImageAltTextError(f"Error generating image alt text: {str(e)}")


def generate_multiple_image_alt_texts(
    image_paths: List[str],
    context: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[ImageAltText]:
    """
    Generate alt text for multiple images.
    
    Args:
        image_paths: The paths to the images.
        context: The context in which the images appear.
        keywords: The target keywords.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated image alt texts.
        
    Raises:
        ImageAltTextError: If an error occurs during image alt text generation.
    """
    try:
        alt_texts = []
        
        for image_path in image_paths:
            alt_text = generate_image_alt_text(
                image_path=image_path,
                context=context,
                keywords=keywords,
                provider=provider,
                options=options
            )
            
            alt_texts.append(alt_text)
        
        return alt_texts
    except Exception as e:
        raise ImageAltTextError(f"Error generating image alt texts: {str(e)}")


def generate_batch_image_alt_texts(
    image_paths: List[str],
    context: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Dict[str, ImageAltText]:
    """
    Generate alt text for multiple images in a single batch request.
    
    Args:
        image_paths: The paths to the images.
        context: The context in which the images appear.
        keywords: The target keywords.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        A dictionary mapping image paths to their alt texts.
        
    Raises:
        ImageAltTextError: If an error occurs during image alt text generation.
    """
    try:
        # Extract image names from paths
        image_names = [path.split("/")[-1].split("\\")[-1] for path in image_paths]
        
        # Create prompt for batch alt text generation
        prompt = f"""
        Generate concise and descriptive alt text for the following images:
        
        """
        
        for i, name in enumerate(image_names):
            prompt += f"{i+1}. {name}\n"
        
        if context:
            prompt += f"\nContext: {context}"
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += """
        
        Requirements:
        - Each alt text should be concise (8-10 words maximum).
        - Be descriptive and specific about what each image shows.
        - Include a relevant keyword if it fits naturally.
        - Do not start with phrases like "Image of" or "Picture of".
        - Focus on the main subject of each image.
        
        Return the alt texts as a numbered list corresponding to the image numbers above.
        """
        
        # Generate alt texts
        alt_texts_response = generate_text(prompt, provider, options)
        
        # Parse the alt texts
        alt_texts = {}
        lines = alt_texts_response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to extract the number and alt text
            parts = line.split(".", 1)
            if len(parts) != 2:
                continue
            
            try:
                index = int(parts[0].strip()) - 1
                if 0 <= index < len(image_paths):
                    alt_text = parts[1].strip()
                    # Remove any quotes
                    alt_text = alt_text.replace('"', '').replace("'", "")
                    
                    alt_texts[image_paths[index]] = ImageAltText(
                        image_path=image_paths[index],
                        alt_text=alt_text
                    )
            except ValueError:
                continue
        
        # Ensure we have alt text for all images
        for i, path in enumerate(image_paths):
            if path not in alt_texts:
                alt_texts[path] = generate_image_alt_text(
                    image_path=path,
                    context=context,
                    keywords=keywords,
                    provider=provider,
                    options=options
                )
        
        return alt_texts
    except Exception as e:
        raise ImageAltTextError(f"Error generating batch image alt texts: {str(e)}")
