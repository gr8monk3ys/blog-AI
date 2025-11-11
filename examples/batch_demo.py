"""Demonstration of batch processing for multiple content generations.

This script shows how to efficiently generate multiple blog posts concurrently
using the batch processing utilities.

Usage:
    python examples/batch_demo.py
    python examples/batch_demo.py --topics examples/sample_topics.txt
    python examples/batch_demo.py --concurrent 10
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.blog import BlogPost
from src.repositories.file import FileRepository
from src.services.formatters.mdx import MDXFormatter
from src.services.generators.blog import BlogGenerator
from src.services.llm.openai import OpenAIProvider
from src.utils.batch import BatchJob, BatchProcessor, create_progress_bar
from src.utils.cache import CacheManager, MemoryCache

logger = logging.getLogger(__name__)


async def generate_blog_post(topic: str, generator: BlogGenerator) -> BlogPost:
    """Generate a single blog post."""
    logger.info(f"Generating blog post: {topic}")
    return await generator.generate_async(topic)


async def batch_generate_blogs(
    topics: list[str],
    max_concurrent: int = 5,
) -> BatchJob[str]:
    """Generate multiple blog posts concurrently."""
    # Initialize components
    cache = CacheManager(
        backend=MemoryCache(max_size=100),
        enabled=True,
        default_ttl=3600,
    )

    llm = OpenAIProvider(
        temperature=0.7,
        verbose=False,
        cache=cache,
    )

    generator = BlogGenerator(llm_provider=llm)
    repository = FileRepository()
    formatter = MDXFormatter()

    # Create batch job
    job_id = f"blog_batch_{int(time.time())}"
    job: BatchJob[str] = BatchJob(job_id=job_id)

    for i, topic in enumerate(topics, 1):
        job.add_item(f"blog_{i}", topic)

    # Progress callback
    def on_progress(job: BatchJob) -> None:
        """Print progress update."""
        progress = create_progress_bar(job, width=40)
        logger.info(f"Progress: {progress}")

    # Create processor
    processor = BatchProcessor[str](
        max_concurrent=max_concurrent,
        max_retries=3,
        state_dir=Path("content/.batch_state"),
    )

    # Process function
    async def process_topic(topic: str) -> BlogPost:
        """Generate and save a blog post."""
        blog_post = await generate_blog_post(topic, generator)

        # Save to file
        content = formatter.format(blog_post)
        file_path = Path("content/blog") / f"{blog_post.metadata.slug}.mdx"
        repository.save(content, file_path)

        logger.info(f"Saved blog post: {file_path}")
        return blog_post

    # Process batch
    logger.info(f"\n{'=' * 70}")
    logger.info(f"Starting batch generation of {len(topics)} blog posts")
    logger.info(f"Max concurrent: {max_concurrent}")
    logger.info(f"{'=' * 70}\n")

    start_time = time.perf_counter()
    completed_job = await processor.process_batch(job, process_topic, on_progress)
    elapsed = time.perf_counter() - start_time

    # Print summary
    logger.info(f"\n{'=' * 70}")
    logger.info("BATCH GENERATION COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total time: {elapsed:.2f}s")
    logger.info(f"Average per post: {elapsed / len(topics):.2f}s")
    logger.info(f"Completed: {completed_job.completed}")
    logger.info(f"Failed: {completed_job.failed}")
    logger.info(f"Success rate: {completed_job.completed / completed_job.total * 100:.1f}%")

    # Show cache stats
    cache_stats = cache.stats()
    logger.info(f"\nCache Statistics:")
    logger.info(f"  Hit rate: {cache_stats['hit_rate']:.1%}")
    logger.info(f"  Total hits: {cache_stats['hits']}")
    logger.info(f"  Total misses: {cache_stats['misses']}")
    logger.info(f"{'=' * 70}\n")

    return completed_job


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch generate multiple blog posts concurrently"
    )
    parser.add_argument(
        "--topics",
        type=Path,
        help="File containing topics (one per line)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Maximum concurrent generations (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Check API key
    try:
        from src.config.settings import settings

        if not settings.openai_api_key or len(settings.openai_api_key) < 20:
            logger.error("\n❌ OpenAI API key not configured")
            logger.info("\n💡 Set OPENAI_API_KEY in .env file to run this demo")
            return 1
    except Exception as e:
        logger.error(f"\n❌ Configuration error: {e}")
        return 1

    # Get topics
    if args.topics:
        try:
            from src.utils.batch import read_topics_from_file

            topics = read_topics_from_file(args.topics)
        except FileNotFoundError as e:
            logger.error(f"\n❌ {e}")
            return 1
    else:
        # Default topics for demo
        topics = [
            "Python AsyncIO Best Practices",
            "Machine Learning Model Deployment",
            "Cloud Architecture Patterns",
        ]
        logger.info("Using default demo topics (use --topics to specify a file)")

    # Validate concurrent setting
    if args.concurrent < 1:
        logger.error("--concurrent must be at least 1")
        return 1
    if args.concurrent > 20:
        logger.warning("High concurrency may hit API rate limits")

    # Run batch generation
    try:
        asyncio.run(batch_generate_blogs(topics, args.concurrent))
        return 0
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Batch generation interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"\n\n❌ Batch generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
