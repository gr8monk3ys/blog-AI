"""Batch processing CLI commands for blog-AI."""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from ..models.blog import BlogPost
from ..repositories.file import FileRepository
from ..services.formatters.mdx import MDXFormatter
from ..services.generators.blog import BlogGenerator
from ..services.llm.openai import OpenAIProvider
from ..utils.batch import BatchJob, BatchProcessor, create_progress_bar, read_topics_from_file
from ..utils.cache import CacheManager, MemoryCache

try:
    from ..services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


async def batch_generate_blogs(
    topics: list[str],
    output_dir: Path,
    provider: str = "openai",
    max_concurrent: int = 5,
    use_cache: bool = True,
    temperature: float = 0.7,
    verbose: bool = False,
) -> BatchJob[str]:
    """
    Generate multiple blog posts concurrently.

    Args:
        topics: List of blog topics
        output_dir: Output directory for blog posts
        provider: LLM provider ('openai' or 'anthropic')
        max_concurrent: Maximum concurrent generations
        use_cache: Enable response caching
        temperature: LLM temperature
        verbose: Enable verbose output

    Returns:
        Completed batch job
    """
    # Initialize cache
    cache = None
    if use_cache:
        from ..config import settings

        cache = CacheManager(
            backend=MemoryCache(max_size=settings.cache_max_size),
            enabled=True,
            default_ttl=settings.cache_ttl,
        )
        logger.info("Cache enabled")

    # Initialize LLM provider
    if provider == "openai":
        llm = OpenAIProvider(temperature=temperature, verbose=verbose, cache=cache)
    elif provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic provider not available. Install with: pip install anthropic"
            )
        llm = AnthropicProvider(temperature=temperature, verbose=verbose, cache=cache)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    logger.info(f"Using {provider} provider (temperature={temperature})")

    # Initialize components
    generator = BlogGenerator(llm_provider=llm)
    repository = FileRepository()
    formatter = MDXFormatter()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create batch job
    job_id = f"blog_batch_{int(time.time())}"
    job: BatchJob[str] = BatchJob(job_id=job_id)

    for i, topic in enumerate(topics, 1):
        job.add_item(f"blog_{i}", topic)

    # Progress callback
    def on_progress(job: BatchJob) -> None:
        """Print progress update."""
        progress = create_progress_bar(job, width=40)
        print(f"\rProgress: {progress}", end="", flush=True)

    # Create processor
    processor = BatchProcessor[str](
        max_concurrent=max_concurrent,
        max_retries=3,
        state_dir=output_dir / ".batch_state",
    )

    # Process function
    async def process_topic(topic: str) -> BlogPost:
        """Generate and save a blog post."""
        blog_post = await generator.generate_async(topic)

        # Save to file
        content = formatter.format(blog_post)
        file_path = output_dir / f"{blog_post.metadata.slug}.mdx"
        repository.save(content, file_path)

        return blog_post

    # Process batch
    print(f"\n{'=' * 70}")
    print(f"Batch Blog Generation")
    print(f"{'=' * 70}")
    print(f"Topics: {len(topics)}")
    print(f"Provider: {provider}")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Cache: {'enabled' if use_cache else 'disabled'}")
    print(f"Output: {output_dir}")
    print(f"{'=' * 70}\n")

    start_time = time.perf_counter()
    completed_job = await processor.process_batch(job, process_topic, on_progress)
    elapsed = time.perf_counter() - start_time

    # Print summary
    print(f"\n\n{'=' * 70}")
    print("BATCH GENERATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average per post: {elapsed / len(topics):.2f}s" if topics else "N/A")
    print(f"Completed: {completed_job.completed}")
    print(f"Failed: {completed_job.failed}")
    if completed_job.total > 0:
        print(f"Success rate: {completed_job.completed / completed_job.total * 100:.1f}%")

    # Show failed items
    if completed_job.failed > 0:
        print("\nFailed items:")
        for item in completed_job.get_failed_items():
            print(f"  - {item.input}: {item.error}")

    # Show cache stats
    if cache:
        cache_stats = cache.stats()
        print(f"\nCache Statistics:")
        print(f"  Hit rate: {cache_stats['hit_rate']:.1%}")
        print(f"  Total hits: {cache_stats['hits']}")
        print(f"  Total misses: {cache_stats['misses']}")

    print(f"{'=' * 70}\n")

    return completed_job


def main() -> int:
    """Main CLI entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Generate multiple blog posts concurrently from a topics file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "topics_file",
        type=Path,
        help="File containing topics (one per line, # for comments)",
    )

    # Optional arguments
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("content/blog"),
        help="Output directory for blog posts",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use",
    )
    parser.add_argument(
        "-c",
        "--concurrent",
        type=int,
        default=5,
        help="Maximum concurrent generations",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature (0.0-2.0)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable response caching",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s" if not args.verbose else "%(asctime)s - %(levelname)s - %(message)s",
    )

    # Validate arguments
    if args.concurrent < 1:
        print("Error: --concurrent must be at least 1", file=sys.stderr)
        return 1

    if args.concurrent > 20:
        logger.warning(
            "Warning: High concurrency (>20) may hit API rate limits or cause instability"
        )

    if not (0.0 <= args.temperature <= 2.0):
        print("Error: --temperature must be between 0.0 and 2.0", file=sys.stderr)
        return 1

    # Check provider availability
    if args.provider == "anthropic" and not ANTHROPIC_AVAILABLE:
        print(
            "Error: Anthropic provider not available. Install with: pip install anthropic",
            file=sys.stderr,
        )
        return 1

    # Load topics
    try:
        topics = read_topics_from_file(args.topics_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not topics:
        print("Error: No topics found in file", file=sys.stderr)
        return 1

    # Run batch generation
    try:
        asyncio.run(
            batch_generate_blogs(
                topics=topics,
                output_dir=args.output_dir,
                provider=args.provider,
                max_concurrent=args.concurrent,
                use_cache=not args.no_cache,
                temperature=args.temperature,
                verbose=args.verbose,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch generation interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n\n❌ Batch generation failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
