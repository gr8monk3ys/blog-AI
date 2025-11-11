"""Demonstration of caching capabilities for LLM responses.

This script shows how caching can significantly reduce API calls and costs
by storing and reusing previously generated responses.

Usage:
    python examples/cache_demo.py
    python examples/cache_demo.py --runs 3
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm.openai import OpenAIProvider
from src.utils.cache import CacheManager, MemoryCache

logger = logging.getLogger(__name__)


def demo_without_cache(llm: OpenAIProvider, prompts: list[str], runs: int = 2) -> float:
    """Run generation without caching."""
    logger.info("\n" + "=" * 70)
    logger.info("🚫 GENERATION WITHOUT CACHE")
    logger.info("=" * 70)

    start = time.perf_counter()
    api_calls = 0

    for run in range(runs):
        logger.info(f"\n--- Run {run + 1}/{runs} ---")
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"[{i}] Generating: {prompt[:50]}...")
            _ = llm.generate(prompt, max_tokens=100)
            api_calls += 1

    total_time = time.perf_counter() - start

    logger.info(f"\n✅ Completed {api_calls} API calls in {total_time:.2f}s")
    logger.info(f"⏱️  Average time per call: {total_time / api_calls:.2f}s")

    return total_time


def demo_with_cache(
    llm: OpenAIProvider, cache: CacheManager, prompts: list[str], runs: int = 2
) -> tuple[float, dict]:
    """Run generation with caching."""
    logger.info("\n" + "=" * 70)
    logger.info("✅ GENERATION WITH CACHE")
    logger.info("=" * 70)

    # Clear cache to start fresh
    cache.clear()

    start = time.perf_counter()
    api_calls = 0

    for run in range(runs):
        logger.info(f"\n--- Run {run + 1}/{runs} ---")
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"[{i}] Generating: {prompt[:50]}...")

            # Generate (will be cached after first call)
            _ = llm.generate(prompt, max_tokens=100)

            # Count as API call only on first run (subsequent ones are cached)
            if run == 0:
                api_calls += 1

    total_time = time.perf_counter() - start

    # Get cache statistics
    stats = cache.stats()

    logger.info(f"\n✅ Completed with {api_calls} API calls in {total_time:.2f}s")
    logger.info(f"📊 Cache Statistics:")
    logger.info(f"   - Hit Rate: {stats['hit_rate']:.1%}")
    logger.info(f"   - Cache Hits: {stats['hits']}")
    logger.info(f"   - Cache Misses: {stats['misses']}")
    logger.info(f"   - Cache Size: {stats['size']} entries")

    return total_time, stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Demonstrate caching for LLM responses")
    parser.add_argument(
        "--runs",
        type=int,
        default=2,
        help="Number of times to run each prompt (default: 2)",
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

    # Sample prompts
    prompts = [
        "Write a brief paragraph about Python programming.",
        "Write a brief paragraph about data science.",
        "Write a brief paragraph about machine learning.",
    ]

    logger.info("=" * 70)
    logger.info("📊 Caching Performance Demonstration")
    logger.info("=" * 70)
    logger.info(f"📝 Testing with {len(prompts)} prompts")
    logger.info(f"🔁 Running each prompt {args.runs} times")
    logger.info("=" * 70)

    try:
        # Test without cache
        logger.info("\n🔧 Initializing provider WITHOUT cache...")
        llm_no_cache = OpenAIProvider(temperature=0.7, verbose=False)
        time_no_cache = demo_without_cache(llm_no_cache, prompts, args.runs)

        # Small delay between tests
        time.sleep(2)

        # Test with cache
        logger.info("\n🔧 Initializing provider WITH cache...")
        cache = CacheManager(
            backend=MemoryCache(max_size=100),
            enabled=True,
            default_ttl=3600,
        )
        llm_with_cache = OpenAIProvider(temperature=0.7, verbose=False, cache=cache)
        time_with_cache, cache_stats = demo_with_cache(llm_with_cache, cache, prompts, args.runs)

        # Compare results
        logger.info("\n" + "=" * 70)
        logger.info("📈 PERFORMANCE COMPARISON")
        logger.info("=" * 70)
        logger.info(f"Without cache: {time_no_cache:.2f}s")
        logger.info(f"With cache:    {time_with_cache:.2f}s")

        speedup = time_no_cache / time_with_cache if time_with_cache > 0 else 0
        time_saved = time_no_cache - time_with_cache
        cost_savings = (1 - (1 / args.runs)) * 100  # Approximate cost savings

        logger.info(f"\n🎯 Speedup: {speedup:.2f}x faster")
        logger.info(f"⏱️  Time saved: {time_saved:.2f}s ({time_saved / time_no_cache * 100:.1f}%)")
        logger.info(f"💰 Cost savings: ~{cost_savings:.0f}% (fewer API calls)")

        logger.info("\n" + "=" * 70)
        logger.info("💡 KEY INSIGHTS")
        logger.info("=" * 70)
        logger.info("• First generation: API call + caching")
        logger.info("• Subsequent identical prompts: Instant cache retrieval")
        logger.info("• Cache key based on: prompt + model + temperature + max_tokens")
        logger.info("• Perfect for: Regenerating content, testing, development")
        logger.info("• Cost reduction: Only pay for unique generations")
        logger.info("=" * 70)

        return 0

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Demo interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"\n\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
