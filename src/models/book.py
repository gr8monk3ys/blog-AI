"""Pydantic models for book generation."""

from pydantic import Field, field_validator

from .base import ContentModel
from .common import Topic


class Chapter(ContentModel):
    """
    A chapter in a book with multiple topics.

    Attributes:
        number: Chapter number (1-indexed)
        title: Chapter title
        topics: List of topics covered in this chapter
    """

    number: int = Field(
        ...,
        ge=1,
        le=100,
        description="Chapter number",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Chapter title",
    )
    topics: list[Topic] = Field(
        default_factory=list,
        min_length=1,
        max_length=20,
        description="Topics in this chapter",
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean and validate chapter title."""
        cleaned = v.strip().strip('"').strip("'")
        if not cleaned:
            raise ValueError("Chapter title cannot be empty")
        return cleaned

    @property
    def word_count(self) -> int:
        """Calculate approximate word count for this chapter."""
        count = 0
        for topic in self.topics:
            if topic.content:
                count += len(topic.content.split())
        return count


class Book(ContentModel):
    """
    Complete book with title, chapters, and topics.

    Attributes:
        title: Book title
        chapters: List of chapters in the book
        output_file: Filename for the generated document
        author: Optional author name
        subtitle: Optional subtitle
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Book title",
    )
    chapters: list[Chapter] = Field(
        default_factory=list,
        min_length=1,
        max_length=100,
        description="Book chapters",
    )
    output_file: str = Field(
        default="book.docx",
        description="Output filename",
    )
    author: str | None = Field(
        default=None,
        description="Author name",
    )
    subtitle: str | None = Field(
        default=None,
        max_length=200,
        description="Book subtitle",
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Remove quotes and clean title."""
        return v.strip().strip('"').strip("'")

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, v: str) -> str:
        """Ensure output file has .docx extension."""
        if not v.endswith(".docx"):
            return f"{v}.docx"
        return v

    @property
    def total_chapters(self) -> int:
        """Get total number of chapters."""
        return len(self.chapters)

    @property
    def total_topics(self) -> int:
        """Get total number of topics across all chapters."""
        return sum(len(chapter.topics) for chapter in self.chapters)

    @property
    def word_count(self) -> int:
        """Calculate approximate word count for the entire book."""
        return sum(chapter.word_count for chapter in self.chapters)

    def get_chapter_by_number(self, number: int) -> Chapter | None:
        """
        Retrieve a chapter by its number.

        Args:
            number: Chapter number to retrieve

        Returns:
            Chapter if found, None otherwise
        """
        for chapter in self.chapters:
            if chapter.number == number:
                return chapter
        return None

    def get_safe_filename(self) -> str:
        """
        Generate a safe filename from the book title.

        Returns:
            URL-safe filename based on the title
        """
        safe_title = (
            self.title.lower()
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
        return f"{safe_title}.docx"
