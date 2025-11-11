"""FAQ generation CLI for blog-AI."""

import argparse
import logging
import sys
from pathlib import Path

from ..config import settings
from ..exceptions import GenerationError, ValidationError
from ..models.faq import FAQ
from ..repositories.file import FileRepository
from ..services.formatters.faq_html import FAQHTMLFormatter
from ..services.formatters.faq_md import FAQMarkdownFormatter
from ..services.generators.faq import FAQGenerator
from ..services.llm.openai import OpenAIProvider
from ..utils.logging import setup_logging

try:
    from ..services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


def main() -> int:
    """Main CLI entry point for FAQ generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive FAQ documents using AI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "topic",
        type=str,
        help="Main topic for the FAQ (e.g., 'Python Programming')",
    )

    # Optional arguments
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename (without extension, will add .md/.html)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("content/faq"),
        help="Output directory for FAQ",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "html", "both"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "-q",
        "--questions",
        type=int,
        default=8,
        help="Number of questions to generate",
    )
    parser.add_argument(
        "--no-intro",
        action="store_true",
        help="Skip introduction section",
    )
    parser.add_argument(
        "--no-conclusion",
        action="store_true",
        help="Skip conclusion section",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        help=f"Override temperature (default: {settings.temperature})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level)

    # Validate arguments
    if args.questions < 1:
        logger.error("Error: Number of questions must be at least 1")
        return 1

    if args.questions > 50:
        logger.warning("Warning: Generating more than 50 questions may take a long time")

    if args.temperature is not None and not (0.0 <= args.temperature <= 2.0):
        logger.error("Error: Temperature must be between 0.0 and 2.0")
        return 1

    # Validate topic
    if not args.topic or len(args.topic.strip()) < 3:
        logger.error("Error: Topic must be at least 3 characters")
        return 1

    # Check provider availability
    if args.provider == "anthropic" and not ANTHROPIC_AVAILABLE:
        logger.error(
            "Error: Anthropic provider not available. Install with: pip install anthropic"
        )
        return 1

    # Create output directory
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Error: Failed to create output directory: {e}")
        return 1

    # Generate FAQ
    try:
        # Initialize components
        logger.info(f"Initializing {args.provider} provider...")

        if args.provider == "openai":
            llm = OpenAIProvider(
                temperature=args.temperature or settings.temperature,
                verbose=args.verbose,
            )
        else:  # anthropic
            llm = AnthropicProvider(
                temperature=args.temperature or settings.temperature,
                verbose=args.verbose,
            )

        generator = FAQGenerator(
            llm_provider=llm,
            num_questions=args.questions,
            include_intro=not args.no_intro,
            include_conclusion=not args.no_conclusion,
        )

        repository = FileRepository()

        # Generate FAQ
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Generating FAQ: {args.topic}")
        logger.info(f"{'=' * 70}")
        logger.info(f"Questions: {args.questions}")
        logger.info(f"Provider: {args.provider}")
        logger.info(f"Format: {args.format}")
        logger.info(f"{'=' * 70}\n")

        faq: FAQ = generator.generate(args.topic)

        # Generate output filename
        if args.output:
            base_filename = args.output
        else:
            base_filename = faq.metadata.generate_slug()

        # Format and save
        outputs = []

        if args.format in ["markdown", "both"]:
            logger.info("Formatting as Markdown...")
            formatter = FAQMarkdownFormatter()
            content = formatter.format(faq)
            file_path = args.output_dir / f"{base_filename}.md"
            repository.save(content, file_path)
            outputs.append(("Markdown", file_path))

        if args.format in ["html", "both"]:
            logger.info("Formatting as HTML...")
            formatter = FAQHTMLFormatter()
            content = formatter.format(faq)
            file_path = args.output_dir / f"{base_filename}.html"
            repository.save(content, file_path)
            outputs.append(("HTML", file_path))

        # Print summary
        logger.info(f"\n{'=' * 70}")
        logger.info("✓ FAQ GENERATION COMPLETE")
        logger.info(f"{'=' * 70}")
        logger.info(f"Title: {faq.metadata.title}")
        logger.info(f"Questions: {len(faq.items)}")
        logger.info(f"Categories: {', '.join(faq.get_categories())}")
        logger.info(f"Word count: {faq.word_count()}")

        if faq.introduction:
            logger.info("Introduction: Yes")
        if faq.conclusion:
            logger.info("Conclusion: Yes")

        logger.info("\nOutput files:")
        for format_name, path in outputs:
            logger.info(f"  {format_name}: {path}")

        logger.info(f"{'=' * 70}\n")

        return 0

    except ValidationError as e:
        logger.error(f"\n❌ Validation Error: {e}")
        logger.info("\n💡 Troubleshooting:")
        logger.info("   1. Try regenerating with a different temperature")
        logger.info("   2. Check that your topic is clear and specific")
        logger.info("   3. Enable verbose mode (-v) for more details")
        return 1

    except GenerationError as e:
        logger.error(f"\n❌ Generation Error: {e}")
        logger.info("\n💡 Troubleshooting:")
        logger.info("   1. Check your API key is valid and has credits")
        logger.info("   2. Verify your internet connection")
        logger.info("   3. Try with a smaller number of questions")
        logger.info(f"   4. Try a different provider (--provider {'anthropic' if args.provider == 'openai' else 'openai'})")
        return 1

    except Exception as e:
        logger.exception(f"\n❌ Unexpected Error: {e}")
        logger.info("\n💡 Please report this issue with the full error log")
        return 1


if __name__ == "__main__":
    sys.exit(main())
