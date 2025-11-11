"""Common models shared across content types."""

from pydantic import Field, field_validator, model_validator

from .base import ContentModel


class Topic(ContentModel):
    """
    Represents a topic or subtopic in generated content.

    Used across blog posts, books, and other content types to represent
    a single subject area with optional generated content.

    Attributes:
        title: Topic heading (1-200 characters)
        content: Generated content for this topic (optional)
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Topic title or heading",
    )
    content: str | None = Field(
        default=None,
        description="Generated content for this topic",
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_meaningful(cls, v: str | None) -> str | None:
        """Ensure content is meaningful if provided."""
        if v is not None and not v.strip():
            return None  # Convert empty strings to None
        return v.strip() if v else None


class Tag(ContentModel):
    """Represents a tag or category."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tag name",
    )
    slug: str | None = Field(
        default=None,
        description="URL-friendly version of tag name",
    )

    @field_validator("name")
    @classmethod
    def normalize_tag(cls, v: str) -> str:
        """Normalize tag name."""
        return v.strip().lower()

    @model_validator(mode="after")
    def generate_slug_if_needed(self) -> "Tag":
        """Generate slug from name if not provided."""
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-").replace("_", "-")
        return self
