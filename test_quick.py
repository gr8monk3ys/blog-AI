"""Quick test to verify imports and basic setup."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all imports work."""
    logger.info("Testing imports...")

    try:
        # Test configuration
        from config import settings

        logger.info(f"✓ Config loaded - Model: {settings.default_model}")

        # Test models
        from models import BlogPost, Book, Topic

        logger.info("✓ Models imported")

        # Test exceptions
        from exceptions import BlogAIException, GenerationError, LLMError

        logger.info("✓ Exceptions imported")

        # Test services
        from services import (
            BlogGenerator,
            BookGenerator,
            DOCXFormatter,
            MDXFormatter,
            OpenAIProvider,
        )

        logger.info("✓ Services imported")

        # Test repositories
        from repositories import FileRepository

        logger.info("✓ Repositories imported")

        # Test utilities
        from utils import retry_with_backoff

        logger.info("✓ Utilities imported")

        logger.info("\n✅ All imports successful!")

        # Test creating instances
        logger.info("\nTesting instance creation...")

        llm = OpenAIProvider()
        logger.info(f"✓ LLM provider created: {llm.model_name}")

        blog_gen = BlogGenerator(llm, settings)
        logger.info("✓ Blog generator created")

        book_gen = BookGenerator(llm, settings)
        logger.info("✓ Book generator created")

        mdx_fmt = MDXFormatter()
        logger.info(f"✓ MDX formatter created: {mdx_fmt.output_extension}")

        docx_fmt = DOCXFormatter()
        logger.info(f"✓ DOCX formatter created: {docx_fmt.output_extension}")

        blog_repo = FileRepository(settings.get_blog_output_path())
        logger.info(f"✓ Blog repository created: {blog_repo.base_dir}")

        book_repo = FileRepository(settings.get_book_output_path())
        logger.info(f"✓ Book repository created: {book_repo.base_dir}")

        logger.info("\n✅ All components initialized successfully!")
        logger.info("\n🎉 System is ready for content generation!")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
