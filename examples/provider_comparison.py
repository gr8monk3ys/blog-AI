"""Compare different LLM providers (OpenAI vs Anthropic).

This script demonstrates how to use different LLM providers and compare
their outputs, performance, and capabilities.

Usage:
    python examples/provider_comparison.py
    python examples/provider_comparison.py --topic "Your Topic"
    python examples/provider_comparison.py --providers openai anthropic
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings

logger = logging.getLogger(__name__)


def compare_providers(topic: str, providers: list[str]) -> dict[str, dict[str, any]]:
    """
    Compare different LLM providers on the same prompt.

    Args:
        topic: The topic to generate content about
        providers: List of provider names ("openai", "anthropic")

    Returns:
        Dictionary with results for each provider
    """
    prompt = f"Write a concise 150-word introduction about: {topic}"
    results = {}

    for provider_name in providers:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Testing provider: {provider_name.upper()}")
        logger.info(f"{'=' * 70}")

        try:
            # Initialize provider
            if provider_name == "openai":
                from src.services.llm.openai import OpenAIProvider

                provider = OpenAIProvider(temperature=0.7, verbose=False)
            elif provider_name == "anthropic":
                try:
                    from src.services.llm.anthropic import AnthropicProvider

                    provider = AnthropicProvider(temperature=0.7, verbose=False)
                except ImportError:
                    logger.error(
                        "❌ Anthropic provider requires 'anthropic' package: pip install anthropic"
                    )
                    continue
            else:
                logger.error(f"Unknown provider: {provider_name}")
                continue

            logger.info(f"Using model: {provider.model_name}")

            # Generate content
            start_time = time.perf_counter()
            response = provider.generate(prompt, max_tokens=200)
            elapsed = time.perf_counter() - start_time

            # Store results
            results[provider_name] = {
                "model": provider.model_name,
                "response": response,
                "time": elapsed,
                "word_count": len(response.split()),
                "char_count": len(response),
            }

            logger.info(f"\n✅ Generated in {elapsed:.2f}s")
            logger.info(f"📝 Words: {results[provider_name]['word_count']}")
            logger.info(f"📊 Characters: {results[provider_name]['char_count']}")
            logger.info(f"\n{response}\n")

        except Exception as e:
            logger.error(f"❌ Failed to generate with {provider_name}: {e}")
            results[provider_name] = {"error": str(e)}

    return results


def print_comparison(results: dict[str, dict[str, any]]) -> None:
    """Print a comparison table of results."""
    logger.info("\n" + "=" * 70)
    logger.info("📊 COMPARISON SUMMARY")
    logger.info("=" * 70)

    # Check if we have valid results
    valid_results = {k: v for k, v in results.items() if "error" not in v}

    if not valid_results:
        logger.error("No valid results to compare")
        return

    # Print table header
    logger.info(f"\n{'Metric':<20} | " + " | ".join(f"{k:^15}" for k in valid_results.keys()))
    logger.info("-" * 70)

    # Print metrics
    metrics = ["model", "time", "word_count", "char_count"]
    metric_names = ["Model", "Time (s)", "Words", "Characters"]

    for metric, name in zip(metrics, metric_names):
        values = []
        for provider, data in valid_results.items():
            if metric == "time":
                values.append(f"{data[metric]:.2f}")
            else:
                values.append(str(data[metric]))

        logger.info(f"{name:<20} | " + " | ".join(f"{v:^15}" for v in values))

    # Find fastest
    if len(valid_results) > 1:
        fastest = min(valid_results.items(), key=lambda x: x[1]["time"])
        logger.info(f"\n🏆 Fastest: {fastest[0].upper()} ({fastest[1]['time']:.2f}s)")

        # Calculate speed difference
        times = [v["time"] for v in valid_results.values()]
        speedup = max(times) / min(times)
        logger.info(f"⚡ Speedup: {speedup:.2f}x")

    logger.info("=" * 70)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare different LLM providers"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Artificial Intelligence and Machine Learning",
        help="Topic to generate content about",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["openai"],
        choices=["openai", "anthropic"],
        help="Providers to compare (default: openai)",
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
        format="%(message)s",
    )

    # Check if we can run
    try:
        if "openai" in args.providers:
            if not settings.openai_api_key or len(settings.openai_api_key) < 20:
                logger.error("\n❌ OpenAI API key not configured")
                logger.info("💡 Set OPENAI_API_KEY in .env file")
                return 1

        if "anthropic" in args.providers:
            if not hasattr(settings, "anthropic_api_key") or not settings.anthropic_api_key:
                logger.error("\n❌ Anthropic API key not configured")
                logger.info("💡 Set ANTHROPIC_API_KEY in .env file")
                logger.info("💡 Get your key at: https://console.anthropic.com/settings/keys")
                return 1

    except Exception as e:
        logger.error(f"\n❌ Configuration error: {e}")
        return 1

    # Print header
    logger.info("=" * 70)
    logger.info("🔬 LLM Provider Comparison")
    logger.info("=" * 70)
    logger.info(f"Topic: {args.topic}")
    logger.info(f"Providers: {', '.join(args.providers)}")
    logger.info("=" * 70)

    # Run comparison
    try:
        results = compare_providers(args.topic, args.providers)

        # Print comparison
        print_comparison(results)

        # Print insights
        logger.info("\n💡 INSIGHTS")
        logger.info("=" * 70)
        logger.info("• OpenAI (GPT-4): Generally strong at structured tasks and following instructions")
        logger.info("• Anthropic (Claude): Often more conversational, strong at analysis and reasoning")
        logger.info("• Performance varies by prompt type, complexity, and current API load")
        logger.info("• Both support async for concurrent operations (see examples/async_demo.py)")
        logger.info("=" * 70)

        return 0

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Comparison interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"\n\n❌ Comparison failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
