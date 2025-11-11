"""Demonstration of async/await capabilities for concurrent LLM generation.

This script shows how async methods can significantly improve performance
when generating multiple pieces of content concurrently.

Usage:
    python examples/async_demo.py
    python examples/async_demo.py --topics 5
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm.openai import OpenAIProvider

logger = logging.getLogger(__name__)


async def generate_single_topic_async(llm: OpenAIProvider, topic: str, index: int) -> str:
    """Generate content for a single topic asynchronously."""
    prompt = f"Write a brief 100-word paragraph about: {topic}"
    logger.info(f"[{index}] Starting generation for: {topic}")

    start = time.perf_counter()
    response = await llm.generate_async(prompt, max_tokens=150)
    elapsed = time.perf_counter() - start

    logger.info(f"[{index}] Completed in {elapsed:.2f}s: {topic}")
    return response


def generate_single_topic_sync(llm: OpenAIProvider, topic: str, index: int) -> str:
    """Generate content for a single topic synchronously."""
    prompt = f"Write a brief 100-word paragraph about: {topic}"
    logger.info(f"[{index}] Starting generation for: {topic}")

    start = time.perf_counter()
    response = llm.generate(prompt, max_tokens=150)
    elapsed = time.perf_counter() - start

    logger.info(f"[{index}] Completed in {elapsed:.2f}s: {topic}")
    return response


async def benchmark_async(llm: OpenAIProvider, topics: list[str]) -> tuple[list[str], float]:
    """Benchmark async concurrent generation."""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 ASYNC CONCURRENT GENERATION")
    logger.info("=" * 70)

    start = time.perf_counter()

    # Generate all topics concurrently
    tasks = [
        generate_single_topic_async(llm, topic, i + 1) for i, topic in enumerate(topics)
    ]
    results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ Async completed in {total_time:.2f}s")
    logger.info("=" * 70)

    return results, total_time


def benchmark_sync(llm: OpenAIProvider, topics: list[str]) -> tuple[list[str], float]:
    """Benchmark sync sequential generation."""
    logger.info("\n" + "=" * 70)
    logger.info("🐌 SYNC SEQUENTIAL GENERATION")
    logger.info("=" * 70)

    start = time.perf_counter()

    # Generate all topics sequentially
    results = [generate_single_topic_sync(llm, topic, i + 1) for i, topic in enumerate(topics)]

    total_time = time.perf_counter() - start

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ Sync completed in {total_time:.2f}s")
    logger.info("=" * 70)

    return results, total_time


async def main_async(num_topics: int = 3) -> None:
    """Main async function."""
    # Sample topics for generation
    all_topics = [
        "Python asyncio programming",
        "Machine learning fundamentals",
        "Web development best practices",
        "Database optimization techniques",
        "Cloud computing architecture",
        "API design principles",
        "Software testing strategies",
        "DevOps automation",
        "Security best practices",
        "Performance optimization",
    ]

    topics = all_topics[:num_topics]

    logger.info("=" * 70)
    logger.info(f"📊 Async/Await Performance Demonstration")
    logger.info(f"📝 Generating {len(topics)} topics")
    logger.info("=" * 70)
    logger.info("\nTopics:")
    for i, topic in enumerate(topics, 1):
        logger.info(f"  {i}. {topic}")

    # Initialize LLM provider
    logger.info("\n🔧 Initializing OpenAI provider...")
    llm = OpenAIProvider(
        temperature=0.7,
        verbose=False,
    )

    # Benchmark async (concurrent)
    async_results, async_time = await benchmark_async(llm, topics)

    # Benchmark sync (sequential)
    sync_results, sync_time = benchmark_sync(llm, topics)

    # Compare results
    logger.info("\n" + "=" * 70)
    logger.info("📈 PERFORMANCE COMPARISON")
    logger.info("=" * 70)
    logger.info(f"Sync (sequential):  {sync_time:.2f}s")
    logger.info(f"Async (concurrent): {async_time:.2f}s")

    speedup = sync_time / async_time if async_time > 0 else 0
    time_saved = sync_time - async_time

    logger.info(f"\n🎯 Speedup: {speedup:.2f}x faster")
    logger.info(f"⏱️  Time saved: {time_saved:.2f}s ({time_saved / sync_time * 100:.1f}%)")

    logger.info("\n" + "=" * 70)
    logger.info("💡 KEY INSIGHTS")
    logger.info("=" * 70)
    logger.info("• Async allows multiple API calls to run concurrently")
    logger.info("• Sync waits for each API call to complete before starting the next")
    logger.info("• Speedup increases with more concurrent tasks")
    logger.info("• Ideal for generating multiple blog sections or book chapters")
    logger.info("=" * 70)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demonstrate async/await performance for LLM generation"
    )
    parser.add_argument(
        "--topics",
        type=int,
        default=3,
        help="Number of topics to generate (default: 3)",
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

    # Run async demo
    try:
        asyncio.run(main_async(args.topics))
        return 0
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Demo interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"\n\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
