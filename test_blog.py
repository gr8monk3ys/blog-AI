"""Test script for blog generation using new architecture."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import settings
from repositories import FileRepository
from services import BlogGenerator, MDXFormatter, OpenAIProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Test blog generation pipeline."""
    try:
        logger.info("=" * 60)
        logger.info("Testing Blog Generation Pipeline")
        logger.info("=" * 60)

        # Test topic
        topic = "The Future of Artificial Intelligence in Healthcare"
        logger.info(f"\nTopic: {topic}")

        # Initialize components
        logger.info("\n1. Initializing LLM provider...")
        llm = OpenAIProvider()
        logger.info(f"   ✓ Using model: {llm.model_name}")

        logger.info("\n2. Initializing blog generator...")
        generator = BlogGenerator(llm, settings)
        logger.info("   ✓ Generator ready")

        logger.info("\n3. Generating blog structure...")
        blog_post = generator.generate_structure(topic)
        logger.info(f"   ✓ Title: {blog_post.metadata.title}")
        logger.info(f"   ✓ Description: {blog_post.metadata.description}")
        logger.info(f"   ✓ Sections: {len(blog_post.sections)}")
        logger.info(
            f"   ✓ Total subtopics: {sum(len(s.subtopics) for s in blog_post.sections)}"
        )

        logger.info("\n4. Generating content for each section...")
        blog_post = generator.generate_content(blog_post)
        logger.info(f"   ✓ Content generated (~{blog_post.word_count} words)")

        logger.info("\n5. Formatting as MDX...")
        formatter = MDXFormatter()
        mdx_content = formatter.format(blog_post)
        logger.info(f"   ✓ MDX formatted ({len(mdx_content)} chars)")

        logger.info("\n6. Saving to file...")
        repository = FileRepository(settings.get_blog_output_path())
        filename = blog_post.get_safe_filename()
        filepath = repository.save(mdx_content, filename)
        logger.info(f"   ✓ Saved to: {filepath}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Blog generation test COMPLETED successfully!")
        logger.info("=" * 60)
        logger.info(f"\nGenerated blog post:")
        logger.info(f"  Title: {blog_post.metadata.title}")
        logger.info(f"  File: {filepath}")
        logger.info(f"  Word count: ~{blog_post.word_count}")
        logger.info(f"  Sections: {len(blog_post.sections)}")

    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
