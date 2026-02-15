"""
AI Image Generator for Blog AI.

Supports multiple image generation providers:
- OpenAI DALL-E 3 (primary)
- Stability AI (fallback)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional, Union

try:
    import openai  # type: ignore
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

from ..types.images import (
    BlogImagesResult,
    ImageProvider,
    ImageQuality,
    ImageResult,
    ImageStyle,
    ImageType,
)
from .prompt_generator import PromptGenerator

logger = logging.getLogger(__name__)

# Sentinel to distinguish "not provided" from "explicitly None" when reading env vars.
_UNSET: object = object()


class ImageGenerationError(Exception):
    """Exception raised for errors in the image generation process."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class ImageGenerator:
    """
    AI-powered image generator supporting multiple providers.

    Provides a unified interface for generating images using
    OpenAI DALL-E 3 or Stability AI as providers.
    """

    # Default timeout for image generation requests (in seconds)
    DEFAULT_TIMEOUT = 120

    # Size mappings for different providers
    OPENAI_SIZES = {
        "1024x1024": "1024x1024",
        "1792x1024": "1792x1024",
        "1024x1792": "1024x1792",
    }

    STABILITY_SIZES = {
        "1024x1024": (1024, 1024),
        "1344x768": (1344, 768),
        "768x1344": (768, 1344),
        "1792x1024": (1344, 768),  # Map to closest
        "1024x1792": (768, 1344),  # Map to closest
    }

    def __init__(
        self,
        provider: str = "openai",
        openai_api_key: Union[str, None, object] = _UNSET,
        stability_api_key: Union[str, None, object] = _UNSET,
    ):
        """
        Initialize the image generator.

        Args:
            provider: The default provider to use ("openai" or "stability").
            openai_api_key: OpenAI API key. If omitted, reads from environment.
                           If explicitly set to None, disables OpenAI.
            stability_api_key: Stability AI API key. If omitted, reads from environment.
                               If explicitly set to None, disables Stability.
        """
        self.default_provider = provider

        if openai_api_key is _UNSET:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        else:
            self.openai_api_key = openai_api_key  # type: ignore[assignment]

        if stability_api_key is _UNSET:
            self.stability_api_key = os.environ.get("STABILITY_API_KEY")
        else:
            self.stability_api_key = stability_api_key  # type: ignore[assignment]

        self.prompt_generator = PromptGenerator()

        # Validate that at least one provider is configured
        if not self.openai_api_key and not self.stability_api_key:
            logger.warning(
                "No image generation API keys configured. "
                "Set OPENAI_API_KEY or STABILITY_API_KEY."
            )

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
        quality: str = "standard",
        provider: Optional[str] = None,
        negative_prompt: Optional[str] = None,
    ) -> ImageResult:
        """
        Generate an image from a prompt.

        Args:
            prompt: The text prompt to generate an image from.
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792").
            style: Image style ("natural" or "vivid", DALL-E 3 only).
            quality: Image quality ("standard" or "hd", DALL-E 3 only).
            provider: Provider to use (overrides default).
            negative_prompt: What to avoid in the image (Stability AI only).

        Returns:
            ImageResult with the generated image URL and metadata.

        Raises:
            ImageGenerationError: If image generation fails.
        """
        use_provider = provider or self.default_provider

        # Refine prompt for the specific provider
        refined_prompt = self.prompt_generator.refine_prompt_for_provider(
            prompt, use_provider
        )

        if use_provider == "openai":
            return await self._generate_with_openai(
                prompt=refined_prompt,
                size=size,
                style=style,
                quality=quality,
            )
        elif use_provider == "stability":
            return await self._generate_with_stability(
                prompt=refined_prompt,
                size=size,
                negative_prompt=negative_prompt,
            )
        else:
            raise ImageGenerationError(
                f"Unsupported provider: {use_provider}",
                provider=use_provider,
            )

    async def generate_from_content(
        self,
        content: str,
        image_type: str = "featured",
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        size: Optional[str] = None,
        style: str = "natural",
        quality: str = "standard",
        provider: Optional[str] = None,
    ) -> ImageResult:
        """
        Generate an image from blog content.

        Analyzes the content to generate an appropriate image prompt,
        then generates the image.

        Args:
            content: The blog content to generate an image from.
            image_type: Type of image ("featured", "social", "inline").
            title: Optional blog title.
            keywords: Optional keywords.
            size: Optional size override.
            style: Image style.
            quality: Image quality.
            provider: Provider to use.

        Returns:
            ImageResult with the generated image.
        """
        # Convert string to ImageType enum
        try:
            img_type = ImageType(image_type)
        except ValueError:
            img_type = ImageType.FEATURED

        # Determine appropriate size if not specified
        if not size:
            size = self._get_default_size_for_type(img_type)

        # Generate the prompt
        prompt = self.prompt_generator.generate_prompt(
            content=content,
            image_type=img_type,
            title=title,
            keywords=keywords,
        )

        logger.info(f"Generating {image_type} image with prompt: {prompt[:100]}...")

        return await self.generate_image(
            prompt=prompt,
            size=size,
            style=style,
            quality=quality,
            provider=provider,
        )

    async def generate_blog_images(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]] = None,
        generate_featured: bool = True,
        generate_social: bool = True,
        inline_count: int = 0,
        provider: Optional[str] = None,
        style: str = "natural",
        quality: str = "standard",
    ) -> BlogImagesResult:
        """
        Generate all images for a blog post.

        Args:
            content: The full blog content.
            title: The blog title.
            keywords: Optional keywords.
            generate_featured: Whether to generate a featured image.
            generate_social: Whether to generate a social media image.
            inline_count: Number of inline images to generate (0-5).
            provider: Provider to use.
            style: Image style.
            quality: Image quality.

        Returns:
            BlogImagesResult with all generated images.
        """
        use_provider = provider or self.default_provider
        result = BlogImagesResult(provider_used=use_provider)
        tasks = []

        # Generate featured image
        if generate_featured:
            tasks.append(
                self._generate_featured_image(
                    content=content,
                    title=title,
                    keywords=keywords,
                    provider=use_provider,
                    style=style,
                    quality=quality,
                )
            )
        else:
            tasks.append(asyncio.coroutine(lambda: None)())

        # Generate social image
        if generate_social:
            tasks.append(
                self._generate_social_image(
                    content=content,
                    title=title,
                    keywords=keywords,
                    provider=use_provider,
                    style=style,
                    quality=quality,
                )
            )
        else:
            tasks.append(asyncio.coroutine(lambda: None)())

        # Generate inline images
        inline_tasks = []
        if inline_count > 0:
            # Split content into sections for inline images
            sections = self._split_content_for_inline_images(content, inline_count)
            for i, section in enumerate(sections):
                inline_tasks.append(
                    self._generate_inline_image(
                        content=section,
                        title=title,
                        keywords=keywords,
                        provider=use_provider,
                        style=style,
                        quality=quality,
                        index=i,
                    )
                )

        # Execute all tasks concurrently
        try:
            main_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle featured image result
            if generate_featured and not isinstance(main_results[0], Exception):
                result.featured_image = main_results[0]
                result.total_generated += 1
            elif isinstance(main_results[0], Exception):
                logger.error(f"Failed to generate featured image: {main_results[0]}")

            # Handle social image result
            if generate_social and len(main_results) > 1:
                if not isinstance(main_results[1], Exception):
                    result.social_image = main_results[1]
                    result.total_generated += 1
                elif isinstance(main_results[1], Exception):
                    logger.error(f"Failed to generate social image: {main_results[1]}")

            # Handle inline images
            if inline_tasks:
                inline_results = await asyncio.gather(*inline_tasks, return_exceptions=True)
                for inline_result in inline_results:
                    if not isinstance(inline_result, Exception) and inline_result:
                        result.inline_images.append(inline_result)
                        result.total_generated += 1
                    elif isinstance(inline_result, Exception):
                        logger.error(f"Failed to generate inline image: {inline_result}")

        except Exception as e:
            logger.error(f"Error generating blog images: {e}")
            raise ImageGenerationError(
                f"Failed to generate blog images: {str(e)}",
                provider=use_provider,
                original_error=e,
            )

        return result

    async def _generate_with_openai(
        self,
        prompt: str,
        size: str,
        style: str,
        quality: str,
    ) -> ImageResult:
        """
        Generate an image using OpenAI DALL-E 3.

        Args:
            prompt: The image prompt.
            size: Image size.
            style: Image style.
            quality: Image quality.

        Returns:
            ImageResult with the generated image.
        """
        if not self.openai_api_key:
            raise ImageGenerationError(
                "OpenAI API key not configured",
                provider="openai",
            )

        if openai is None:
            raise ImageGenerationError(
                "OpenAI package not installed. Install with 'pip install openai'.",
                provider="openai",
            )

        try:
            client = openai.AsyncOpenAI(
                api_key=self.openai_api_key,
                timeout=self.DEFAULT_TIMEOUT,
            )

            # Validate and map size
            openai_size = self.OPENAI_SIZES.get(size, "1024x1024")

            # Map style and quality to DALL-E 3 values
            dalle_style = "vivid" if style == "vivid" else "natural"
            dalle_quality = "hd" if quality == "hd" else "standard"

            try:
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=openai_size,
                    quality=dalle_quality,
                    style=dalle_style,
                    n=1,
                )
            except Exception as e:
                def _is_openai_exc(attr: str) -> bool:
                    exc_cls = getattr(openai, attr, None)
                    return (
                        isinstance(exc_cls, type)
                        and issubclass(exc_cls, Exception)
                        and isinstance(e, exc_cls)
                    )

                if _is_openai_exc("AuthenticationError"):
                    raise ImageGenerationError(
                        f"OpenAI authentication failed: {e}",
                        provider="openai",
                        original_error=e,
                    )
                if _is_openai_exc("RateLimitError"):
                    raise ImageGenerationError(
                        f"OpenAI rate limit exceeded: {e}",
                        provider="openai",
                        original_error=e,
                    )
                if _is_openai_exc("BadRequestError"):
                    raise ImageGenerationError(
                        f"OpenAI bad request (possibly content policy violation): {e}",
                        provider="openai",
                        original_error=e,
                    )
                if _is_openai_exc("OpenAIError"):
                    raise ImageGenerationError(
                        f"OpenAI error: {e}",
                        provider="openai",
                        original_error=e,
                    )
                raise ImageGenerationError(
                    f"OpenAI error: {e}",
                    provider="openai",
                    original_error=e,
                )

            # Extract result
            image_data = response.data[0]

            return ImageResult(
                url=image_data.url,
                prompt_used=prompt,
                provider="openai",
                size=openai_size,
                style=dalle_style,
                quality=dalle_quality,
                created_at=datetime.now(),
                revised_prompt=image_data.revised_prompt,
                metadata={
                    "model": "dall-e-3",
                },
            )
        except ImageGenerationError:
            raise
        except Exception as e:
            # Client construction or other unexpected failures.
            raise ImageGenerationError(
                f"OpenAI error: {e}",
                provider="openai",
                original_error=e,
            )

    async def _generate_with_stability(
        self,
        prompt: str,
        size: str,
        negative_prompt: Optional[str] = None,
    ) -> ImageResult:
        """
        Generate an image using Stability AI.

        Args:
            prompt: The image prompt.
            size: Image size.
            negative_prompt: What to avoid in the image.

        Returns:
            ImageResult with the generated image.
        """
        if not self.stability_api_key:
            raise ImageGenerationError(
                "Stability AI API key not configured",
                provider="stability",
            )

        try:
            import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
            from stability_sdk import client as stability_client
        except ImportError:
            raise ImageGenerationError(
                "Stability SDK not installed. Install with 'pip install stability-sdk'.",
                provider="stability",
            )

        try:
            # Get dimensions for size
            width, height = self.STABILITY_SIZES.get(size, (1024, 1024))

            # Create stability client
            stability = stability_client.StabilityInference(
                key=self.stability_api_key,
                verbose=False,
            )

            # Set up prompts
            prompts = [
                generation.Prompt(
                    text=prompt,
                    parameters=generation.PromptParameters(weight=1.0),
                )
            ]

            if negative_prompt:
                prompts.append(
                    generation.Prompt(
                        text=negative_prompt,
                        parameters=generation.PromptParameters(weight=-1.0),
                    )
                )

            # Run in executor since stability SDK is synchronous
            loop = asyncio.get_running_loop()
            answers = await loop.run_in_executor(
                None,
                lambda: stability.generate(
                    prompt=prompts,
                    width=width,
                    height=height,
                    steps=30,
                    cfg_scale=7.0,
                    sampler=generation.SAMPLER_K_DPM_2_ANCESTRAL,
                ),
            )

            # Process response
            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        # For now, we would need to upload to storage
                        # and return a URL. For this implementation,
                        # we return base64 data URL
                        import base64

                        b64_data = base64.b64encode(artifact.binary).decode()
                        data_url = f"data:image/png;base64,{b64_data}"

                        return ImageResult(
                            url=data_url,
                            prompt_used=prompt,
                            provider="stability",
                            size=f"{width}x{height}",
                            style=None,
                            quality=None,
                            created_at=datetime.now(),
                            metadata={
                                "model": "stable-diffusion-xl",
                                "steps": 30,
                                "cfg_scale": 7.0,
                            },
                        )

            raise ImageGenerationError(
                "No image generated by Stability AI",
                provider="stability",
            )

        except Exception as e:
            if isinstance(e, ImageGenerationError):
                raise
            raise ImageGenerationError(
                f"Stability AI error: {e}",
                provider="stability",
                original_error=e,
            )

    async def _generate_featured_image(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]],
        provider: str,
        style: str,
        quality: str,
    ) -> ImageResult:
        """Generate a featured image."""
        return await self.generate_from_content(
            content=content,
            image_type="featured",
            title=title,
            keywords=keywords,
            size="1792x1024",  # Landscape for featured
            style=style,
            quality=quality,
            provider=provider,
        )

    async def _generate_social_image(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]],
        provider: str,
        style: str,
        quality: str,
    ) -> ImageResult:
        """Generate a social media image."""
        return await self.generate_from_content(
            content=content,
            image_type="social",
            title=title,
            keywords=keywords,
            size="1024x1024",  # Square for social
            style=style,
            quality=quality,
            provider=provider,
        )

    async def _generate_inline_image(
        self,
        content: str,
        title: str,
        keywords: Optional[List[str]],
        provider: str,
        style: str,
        quality: str,
        index: int,
    ) -> ImageResult:
        """Generate an inline image."""
        return await self.generate_from_content(
            content=content,
            image_type="inline",
            title=title,
            keywords=keywords,
            size="1024x1024",
            style=style,
            quality="standard",  # Use standard for inline
            provider=provider,
        )

    def _get_default_size_for_type(self, image_type: ImageType) -> str:
        """Get the default size for an image type."""
        size_map = {
            ImageType.FEATURED: "1792x1024",
            ImageType.SOCIAL: "1024x1024",
            ImageType.INLINE: "1024x1024",
            ImageType.THUMBNAIL: "1024x1024",
            ImageType.HERO: "1792x1024",
        }
        return size_map.get(image_type, "1024x1024")

    def _split_content_for_inline_images(
        self,
        content: str,
        count: int,
    ) -> List[str]:
        """
        Split content into sections for inline image generation.

        Args:
            content: The full content.
            count: Number of sections to create.

        Returns:
            List of content sections.
        """
        if count <= 0:
            return []

        # Split by paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        if len(paragraphs) <= count:
            return paragraphs[:count]

        # Distribute paragraphs evenly
        section_size = len(paragraphs) // count
        sections = []

        for i in range(count):
            start = i * section_size
            end = start + section_size if i < count - 1 else len(paragraphs)
            section = "\n\n".join(paragraphs[start:end])
            sections.append(section)

        return sections
