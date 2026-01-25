"""
Type definitions for image generation.

Includes security validation for:
- Content size limits (DoS protection)
- Prompt sanitization (injection protection)
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Security Constants
# =============================================================================

# Patterns that could indicate prompt injection in image prompts
IMAGE_PROMPT_DANGEROUS_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|?(system|user|assistant)\|?>", re.IGNORECASE),
]


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    OPENAI = "openai"
    STABILITY = "stability"


class ImageSize(str, Enum):
    """Supported image sizes."""

    # DALL-E 3 sizes
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"
    PORTRAIT = "1024x1792"

    # Stability AI sizes (SD XL)
    SD_SQUARE = "1024x1024"
    SD_LANDSCAPE = "1344x768"
    SD_PORTRAIT = "768x1344"


class ImageStyle(str, Enum):
    """Image style options for DALL-E 3."""

    NATURAL = "natural"
    VIVID = "vivid"


class ImageQuality(str, Enum):
    """Image quality options for DALL-E 3."""

    STANDARD = "standard"
    HD = "hd"


class ImageType(str, Enum):
    """Types of images for content."""

    FEATURED = "featured"
    SOCIAL = "social"
    INLINE = "inline"
    THUMBNAIL = "thumbnail"
    HERO = "hero"


class ImageResult(BaseModel):
    """Result of an image generation request."""

    url: str = Field(..., description="URL of the generated image")
    prompt_used: str = Field(..., description="The prompt used to generate the image")
    provider: str = Field(..., description="The provider that generated the image")
    size: str = Field(..., description="Size of the generated image")
    style: Optional[str] = Field(None, description="Style applied to the image")
    quality: Optional[str] = Field(None, description="Quality level of the image")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the image was generated",
    )
    revised_prompt: Optional[str] = Field(
        None,
        description="Revised prompt returned by the provider (DALL-E 3 feature)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from the provider",
    )


class ImageGenerationRequest(BaseModel):
    """Request model for image generation with security validation."""

    content: Optional[str] = Field(
        None,
        max_length=50000,
        description="Content to generate image from (blog content, article text, etc.)",
    )
    custom_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Custom prompt to use instead of generating from content",
    )
    image_type: ImageType = Field(
        default=ImageType.FEATURED,
        description="Type of image to generate",
    )
    size: str = Field(
        default="1024x1024",
        max_length=20,
        description="Size of the image to generate",
    )
    style: ImageStyle = Field(
        default=ImageStyle.NATURAL,
        description="Style of the image (DALL-E 3 only)",
    )
    quality: ImageQuality = Field(
        default=ImageQuality.STANDARD,
        description="Quality of the image (DALL-E 3 only)",
    )
    provider: ImageProvider = Field(
        default=ImageProvider.OPENAI,
        description="Image generation provider to use",
    )
    negative_prompt: Optional[str] = Field(
        None,
        max_length=1000,
        description="What to avoid in the image (Stability AI only)",
    )

    @field_validator("custom_prompt")
    @classmethod
    def sanitize_custom_prompt(cls, v):
        """Sanitize custom prompt to prevent injection."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        # Remove control characters
        v = "".join(char for char in v if char.isprintable() or char in "\n ")

        # Check for dangerous patterns
        for pattern in IMAGE_PROMPT_DANGEROUS_PATTERNS:
            if pattern.search(v):
                # Remove the dangerous pattern instead of rejecting
                v = pattern.sub("", v)

        return v.strip() if v.strip() else None

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content field."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        # Remove control characters except newlines
        v = "".join(char for char in v if char.isprintable() or char == "\n")

        return v

    @field_validator("negative_prompt")
    @classmethod
    def sanitize_negative_prompt(cls, v):
        """Sanitize negative prompt."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        # Remove control characters
        v = "".join(char for char in v if char.isprintable() or char == " ")

        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        """Validate image size format."""
        if not v:
            return "1024x1024"
        v = str(v).strip()
        # Must match pattern like "1024x1024"
        if not re.match(r"^\d{3,4}x\d{3,4}$", v):
            raise ValueError("Invalid size format. Expected format: WIDTHxHEIGHT (e.g., 1024x1024)")
        return v


class BlogImageGenerationRequest(BaseModel):
    """Request to generate all images for a blog post with security validation."""

    content: str = Field(
        ...,
        min_length=10,
        max_length=100000,
        description="Full blog content to generate images from",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Blog post title",
    )
    keywords: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Keywords related to the blog content",
    )
    generate_featured: bool = Field(
        default=True,
        description="Generate a featured/hero image",
    )
    generate_social: bool = Field(
        default=True,
        description="Generate social media sharing image",
    )
    inline_count: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of inline images to generate (0-5)",
    )
    provider: ImageProvider = Field(
        default=ImageProvider.OPENAI,
        description="Image generation provider to use",
    )
    style: ImageStyle = Field(
        default=ImageStyle.NATURAL,
        description="Style for all generated images",
    )
    quality: ImageQuality = Field(
        default=ImageQuality.STANDARD,
        description="Quality for all generated images",
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize blog content."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()

        # Remove control characters except newlines
        v = "".join(char for char in v if char.isprintable() or char == "\n")

        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters")

        return v

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v):
        """Sanitize title field."""
        if not v:
            raise ValueError("Title is required")
        v = str(v).strip()

        # Remove control characters
        v = "".join(char for char in v if char.isprintable())

        if not v:
            raise ValueError("Title cannot be empty")

        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        """Validate and sanitize keywords."""
        if not v:
            return []
        validated = []
        for kw in v:
            if not kw:
                continue
            kw = str(kw).strip().lower()
            # Remove non-printable characters
            kw = "".join(char for char in kw if char.isprintable())
            if kw and len(kw) <= 50:
                validated.append(kw)
        return validated[:20]


class BlogImagesResult(BaseModel):
    """Result containing all generated images for a blog post."""

    featured_image: Optional[ImageResult] = Field(
        None,
        description="Featured/hero image for the blog",
    )
    social_image: Optional[ImageResult] = Field(
        None,
        description="Social media sharing image",
    )
    inline_images: List[ImageResult] = Field(
        default_factory=list,
        description="Inline images for the blog content",
    )
    total_generated: int = Field(
        default=0,
        description="Total number of images generated",
    )
    provider_used: str = Field(
        default="",
        description="Provider used for generation",
    )


class ImageStyleInfo(BaseModel):
    """Information about an available image style."""

    name: str
    description: str
    provider: str
    example_prompt_modifier: Optional[str] = None


class ImageSizeInfo(BaseModel):
    """Information about an available image size."""

    name: str
    dimensions: str
    aspect_ratio: str
    provider: str
    recommended_for: List[str] = Field(default_factory=list)


class AvailableStyles(BaseModel):
    """Available styles and sizes for image generation."""

    styles: List[ImageStyleInfo] = Field(default_factory=list)
    sizes: List[ImageSizeInfo] = Field(default_factory=list)
    providers: List[str] = Field(default_factory=list)
