"""Pydantic models for blog post generation."""

from datetime import datetime

from pydantic import Field, field_validator

from .base import ContentModel
from .common import Topic


class BlogMetadata(ContentModel):
    """
    Metadata and SEO information for a blog post.

    Attributes:
        title: Blog post title
        description: SEO meta description (max 160 chars for optimal SEO)
        date: Publication date in ISO format
        image: Path or URL to featured image
        tags: List of content tags/categories
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Blog post title",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=160,
        description="SEO meta description",
    )
    date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Publication date (YYYY-MM-DD)",
    )
    image: str = Field(
        default="/images/blog/default.jpg",
        description="Featured image path or URL",
    )
    tags: list[str] = Field(
        default_factory=lambda: ["AI", "technology"],
        description="Content tags",
    )

    @field_validator("title", "description")
    @classmethod
    def strip_quotes(cls, v: str) -> str:
        """Remove surrounding quotes from title and description."""
        return v.strip('"').strip("'").strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase."""
        return [tag.strip().lower() for tag in v if tag.strip()]

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class BlogSection(ContentModel):
    """
    A major section of a blog post containing multiple subtopics.

    Attributes:
        title: Section heading
        subtopics: List of subtopics within this section
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Section title",
    )
    subtopics: list[Topic] = Field(
        default_factory=list,
        min_length=1,
        max_length=10,
        description="Subtopics in this section",
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean and validate section title."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Section title cannot be empty")
        return cleaned


class BlogPost(ContentModel):
    """
    Complete blog post with metadata and content sections.

    Attributes:
        metadata: SEO and publication metadata
        sections: Main content sections
    """

    metadata: BlogMetadata
    sections: list[BlogSection] = Field(
        default_factory=list,
        min_length=1,
        max_length=20,
        description="Blog post sections",
    )

    @property
    def title(self) -> str:
        """Convenience property to access title."""
        return self.metadata.title

    @property
    def word_count(self) -> int:
        """Calculate approximate word count of generated content."""
        count = 0
        for section in self.sections:
            for subtopic in section.subtopics:
                if subtopic.content:
                    count += len(subtopic.content.split())
        return count

    def get_safe_filename(self) -> str:
        """
        Generate a safe filename from the blog title.

        Returns:
            URL-safe filename based on the title
        """
        safe_title = (
            self.metadata.title.lower()
            .replace(" ", "-")
            .replace(":", "")
            .replace("'", "")
            .replace('"', "")
            .replace("?", "")
            .replace("!", "")
            .replace("/", "-")
            .replace("\\", "-")
        )
        # Remove any remaining special characters
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in "-_")
        # Remove consecutive dashes
        while "--" in safe_title:
            safe_title = safe_title.replace("--", "-")
        return f"{safe_title}.mdx"
