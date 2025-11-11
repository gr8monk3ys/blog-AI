"""Test script for book generation using new architecture."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import settings
from repositories import FileRepository
from services import BookGenerator, DOCXFormatter, OpenAIProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Test book generation pipeline."""
    try:
        logger.info("=" * 60)
        logger.info("Testing Book Generation Pipeline")
        logger.info("=" * 60)

        # Test topic (using smaller settings for testing)
        topic = "Introduction to Python Programming"
        output_file = "test-python-book.docx"

        logger.info(f"\nTopic: {topic}")
        logger.info(f"Output: {output_file}")

        # Override settings for faster testing (fewer chapters)
        original_chapters = settings.book_chapters
        original_topics = settings.book_topics_per_chapter
        settings.book_chapters = 3  # Just 3 chapters for testing
        settings.book_topics_per_chapter = 2  # Just 2 topics per chapter

        logger.info(
            f"\nUsing test settings: {settings.book_chapters} chapters, "
            f"{settings.book_topics_per_chapter} topics/chapter"
        )

        # Initialize components
        logger.info("\n1. Initializing LLM provider...")
        llm = OpenAIProvider()
        logger.info(f"   ✓ Using model: {llm.model_name}")

        logger.info("\n2. Initializing book generator...")
        generator = BookGenerator(llm, settings)
        logger.info("   ✓ Generator ready")

        logger.info("\n3. Generating book structure...")
        book = generator.generate_structure(topic, output_file=output_file)
        logger.info(f"   ✓ Title: {book.title}")
        logger.info(f"   ✓ Chapters: {len(book.chapters)}")
        logger.info(f"   ✓ Total topics: {book.total_topics}")

        logger.info("\n4. Generating content for each chapter...")
        logger.info(
            "   (This may take several minutes depending on API rate limits...)"
        )
        book = generator.generate_content(book)
        logger.info(f"   ✓ Content generated (~{book.word_count} words)")

        logger.info("\n5. Formatting as DOCX...")
        formatter = DOCXFormatter()
        docx_bytes = formatter.format(book)
        logger.info(f"   ✓ DOCX formatted ({len(docx_bytes)} bytes)")

        logger.info("\n6. Saving to file...")
        repository = FileRepository(settings.get_book_output_path())
        filepath = repository.save(docx_bytes, book.output_file)
        logger.info(f"   ✓ Saved to: {filepath}")

        # Restore original settings
        settings.book_chapters = original_chapters
        settings.book_topics_per_chapter = original_topics

        logger.info("\n" + "=" * 60)
        logger.info("✅ Book generation test COMPLETED successfully!")
        logger.info("=" * 60)
        logger.info(f"\nGenerated book:")
        logger.info(f"  Title: {book.title}")
        logger.info(f"  File: {filepath}")
        logger.info(f"  Word count: ~{book.word_count}")
        logger.info(f"  Chapters: {len(book.chapters)}")
        logger.info(f"  Topics: {book.total_topics}")

    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
