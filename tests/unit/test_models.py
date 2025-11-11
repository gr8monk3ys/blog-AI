"""Unit tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import (
    BlogMetadata,
    BlogPost,
    BlogSection,
    Book,
    Chapter,
    Tag,
    Topic,
)


class TestTopic:
    """Tests for Topic model."""

    def test_valid_topic(self):
        """Test creating a valid topic."""
        topic = Topic(title="Introduction to AI")
        assert topic.title == "Introduction to AI"
        assert topic.content is None

    def test_topic_with_content(self):
        """Test topic with content."""
        topic = Topic(title="Machine Learning", content="This is content about ML.")
        assert topic.title == "Machine Learning"
        assert topic.content == "This is content about ML."

    def test_topic_title_validation(self):
        """Test topic title validation."""
        # Empty title should fail
        with pytest.raises(ValidationError):
            Topic(title="")

        # Whitespace-only should fail
        with pytest.raises(ValidationError):
            Topic(title="   ")

        # Too long should fail
        with pytest.raises(ValidationError):
            Topic(title="x" * 201)

    def test_topic_content_cleaning(self):
        """Test content is cleaned properly."""
        topic = Topic(title="Test", content="   content   ")
        assert topic.content == "content"

        # Empty content becomes None
        topic = Topic(title="Test", content="   ")
        assert topic.content is None


class TestTag:
    """Tests for Tag model."""

    def test_valid_tag(self):
        """Test creating a valid tag."""
        tag = Tag(name="AI")
        assert tag.name == "ai"  # Should be normalized to lowercase
        assert tag.slug == "ai"

    def test_tag_slug_generation(self):
        """Test automatic slug generation."""
        tag = Tag(name="Machine Learning")
        assert tag.name == "machine learning"
        assert tag.slug == "machine-learning"

    def test_custom_slug(self):
        """Test providing custom slug."""
        tag = Tag(name="AI", slug="artificial-intelligence")
        assert tag.slug == "artificial-intelligence"


class TestBlogMetadata:
    """Tests for BlogMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid blog metadata."""
        metadata = BlogMetadata(title="Test Blog", description="A test blog post")
        assert metadata.title == "Test Blog"
        assert metadata.description == "A test blog post"
        assert metadata.date  # Should have default date
        assert metadata.image == "/images/blog/default.jpg"
        assert metadata.tags == ["AI", "technology"]

    def test_metadata_strips_quotes(self):
        """Test that quotes are stripped from title/description."""
        metadata = BlogMetadata(title='"Test Blog"', description="'A description'")
        assert metadata.title == "Test Blog"
        assert metadata.description == "A description"

    def test_metadata_date_validation(self):
        """Test date format validation."""
        # Valid date
        metadata = BlogMetadata(title="Test", description="Test", date="2024-01-15")
        assert metadata.date == "2024-01-15"

        # Invalid date format should fail
        with pytest.raises(ValidationError):
            BlogMetadata(title="Test", description="Test", date="15-01-2024")

    def test_metadata_description_length(self):
        """Test description length validation."""
        # Valid length (160 chars)
        desc = "x" * 160
        metadata = BlogMetadata(title="Test", description=desc)
        assert len(metadata.description) == 160

        # Too long should fail
        with pytest.raises(ValidationError):
            BlogMetadata(title="Test", description="x" * 161)

    def test_metadata_tags_normalization(self):
        """Test tags are normalized to lowercase."""
        metadata = BlogMetadata(
            title="Test", description="Test", tags=["AI", "Machine Learning", "Python"]
        )
        assert metadata.tags == ["ai", "machine learning", "python"]


class TestBlogSection:
    """Tests for BlogSection model."""

    def test_valid_section(self):
        """Test creating a valid blog section."""
        section = BlogSection(
            title="Introduction",
            subtopics=[Topic(title="What is AI?"), Topic(title="Why AI matters")],
        )
        assert section.title == "Introduction"
        assert len(section.subtopics) == 2

    def test_section_requires_subtopics(self):
        """Test section requires at least one subtopic."""
        with pytest.raises(ValidationError):
            BlogSection(title="Test", subtopics=[])

    def test_section_too_many_subtopics(self):
        """Test section subtopic limit."""
        subtopics = [Topic(title=f"Topic {i}") for i in range(11)]
        with pytest.raises(ValidationError):
            BlogSection(title="Test", subtopics=subtopics)


class TestBlogPost:
    """Tests for BlogPost model."""

    def test_valid_blog_post(self):
        """Test creating a valid blog post."""
        post = BlogPost(
            metadata=BlogMetadata(title="Test Blog", description="Test description"),
            sections=[BlogSection(title="Section 1", subtopics=[Topic(title="Topic 1")])],
        )
        assert post.title == "Test Blog"
        assert len(post.sections) == 1

    def test_blog_post_requires_sections(self):
        """Test blog post requires at least one section."""
        with pytest.raises(ValidationError):
            BlogPost(metadata=BlogMetadata(title="Test", description="Test"), sections=[])

    def test_blog_post_word_count(self):
        """Test word count calculation."""
        post = BlogPost(
            metadata=BlogMetadata(title="Test", description="Test"),
            sections=[
                BlogSection(
                    title="Section",
                    subtopics=[Topic(title="Topic", content="This is a test with five words")],
                )
            ],
        )
        assert post.word_count == 7  # "This is a test with five words"

    def test_blog_post_safe_filename(self):
        """Test safe filename generation."""
        post = BlogPost(
            metadata=BlogMetadata(title="Test Blog: A Guide!", description="Test"),
            sections=[BlogSection(title="Section", subtopics=[Topic(title="Topic")])],
        )
        filename = post.get_safe_filename()
        assert filename == "test-blog-a-guide.mdx"
        assert " " not in filename
        assert ":" not in filename
        assert "!" not in filename


class TestChapter:
    """Tests for Chapter model."""

    def test_valid_chapter(self):
        """Test creating a valid chapter."""
        chapter = Chapter(number=1, title="Introduction", topics=[Topic(title="Overview")])
        assert chapter.number == 1
        assert chapter.title == "Introduction"
        assert len(chapter.topics) == 1

    def test_chapter_number_validation(self):
        """Test chapter number validation."""
        # Valid range
        chapter = Chapter(number=1, title="Test", topics=[Topic(title="Topic")])
        assert chapter.number == 1

        # Zero should fail
        with pytest.raises(ValidationError):
            Chapter(number=0, title="Test", topics=[Topic(title="Topic")])

        # Too large should fail
        with pytest.raises(ValidationError):
            Chapter(number=101, title="Test", topics=[Topic(title="Topic")])

    def test_chapter_requires_topics(self):
        """Test chapter requires at least one topic."""
        with pytest.raises(ValidationError):
            Chapter(number=1, title="Test", topics=[])

    def test_chapter_word_count(self):
        """Test chapter word count calculation."""
        chapter = Chapter(
            number=1,
            title="Test",
            topics=[
                Topic(title="Topic 1", content="Hello world"),
                Topic(title="Topic 2", content="Foo bar baz"),
            ],
        )
        assert chapter.word_count == 5  # 2 + 3


class TestBook:
    """Tests for Book model."""

    def test_valid_book(self):
        """Test creating a valid book."""
        book = Book(
            title="Test Book",
            chapters=[Chapter(number=1, title="Chapter 1", topics=[Topic(title="Topic 1")])],
        )
        assert book.title == "Test Book"
        assert book.total_chapters == 1
        assert book.total_topics == 1

    def test_book_requires_chapters(self):
        """Test book requires at least one chapter."""
        with pytest.raises(ValidationError):
            Book(title="Test", chapters=[])

    def test_book_output_file_validation(self):
        """Test output file gets .docx extension."""
        book = Book(
            title="Test",
            chapters=[Chapter(number=1, title="Ch1", topics=[Topic(title="T1")])],
            output_file="book",
        )
        assert book.output_file == "book.docx"

        book = Book(
            title="Test",
            chapters=[Chapter(number=1, title="Ch1", topics=[Topic(title="T1")])],
            output_file="book.docx",
        )
        assert book.output_file == "book.docx"

    def test_book_word_count(self):
        """Test book total word count."""
        book = Book(
            title="Test",
            chapters=[
                Chapter(
                    number=1,
                    title="Ch1",
                    topics=[
                        Topic(title="T1", content="One two three"),
                        Topic(title="T2", content="Four five"),
                    ],
                ),
                Chapter(
                    number=2,
                    title="Ch2",
                    topics=[Topic(title="T3", content="Six seven eight nine")],
                ),
            ],
        )
        assert book.word_count == 9  # 3 + 2 + 4

    def test_book_get_chapter_by_number(self):
        """Test getting chapter by number."""
        book = Book(
            title="Test",
            chapters=[
                Chapter(number=1, title="Ch1", topics=[Topic(title="T1")]),
                Chapter(number=2, title="Ch2", topics=[Topic(title="T2")]),
            ],
        )

        chapter = book.get_chapter_by_number(2)
        assert chapter is not None
        assert chapter.number == 2
        assert chapter.title == "Ch2"

        chapter = book.get_chapter_by_number(99)
        assert chapter is None

    def test_book_safe_filename(self):
        """Test safe filename generation."""
        book = Book(
            title="Python Programming: A Guide!",
            chapters=[Chapter(number=1, title="Ch1", topics=[Topic(title="T1")])],
        )
        filename = book.get_safe_filename()
        assert filename == "python-programming-a-guide.docx"
        assert " " not in filename
        assert ":" not in filename
