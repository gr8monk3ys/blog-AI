"""
Prompt generator for AI image generation.

Generates optimized image prompts from blog content by extracting
key themes, subjects, and visual elements.
"""

import logging
import re
from typing import List, Optional

from ..types.images import ImageType

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates image prompts from blog content.

    Analyzes text content to extract key themes and generate
    descriptive prompts suitable for AI image generation.
    """

    # Maximum characters to analyze from content
    MAX_CONTENT_LENGTH = 5000

    # Common words to filter out when extracting themes
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "can", "will", "just", "should", "now", "also", "like", "get", "make",
        "know", "take", "see", "come", "think", "look", "want", "give", "use",
        "find", "tell", "ask", "work", "seem", "feel", "try", "leave", "call",
        "this", "that", "these", "those", "what", "which", "who", "whom",
        "it", "its", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "would", "could", "might",
    }

    # Style modifiers for different image types
    IMAGE_TYPE_MODIFIERS = {
        ImageType.FEATURED: (
            "professional, high-quality, editorial style, "
            "visually striking, blog header image"
        ),
        ImageType.SOCIAL: (
            "engaging, eye-catching, social media optimized, "
            "bold colors, shareable"
        ),
        ImageType.INLINE: (
            "informative, illustrative, supporting content, "
            "clear and focused"
        ),
        ImageType.THUMBNAIL: (
            "simple, clear, recognizable at small sizes, "
            "high contrast"
        ),
        ImageType.HERO: (
            "dramatic, impactful, full-width banner style, "
            "cinematic quality"
        ),
    }

    def __init__(self):
        """Initialize the prompt generator."""
        pass

    def generate_prompt(
        self,
        content: str,
        image_type: ImageType = ImageType.FEATURED,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        custom_style: Optional[str] = None,
    ) -> str:
        """
        Generate an image prompt from content.

        Args:
            content: The text content to generate a prompt from.
            image_type: The type of image to generate.
            title: Optional title to incorporate.
            keywords: Optional keywords to emphasize.
            custom_style: Optional custom style modifier.

        Returns:
            A descriptive prompt for image generation.
        """
        # Truncate content if too long
        content = content[:self.MAX_CONTENT_LENGTH]

        # Extract key themes from content
        themes = self._extract_themes(content, title, keywords)

        # Build the base prompt
        base_prompt = self._build_base_prompt(themes, title)

        # Add style modifiers based on image type
        style_modifier = custom_style or self.IMAGE_TYPE_MODIFIERS.get(
            image_type, self.IMAGE_TYPE_MODIFIERS[ImageType.FEATURED]
        )

        # Combine into final prompt
        final_prompt = f"{base_prompt}, {style_modifier}"

        # Add safety and quality guidelines
        final_prompt = self._add_quality_guidelines(final_prompt)

        logger.debug(f"Generated image prompt: {final_prompt[:100]}...")
        return final_prompt

    def generate_featured_prompt(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a prompt specifically for featured/hero images.

        Args:
            content: The blog content.
            title: The blog title.
            keywords: Optional keywords.

        Returns:
            A prompt optimized for featured images.
        """
        return self.generate_prompt(
            content=content,
            image_type=ImageType.FEATURED,
            title=title,
            keywords=keywords,
        )

    def generate_social_prompt(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a prompt specifically for social media images.

        Args:
            content: The blog content.
            title: The blog title.
            keywords: Optional keywords.

        Returns:
            A prompt optimized for social media sharing.
        """
        return self.generate_prompt(
            content=content,
            image_type=ImageType.SOCIAL,
            title=title,
            keywords=keywords,
            custom_style=(
                "vibrant colors, bold composition, "
                "social media friendly, attention-grabbing, "
                "minimal text space for overlay"
            ),
        )

    def generate_inline_prompt(
        self,
        content: str,
        section_context: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a prompt for inline content images.

        Args:
            content: The relevant section content.
            section_context: Additional context about the section.
            keywords: Optional keywords.

        Returns:
            A prompt optimized for inline images.
        """
        combined_content = content
        if section_context:
            combined_content = f"{section_context}\n\n{content}"

        return self.generate_prompt(
            content=combined_content,
            image_type=ImageType.INLINE,
            keywords=keywords,
        )

    def _extract_themes(
        self,
        content: str,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Extract key themes from content.

        Args:
            content: The text content.
            title: Optional title.
            keywords: Optional keywords.

        Returns:
            List of extracted themes.
        """
        themes = []

        # Add keywords first (highest priority)
        if keywords:
            themes.extend(keywords[:5])

        # Extract title words (high priority)
        if title:
            title_words = self._extract_significant_words(title)
            themes.extend(title_words[:3])

        # Extract frequent significant words from content
        content_words = self._extract_significant_words(content)

        # Count word frequencies
        word_freq = {}
        for word in content_words:
            word_lower = word.lower()
            if word_lower not in self.STOP_WORDS and len(word_lower) > 3:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Get top words by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_words = [word for word, _ in sorted_words[:10]]

        # Add top words that are not already in themes
        for word in top_words:
            if word not in [t.lower() for t in themes]:
                themes.append(word)
                if len(themes) >= 8:
                    break

        return themes

    def _extract_significant_words(self, text: str) -> List[str]:
        """
        Extract significant words from text.

        Args:
            text: The input text.

        Returns:
            List of significant words.
        """
        # Remove special characters and split into words
        words = re.findall(r"\b[a-zA-Z]+\b", text)

        # Filter out stop words and short words
        significant = [
            word for word in words
            if word.lower() not in self.STOP_WORDS and len(word) > 3
        ]

        return significant

    def _build_base_prompt(
        self,
        themes: List[str],
        title: Optional[str] = None,
    ) -> str:
        """
        Build the base prompt from themes.

        Args:
            themes: Extracted themes.
            title: Optional title.

        Returns:
            Base prompt string.
        """
        if not themes:
            # Fallback to generic prompt
            return "abstract professional illustration, modern digital art"

        # Create a descriptive scene
        primary_theme = themes[0] if themes else "abstract concept"
        secondary_themes = themes[1:4] if len(themes) > 1 else []

        # Build prompt components
        components = [
            f"A visual representation of {primary_theme}",
        ]

        if secondary_themes:
            theme_str = ", ".join(secondary_themes)
            components.append(f"featuring elements of {theme_str}")

        if title:
            # Add a subtle reference to the title theme
            components.append(f"inspired by the concept of \"{title[:50]}\"")

        return ", ".join(components)

    def _add_quality_guidelines(self, prompt: str) -> str:
        """
        Add quality and safety guidelines to the prompt.

        Args:
            prompt: The base prompt.

        Returns:
            Prompt with quality guidelines.
        """
        quality_suffix = (
            ", high resolution, professional photography style, "
            "clean composition, well-lit, detailed"
        )

        # Safety guidelines (avoid problematic content)
        safety_suffix = (
            ", appropriate for professional use, no text or watermarks"
        )

        return f"{prompt}{quality_suffix}{safety_suffix}"

    def refine_prompt_for_provider(
        self,
        prompt: str,
        provider: str,
    ) -> str:
        """
        Refine a prompt for a specific provider.

        Args:
            prompt: The base prompt.
            provider: The image provider (openai, stability).

        Returns:
            Provider-optimized prompt.
        """
        if provider == "openai":
            # DALL-E 3 handles detailed prompts well
            return prompt
        elif provider == "stability":
            # Stability AI prefers more structured prompts
            # Add style tokens that work well with Stable Diffusion
            return f"{prompt}, trending on artstation, highly detailed, 8k resolution"
        else:
            return prompt
