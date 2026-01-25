"""
Image generation endpoints.

Provides API endpoints for AI-powered image generation,
including featured images, social media images, and inline content images.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.images import ImageGenerationError, ImageGenerator
from src.types.images import (
    AvailableStyles,
    BlogImageGenerationRequest,
    BlogImagesResult,
    ImageGenerationRequest,
    ImageProvider,
    ImageQuality,
    ImageResult,
    ImageSizeInfo,
    ImageStyle,
    ImageStyleInfo,
    ImageType,
)

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


# Singleton image generator instance
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Get or create the image generator instance."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


# Response models for API documentation
class ImageGenerationResponse(BaseModel):
    """Response for image generation endpoints."""

    success: bool = True
    data: ImageResult


class BlogImagesResponse(BaseModel):
    """Response for blog image generation endpoint."""

    success: bool = True
    data: BlogImagesResult


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    provider: Optional[str] = None


@router.post(
    "/generate",
    response_model=ImageGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Generation failed"},
        502: {"model": ErrorResponse, "description": "Provider error"},
    },
)
async def generate_image(
    request: ImageGenerationRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Generate an image from a prompt or content.

    Either `custom_prompt` or `content` must be provided:
    - If `custom_prompt` is provided, it will be used directly.
    - If only `content` is provided, a prompt will be generated from it.

    Args:
        request: Image generation request parameters.
        user_id: Authenticated user ID.

    Returns:
        Generated image result with URL and metadata.
    """
    logger.info(
        f"Image generation requested by user: {user_id}, "
        f"type: {request.image_type}, provider: {request.provider}"
    )

    # Validate that we have either a prompt or content
    if not request.custom_prompt and not request.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'custom_prompt' or 'content' must be provided",
        )

    try:
        generator = get_image_generator()

        if request.custom_prompt:
            # Use custom prompt directly
            result = await generator.generate_image(
                prompt=request.custom_prompt,
                size=request.size,
                style=request.style.value,
                quality=request.quality.value,
                provider=request.provider.value,
                negative_prompt=request.negative_prompt,
            )
        else:
            # Generate prompt from content
            result = await generator.generate_from_content(
                content=request.content,
                image_type=request.image_type.value,
                size=request.size,
                style=request.style.value,
                quality=request.quality.value,
                provider=request.provider.value,
            )

        logger.info(
            f"Image generated successfully: provider={result.provider}, "
            f"size={result.size}"
        )

        return ImageGenerationResponse(success=True, data=result)

    except ImageGenerationError as e:
        logger.error(f"Image generation error: {e}")
        status_code = status.HTTP_502_BAD_GATEWAY
        if "rate limit" in str(e).lower():
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif "authentication" in str(e).lower():
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "content policy" in str(e).lower() or "bad request" in str(e).lower():
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=status_code,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating image: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during image generation.",
        )


@router.post(
    "/generate-for-blog",
    response_model=BlogImagesResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Generation failed"},
        502: {"model": ErrorResponse, "description": "Provider error"},
    },
)
async def generate_blog_images(
    request: BlogImageGenerationRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Generate all images for a blog post.

    Generates featured image, social media image, and optional inline images
    based on the blog content.

    Args:
        request: Blog image generation request parameters.
        user_id: Authenticated user ID.

    Returns:
        All generated images for the blog post.
    """
    logger.info(
        f"Blog image generation requested by user: {user_id}, "
        f"title_length: {len(request.title)}, "
        f"featured: {request.generate_featured}, "
        f"social: {request.generate_social}, "
        f"inline_count: {request.inline_count}"
    )

    if not request.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Blog content is required",
        )

    try:
        generator = get_image_generator()

        result = await generator.generate_blog_images(
            content=request.content,
            title=request.title,
            keywords=request.keywords,
            generate_featured=request.generate_featured,
            generate_social=request.generate_social,
            inline_count=request.inline_count,
            provider=request.provider.value,
            style=request.style.value,
            quality=request.quality.value,
        )

        logger.info(
            f"Blog images generated: total={result.total_generated}, "
            f"provider={result.provider_used}"
        )

        return BlogImagesResponse(success=True, data=result)

    except ImageGenerationError as e:
        logger.error(f"Blog image generation error: {e}")
        status_code = status.HTTP_502_BAD_GATEWAY
        if "rate limit" in str(e).lower():
            status_code = status.HTTP_429_TOO_MANY_REQUESTS

        raise HTTPException(
            status_code=status_code,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating blog images: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during blog image generation.",
        )


@router.get(
    "/styles",
    response_model=AvailableStyles,
    responses={
        401: {"description": "Unauthorized"},
    },
)
async def get_available_styles(
    user_id: str = Depends(verify_api_key),
):
    """
    Get available image styles and sizes.

    Returns information about supported styles, sizes, and providers
    for image generation.

    Args:
        user_id: Authenticated user ID.

    Returns:
        Available styles, sizes, and providers.
    """
    logger.debug(f"Styles request from user: {user_id}")

    styles = [
        ImageStyleInfo(
            name="natural",
            description="Realistic, natural-looking images with balanced colors and lighting",
            provider="openai",
            example_prompt_modifier="realistic, natural lighting, photographic",
        ),
        ImageStyleInfo(
            name="vivid",
            description="Hyper-real, dramatic images with enhanced colors and contrast",
            provider="openai",
            example_prompt_modifier="vivid colors, dramatic, hyper-realistic",
        ),
    ]

    sizes = [
        ImageSizeInfo(
            name="Square",
            dimensions="1024x1024",
            aspect_ratio="1:1",
            provider="openai",
            recommended_for=["social media", "profile images", "thumbnails"],
        ),
        ImageSizeInfo(
            name="Landscape",
            dimensions="1792x1024",
            aspect_ratio="16:9 (approx)",
            provider="openai",
            recommended_for=["featured images", "hero banners", "blog headers"],
        ),
        ImageSizeInfo(
            name="Portrait",
            dimensions="1024x1792",
            aspect_ratio="9:16 (approx)",
            provider="openai",
            recommended_for=["mobile-first content", "story formats", "vertical banners"],
        ),
        ImageSizeInfo(
            name="SD Square",
            dimensions="1024x1024",
            aspect_ratio="1:1",
            provider="stability",
            recommended_for=["social media", "general purpose"],
        ),
        ImageSizeInfo(
            name="SD Landscape",
            dimensions="1344x768",
            aspect_ratio="16:9 (approx)",
            provider="stability",
            recommended_for=["blog headers", "featured images"],
        ),
        ImageSizeInfo(
            name="SD Portrait",
            dimensions="768x1344",
            aspect_ratio="9:16 (approx)",
            provider="stability",
            recommended_for=["vertical content", "mobile displays"],
        ),
    ]

    providers = ["openai", "stability"]

    return AvailableStyles(
        styles=styles,
        sizes=sizes,
        providers=providers,
    )


# Health check for image generation service
@router.get("/health")
async def image_service_health():
    """
    Check health of image generation service.

    Returns status of configured providers.
    """
    import os

    openai_configured = bool(os.environ.get("OPENAI_API_KEY"))
    stability_configured = bool(os.environ.get("STABILITY_API_KEY"))

    return {
        "status": "healthy" if (openai_configured or stability_configured) else "degraded",
        "providers": {
            "openai": "configured" if openai_configured else "not_configured",
            "stability": "configured" if stability_configured else "not_configured",
        },
    }
