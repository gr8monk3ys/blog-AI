"""Demonstration of FAQ generation capabilities.

This script shows how to generate comprehensive FAQ documents
for various topics using different providers and formats.

Usage:
    python examples/faq_demo.py
    python examples/faq_demo.py --provider anthropic
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.faq import FAQ
from src.repositories.file import FileRepository
from src.services.formatters.faq_html import FAQHTMLFormatter
from src.services.formatters.faq_md import FAQMarkdownFormatter
from src.services.generators.faq import FAQGenerator
from src.services.llm.openai import OpenAIProvider

logger = logging.getLogger(__name__)


def demo_faq_generation(provider: str = "openai") -> None:
    """Demonstrate FAQ generation."""
    # Sample topics
    topics = [
        "Python Programming Basics",
        "Machine Learning Fundamentals",
        "Web Development with React",
    ]

    print("=" * 70)
    print("FAQ Generation Demonstration")
    print("=" * 70)
    print(f"Provider: {provider}")
    print(f"Topics: {len(topics)}")
    print("=" * 70)
    print()

    # Initialize LLM provider
    print(f"🔧 Initializing {provider} provider...")
    if provider == "openai":
        llm = OpenAIProvider(temperature=0.7, verbose=False)
    else:
        try:
            from src.services.llm.anthropic import AnthropicProvider

            llm = AnthropicProvider(temperature=0.7, verbose=False)
        except ImportError:
            print("❌ Anthropic provider not available")
            print("Install with: pip install anthropic")
            return

    # Initialize components
    generator = FAQGenerator(
        llm_provider=llm,
        num_questions=6,  # Smaller number for demo
        include_intro=True,
        include_conclusion=True,
    )

    repository = FileRepository()
    md_formatter = FAQMarkdownFormatter()
    html_formatter = FAQHTMLFormatter()

    # Generate FAQ for first topic (demo)
    topic = topics[0]
    print(f"\n📝 Generating FAQ for: {topic}")
    print("-" * 70)

    try:
        faq: FAQ = generator.generate(topic)

        print(f"\n✓ FAQ Generated Successfully!")
        print(f"  Title: {faq.metadata.title}")
        print(f"  Questions: {len(faq.items)}")
        print(f"  Categories: {', '.join(faq.get_categories())}")
        print(f"  Word count: {faq.word_count()}")

        # Show sample questions
        print(f"\n📋 Sample Questions:")
        for i, item in enumerate(faq.items[:3], 1):
            print(f"  {i}. {item.question}")
            print(f"     Category: {item.category or 'Uncategorized'}")

        if len(faq.items) > 3:
            print(f"  ... and {len(faq.items) - 3} more questions")

        # Save in both formats
        output_dir = Path("content/faq")
        output_dir.mkdir(parents=True, exist_ok=True)

        slug = faq.metadata.generate_slug()

        # Save Markdown
        md_content = md_formatter.format(faq)
        md_path = output_dir / f"{slug}.md"
        repository.save(md_content, md_path)
        print(f"\n💾 Saved Markdown: {md_path}")

        # Save HTML
        html_content = html_formatter.format(faq)
        html_path = output_dir / f"{slug}.html"
        repository.save(html_content, html_path)
        print(f"💾 Saved HTML: {html_path}")

        # Show formatting preview
        print(f"\n📄 Markdown Preview (first 500 chars):")
        print("-" * 70)
        print(md_content[:500])
        print("...")
        print("-" * 70)

        print(f"\n🎉 Demo completed successfully!")
        print(f"\nView the generated files:")
        print(f"  - Markdown: {md_path}")
        print(f"  - HTML: {html_path}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Demonstrate FAQ generation")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)",
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
            print("\n❌ OpenAI API key not configured")
            print("\n💡 Set OPENAI_API_KEY in .env file to run this demo")
            return 1
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        return 1

    # Run demo
    try:
        demo_faq_generation(args.provider)
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"\n\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
