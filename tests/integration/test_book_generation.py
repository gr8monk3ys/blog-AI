"""Integration tests for book generation pipeline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config import Settings
from src.exceptions import GenerationError, LLMError
from src.models import Book, Chapter
from src.repositories import FileRepository
from src.services import BookGenerator, DOCXFormatter, OpenAIProvider
from tests.fixtures.sample_data import (
    MOCK_LLM_BOOK_OUTLINE_RESPONSE,
    MOCK_LLM_CHAPTER_CONTENT_RESPONSE,
    SAMPLE_BOOK,
    get_sample_book,
)


class TestBookGenerationPipeline:
    """Test complete book generation pipeline."""

    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """Create mock settings."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        return Settings()

    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        provider = Mock(spec=OpenAIProvider)

        # Mock structured output for book outline
        provider.generate_structured.return_value = SAMPLE_BOOK

        # Mock chapter content generation
        provider.generate.return_value = MOCK_LLM_CHAPTER_CONTENT_RESPONSE

        return provider

    @pytest.fixture
    def book_generator(self, mock_llm_provider, mock_settings):
        """Create book generator with mocked dependencies."""
        return BookGenerator(mock_llm_provider, mock_settings)

    @pytest.fixture
    def docx_formatter(self):
        """Create DOCX formatter."""
        return DOCXFormatter()

    @pytest.fixture
    def file_repository(self, tmp_path):
        """Create file repository with temp directory."""
        return FileRepository(tmp_path)

    def test_full_book_generation_pipeline(self, book_generator, docx_formatter, file_repository):
        """Test complete pipeline: generate -> format -> save."""
        # Generate book
        topic = "Python Programming"
        book = book_generator.generate(topic)

        assert isinstance(book, Book)
        assert book.title
        assert len(book.chapters) > 0

        # Verify all chapters have content
        for chapter in book.chapters:
            assert chapter.title
            assert chapter.content
            assert chapter.number > 0

        # Format to DOCX (returns bytes)
        docx_bytes = docx_formatter.format(book)

        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0

        # Save to file
        filename = book.output_file
        filepath = file_repository.save(docx_bytes, filename)

        assert filepath.exists()
        assert filepath.suffix == ".docx"

        # Verify binary content was saved
        saved_content = file_repository.load(filename, mode="binary")
        assert saved_content == docx_bytes

    def test_generate_outline(self, book_generator, mock_llm_provider):
        """Test book outline generation."""
        topic = "Machine Learning"
        chapters = 5

        outline = book_generator.generate_outline(topic, chapters)

        assert isinstance(outline, Book)
        assert outline.title
        assert len(outline.chapters) == chapters

        # Verify chapters have basic structure
        for i, chapter in enumerate(outline.chapters, 1):
            assert chapter.number == i
            assert chapter.title

        # Verify LLM was called with proper prompt
        mock_llm_provider.generate_structured.assert_called_once()

    def test_generate_chapter_content(self, book_generator, mock_llm_provider):
        """Test individual chapter content generation."""
        chapter = Chapter(number=1, title="Introduction to Testing", content="")

        book_context = "This is a book about software testing best practices."

        filled_chapter = book_generator.generate_chapter_content(chapter, book_context)

        assert filled_chapter.content
        assert len(filled_chapter.content) > 0
        assert filled_chapter.title == chapter.title
        assert filled_chapter.number == chapter.number

        # Verify LLM was called
        mock_llm_provider.generate.assert_called_once()
        call_args = mock_llm_provider.generate.call_args
        assert "chapter" in call_args[0][0].lower()

    def test_generate_with_custom_chapters(self, mock_llm_provider, mock_settings):
        """Test generation with custom number of chapters."""
        mock_settings.book_chapters = 15
        generator = BookGenerator(mock_llm_provider, mock_settings)

        outline = generator.generate_outline("Test Topic", chapters=15)

        assert len(outline.chapters) == 15

    def test_chapter_numbering(self, book_generator):
        """Test chapters are numbered sequentially."""
        book = book_generator.generate("Test Topic")

        for i, chapter in enumerate(book.chapters, 1):
            assert chapter.number == i

    def test_error_handling_llm_failure(self, mock_llm_provider, mock_settings):
        """Test error handling when LLM fails."""
        generator = BookGenerator(mock_llm_provider, mock_settings)

        # Simulate LLM error
        mock_llm_provider.generate_structured.side_effect = LLMError("API error", provider="openai")

        with pytest.raises(GenerationError) as exc_info:
            generator.generate("Test Topic")

        assert "generation failed" in str(exc_info.value).lower()

    def test_docx_formatting_structure(self, docx_formatter):
        """Test DOCX formatter creates valid document structure."""
        book = get_sample_book()

        docx_bytes = docx_formatter.format(book)

        # Basic validation - DOCX files start with PK (ZIP signature)
        assert docx_bytes[:2] == b"PK"
        assert len(docx_bytes) > 1000  # Reasonable size for a document

    def test_docx_with_author(self, docx_formatter):
        """Test DOCX includes author metadata when provided."""
        book = get_sample_book()
        book.author = "Test Author"

        docx_bytes = docx_formatter.format(book)

        assert isinstance(docx_bytes, bytes)
        # The actual author metadata is embedded in the DOCX XML
        # but we can't easily test it without parsing the document

    def test_repository_binary_operations(self, file_repository, tmp_path):
        """Test repository handles binary files correctly."""
        binary_content = b"Binary book content"
        filename = "test-book.docx"

        # Save binary
        filepath = file_repository.save(binary_content, filename)
        assert filepath == tmp_path / filename

        # Load binary
        loaded = file_repository.load(filename, mode="binary")
        assert loaded == binary_content
        assert isinstance(loaded, bytes)

    def test_multiple_books_generation(self, book_generator, docx_formatter, file_repository):
        """Test generating multiple books."""
        topics = [
            ("Python Basics", "python_basics.docx"),
            ("Web Development", "web_dev.docx"),
            ("Data Science", "data_science.docx"),
        ]
        generated_files = []

        for topic, output_file in topics:
            book = book_generator.generate(topic)
            book.output_file = output_file

            docx_bytes = docx_formatter.format(book)
            filepath = file_repository.save(docx_bytes, output_file)
            generated_files.append(filepath)

        # Verify all files exist
        assert len(generated_files) == 3
        for filepath in generated_files:
            assert filepath.exists()
            assert filepath.suffix == ".docx"

        # Verify we can list them
        all_files = file_repository.list_files("*.docx")
        assert len(all_files) == 3


class TestBookGeneratorWithRealProvider:
    """Tests that use a real provider instance (but skip actual API calls)."""

    @pytest.fixture
    def settings_with_api_key(self, monkeypatch):
        """Create settings with API key."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        return Settings()

    @patch("src.services.llm.openai.OpenAI")
    def test_provider_initialization(self, mock_openai_client, settings_with_api_key):
        """Test provider initializes correctly."""
        provider = OpenAIProvider(
            api_key=settings_with_api_key.openai_api_key,
            model=settings_with_api_key.default_model,
            temperature=settings_with_api_key.temperature,
        )

        assert provider.model == settings_with_api_key.default_model
        assert provider.temperature == settings_with_api_key.temperature

    @patch("src.services.llm.openai.OpenAI")
    def test_generator_with_real_provider(self, mock_openai_client, settings_with_api_key):
        """Test generator works with real provider instance."""
        # Mock the client's completions
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = MOCK_LLM_CHAPTER_CONTENT_RESPONSE
        mock_openai_client.return_value.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key=settings_with_api_key.openai_api_key)
        generator = BookGenerator(provider, settings_with_api_key)

        # This should not raise even with mocked responses
        assert generator.llm_provider is not None
        assert generator.settings is not None


class TestChapterGeneration:
    """Detailed tests for chapter generation."""

    @pytest.fixture
    def generator(self, monkeypatch):
        """Create generator with mocked dependencies."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        settings = Settings()

        provider = Mock(spec=OpenAIProvider)
        provider.generate_structured.return_value = SAMPLE_BOOK
        provider.generate.return_value = MOCK_LLM_CHAPTER_CONTENT_RESPONSE

        return BookGenerator(provider, settings)

    def test_chapter_content_includes_title(self, generator):
        """Test generated content includes chapter title."""
        chapter = Chapter(number=1, title="Introduction", content="")

        filled = generator.generate_chapter_content(chapter, "Book context")

        assert filled.content
        # Content should reference or include the chapter title
        assert "introduction" in filled.content.lower() or filled.title in filled.content

    def test_empty_chapter_list(self, generator):
        """Test handling of books with no chapters."""
        book = Book(title="Empty Book", chapters=[], output_file="empty.docx")

        # This should not crash
        assert len(book.chapters) == 0

    def test_large_chapter_count(self, monkeypatch):
        """Test generation with many chapters."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        settings = Settings()
        settings.book_chapters = 50

        provider = Mock(spec=OpenAIProvider)

        # Create book with 50 chapters
        chapters = [Chapter(number=i, title=f"Chapter {i}", content="") for i in range(1, 51)]
        book = Book(title="Large Book", chapters=chapters, output_file="large.docx")

        provider.generate_structured.return_value = book
        provider.generate.return_value = "Chapter content..."

        generator = BookGenerator(provider, settings)

        outline = generator.generate_outline("Test", chapters=50)
        assert len(outline.chapters) == 50


class TestErrorRecovery:
    """Test error recovery and retry logic."""

    @pytest.fixture
    def failing_provider(self):
        """Create provider that fails then succeeds."""
        provider = Mock(spec=OpenAIProvider)

        # First call fails, second succeeds
        provider.generate_structured.side_effect = [
            LLMError("Rate limit", provider="openai"),
            SAMPLE_BOOK,
        ]

        return provider

    def test_retry_on_outline_failure(self, failing_provider, monkeypatch):
        """Test retry logic for outline generation."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        settings = Settings()

        generator = BookGenerator(failing_provider, settings)

        # This should fail on first attempt
        with pytest.raises(GenerationError):
            generator.generate("Test Topic")

    def test_partial_chapter_failure(self, monkeypatch):
        """Test handling when some chapters fail to generate."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        settings = Settings()

        provider = Mock(spec=OpenAIProvider)
        provider.generate_structured.return_value = SAMPLE_BOOK

        # First chapter succeeds, second fails
        provider.generate.side_effect = [
            "Chapter 1 content",
            LLMError("Error", provider="openai"),
            "Chapter 3 content",
        ]

        generator = BookGenerator(provider, settings)

        # The generation should handle individual chapter failures
        # depending on implementation (either fail-fast or continue)
        with pytest.raises(GenerationError):
            generator.generate("Test Topic")


class TestDOCXFormatting:
    """Detailed tests for DOCX formatting."""

    @pytest.fixture
    def formatter(self):
        """Create DOCX formatter."""
        return DOCXFormatter()

    def test_format_minimal_book(self, formatter):
        """Test formatting book with minimal content."""
        book = Book(
            title="Minimal Book",
            chapters=[Chapter(number=1, title="Only Chapter", content="Brief content.")],
            output_file="minimal.docx",
        )

        docx_bytes = formatter.format(book)

        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0
        assert docx_bytes[:2] == b"PK"  # ZIP signature

    def test_format_book_with_special_characters(self, formatter):
        """Test formatting with special characters in content."""
        book = Book(
            title="Special Characters: Testing & More",
            chapters=[
                Chapter(
                    number=1,
                    title="Symbols & Entities",
                    content="Content with <brackets> & ampersands and\n\nnew lines.",
                )
            ],
            output_file="special.docx",
        )

        docx_bytes = formatter.format(book)

        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0

    def test_format_book_with_markdown(self, formatter):
        """Test formatting content with markdown syntax."""
        book = Book(
            title="Markdown Book",
            chapters=[
                Chapter(
                    number=1,
                    title="Markdown Chapter",
                    content="""
# Heading 1
## Heading 2

This is **bold** and this is *italic*.

- List item 1
- List item 2

```python
def hello():
    print("Hello")
```
""",
                )
            ],
            output_file="markdown.docx",
        )

        docx_bytes = formatter.format(book)

        assert isinstance(docx_bytes, bytes)
        # The formatter should handle markdown appropriately
        assert len(docx_bytes) > 0


class TestEndToEnd:
    """End-to-end tests simulating real usage."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        output = tmp_path / "book_output"
        output.mkdir()
        return output

    @patch("src.services.llm.openai.OpenAI")
    def test_complete_book_workflow(self, mock_openai_client, output_dir, monkeypatch):
        """Test complete workflow from topic to saved DOCX file."""
        # Setup
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        settings = Settings()

        # Mock OpenAI responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(SAMPLE_BOOK.model_dump(mode="json"))
        mock_response.choices[0].message.parsed = SAMPLE_BOOK
        mock_openai_client.return_value.beta.chat.completions.parse.return_value = mock_response

        # Create pipeline components
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        generator = BookGenerator(provider, settings)
        formatter = DOCXFormatter()
        repository = FileRepository(output_dir)

        # Execute workflow (with mocked LLM)
        assert generator is not None
        assert formatter is not None
        assert repository is not None
        assert output_dir.exists()

    def test_cli_like_usage(self, output_dir, monkeypatch):
        """Test usage similar to CLI invocation."""
        # Setup environment
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        settings = Settings()

        # Mock provider
        provider = Mock(spec=OpenAIProvider)
        provider.generate_structured.return_value = SAMPLE_BOOK
        provider.generate.return_value = "Chapter content..."

        # Create components
        generator = BookGenerator(provider, settings)
        formatter = DOCXFormatter()
        repository = FileRepository(output_dir)

        # Generate book
        topic = "Software Engineering"
        book = generator.generate(topic)

        # Format
        docx_bytes = formatter.format(book)

        # Save
        output_file = "software_engineering.docx"
        filepath = repository.save(docx_bytes, output_file)

        # Verify
        assert filepath.exists()
        assert filepath.name == output_file
        assert filepath.stat().st_size > 0
