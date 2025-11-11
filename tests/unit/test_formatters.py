"""Unit tests for formatters."""

from io import BytesIO

import pytest

from src.models import (
    BlogMetadata,
    BlogPost,
    BlogSection,
    Book,
    Chapter,
    Topic,
)
from src.services.formatters import DOCXFormatter, MDXFormatter


class TestMDXFormatter:
    """Tests for MDX formatter."""

    def test_formatter_properties(self):
        """Test formatter properties."""
        formatter = MDXFormatter()
        assert formatter.output_extension == ".mdx"
        assert formatter.content_type == "text/markdown"

    def test_format_simple_blog(self):
        """Test formatting a simple blog post."""
        post = BlogPost(
            metadata=BlogMetadata(
                title="Test Blog",
                description="Test description",
                date="2024-01-15",
                tags=["test", "blog"],
            ),
            sections=[
                BlogSection(
                    title="Section 1",
                    subtopics=[Topic(title="Topic 1", content="This is the first topic content.")],
                )
            ],
        )

        formatter = MDXFormatter()
        result = formatter.format(post)

        # Check MDX structure
        assert "import { BlogLayout }" in result
        assert "export const meta = {" in result
        assert '"Test Blog"' in result
        assert '"Test description"' in result
        assert '["test", "blog"]' in result
        assert "## Section 1" in result
        assert "This is the first topic content." in result

    def test_format_multiple_sections(self):
        """Test formatting blog with multiple sections."""
        post = BlogPost(
            metadata=BlogMetadata(
                title="Multi-section Blog", description="A blog with multiple sections"
            ),
            sections=[
                BlogSection(
                    title="Introduction", subtopics=[Topic(title="T1", content="Intro content")]
                ),
                BlogSection(
                    title="Main Content",
                    subtopics=[
                        Topic(title="T2", content="Main content 1"),
                        Topic(title="T3", content="Main content 2"),
                    ],
                ),
                BlogSection(
                    title="Conclusion", subtopics=[Topic(title="T4", content="Conclusion content")]
                ),
            ],
        )

        formatter = MDXFormatter()
        result = formatter.format(post)

        assert "## Introduction" in result
        assert "## Main Content" in result
        assert "## Conclusion" in result
        assert "Intro content" in result
        assert "Main content 1" in result
        assert "Main content 2" in result
        assert "Conclusion content" in result

    def test_format_handles_empty_content(self):
        """Test formatter handles topics without content."""
        post = BlogPost(
            metadata=BlogMetadata(title="Test", description="Test"),
            sections=[
                BlogSection(
                    title="Section",
                    subtopics=[
                        Topic(title="Topic with content", content="Content here"),
                        Topic(title="Topic without content"),
                    ],
                )
            ],
        )

        formatter = MDXFormatter()
        result = formatter.format(post)

        assert "Content here" in result
        # Should not crash with empty content

    def test_frontmatter_escaping(self):
        """Test proper escaping in frontmatter."""
        post = BlogPost(
            metadata=BlogMetadata(
                title='Blog with "quotes"', description="Description with 'quotes'"
            ),
            sections=[
                BlogSection(title="Section", subtopics=[Topic(title="Topic", content="Content")])
            ],
        )

        formatter = MDXFormatter()
        result = formatter.format(post)

        # Title and description should be in frontmatter
        assert 'Blog with "quotes"' in result or "Blog with 'quotes'" in result


class TestDOCXFormatter:
    """Tests for DOCX formatter."""

    def test_formatter_properties(self):
        """Test formatter properties."""
        formatter = DOCXFormatter()
        assert formatter.output_extension == ".docx"
        assert "wordprocessingml" in formatter.content_type

    def test_formatter_initialization(self):
        """Test formatter initialization with custom settings."""
        formatter = DOCXFormatter(
            font_name="Times New Roman", font_size=12, line_spacing=1.5, margins=1.5
        )
        assert formatter.font_name == "Times New Roman"
        assert formatter.font_size == 12
        assert formatter.line_spacing == 1.5
        assert formatter.margins == 1.5

    def test_format_simple_book(self):
        """Test formatting a simple book."""
        book = Book(
            title="Test Book",
            chapters=[
                Chapter(
                    number=1,
                    title="Chapter One",
                    topics=[Topic(title="Topic 1", content="This is chapter one content.")],
                )
            ],
        )

        formatter = DOCXFormatter()
        result = formatter.format(book)

        # Should return bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Should be a valid DOCX file (starts with PK for ZIP)
        assert result[:2] == b"PK"

    def test_format_book_with_metadata(self):
        """Test formatting book with author and subtitle."""
        book = Book(
            title="Complete Guide",
            subtitle="A Comprehensive Overview",
            author="John Doe",
            chapters=[
                Chapter(
                    number=1,
                    title="Introduction",
                    topics=[Topic(title="Overview", content="Intro content")],
                )
            ],
        )

        formatter = DOCXFormatter()
        result = formatter.format(book)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_multiple_chapters(self):
        """Test formatting book with multiple chapters."""
        book = Book(
            title="Multi-Chapter Book",
            chapters=[
                Chapter(
                    number=1,
                    title="First Chapter",
                    topics=[Topic(title="T1", content="Chapter 1 content")],
                ),
                Chapter(
                    number=2,
                    title="Second Chapter",
                    topics=[Topic(title="T2", content="Chapter 2 content")],
                ),
                Chapter(
                    number=3,
                    title="Third Chapter",
                    topics=[Topic(title="T3", content="Chapter 3 content")],
                ),
            ],
        )

        formatter = DOCXFormatter()
        result = formatter.format(book)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_handles_paragraph_breaks(self):
        """Test formatter handles paragraph breaks in content."""
        book = Book(
            title="Test",
            chapters=[
                Chapter(
                    number=1,
                    title="Chapter",
                    topics=[
                        Topic(
                            title="Topic",
                            content="First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
                        )
                    ],
                )
            ],
        )

        formatter = DOCXFormatter()
        result = formatter.format(book)

        # Should create valid DOCX with multiple paragraphs
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_returns_bytes_not_document(self):
        """Test that formatter returns bytes, not Document object."""
        book = Book(
            title="Test",
            chapters=[
                Chapter(number=1, title="Ch1", topics=[Topic(title="T1", content="Content")])
            ],
        )

        formatter = DOCXFormatter()
        result = formatter.format(book)

        # Should be bytes, not Document
        assert isinstance(result, bytes)
        assert not hasattr(result, "save")  # Not a Document object
