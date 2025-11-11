"""CLI for book generation."""

import argparse
import logging
import sys

from ..config import settings
from ..exceptions import BlogAIException
from ..repositories import FileRepository
from ..services import BookGenerator, DOCXFormatter, OpenAIProvider
from ..utils.logging import setup_logging

try:
    from ..services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for book generation."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered books in DOCX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate a book:
    %(prog)s "Python Programming"

  Generate with custom output file:
    %(prog)s "Machine Learning" --output ml-guide.docx

  Generate with custom settings:
    %(prog)s "Web Development" --chapters 5 --topics 3

  Generate with verbose logging:
    %(prog)s "Data Science" --verbose
        """,
    )

    parser.add_argument(
        "topic",
        type=str,
        help="Topic for the book",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="book.docx",
        help="Output filename (default: book.docx)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory (default: {settings.book_output_dir})",
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help=f"OpenAI model to use (default: {settings.default_model})",
    )

    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=None,
        help=f"Generation temperature (default: {settings.temperature})",
    )

    parser.add_argument(
        "--chapters",
        type=int,
        default=None,
        help=f"Number of chapters (default: {settings.book_chapters})",
    )

    parser.add_argument(
        "--topics",
        type=int,
        default=None,
        help=f"Topics per chapter (default: {settings.book_topics_per_chapter})",
    )

    parser.add_argument(
        "--words-per-topic",
        type=int,
        default=None,
        help=f"Target words per topic (default: {settings.book_target_words_per_topic})",
    )

    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Author name to include on title page",
    )

    parser.add_argument(
        "--subtitle",
        type=str,
        default=None,
        help="Book subtitle",
    )

    parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Generate but don't save to file (useful for testing)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for book generation CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    setup_logging(args.verbose)

    try:
        logger.info("=" * 60)
        logger.info("Book Generation")
        logger.info("=" * 60)
        logger.info(f"Topic: {args.topic}")
        logger.info(f"Output: {args.output}")

        # Validate topic
        if not args.topic or not args.topic.strip():
            logger.error("Topic cannot be empty")
            return 1

        # Create settings copy with overrides (don't mutate global singleton)
        config = settings
        updates = {}
        if args.chapters:
            updates["book_chapters"] = args.chapters
            logger.debug(f"Using custom chapters: {args.chapters}")
        if args.topics:
            updates["book_topics_per_chapter"] = args.topics
            logger.debug(f"Using custom topics per chapter: {args.topics}")
        if args.words_per_topic:
            updates["book_target_words_per_topic"] = args.words_per_topic
            logger.debug(f"Using custom words per topic: {args.words_per_topic}")

        if updates:
            config = settings.model_copy(update=updates)

        logger.info(
            f"Settings: {config.book_chapters} chapters, "
            f"{config.book_topics_per_chapter} topics/chapter, "
            f"~{config.book_target_words_per_topic} words/topic"
        )

        # Initialize components
        logger.info("Initializing LLM provider...")
        if args.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                logger.error("Anthropic provider not available")
                logger.info("Install with: uv sync --all-extras")
                logger.info("Or: pip install anthropic")
                return 1
            llm = AnthropicProvider(
                temperature=args.temperature,
                verbose=args.verbose,
            )
        else:
            llm = OpenAIProvider(
                model=args.model,
                temperature=args.temperature,
                verbose=args.verbose,
            )
        logger.info(f"Using provider: {args.provider}")
        logger.info(f"Using model: {llm.model_name}")

        logger.info("Initializing book generator...")
        generator = BookGenerator(llm, config)

        # Generate structure
        logger.info("Generating book structure...")
        book = generator.generate_structure(
            args.topic,
            output_file=args.output,
        )

        # Set optional metadata
        if args.author:
            book.author = args.author
        if args.subtitle:
            book.subtitle = args.subtitle

        logger.info(f"Title: {book.title}")
        logger.info(f"Chapters: {book.total_chapters}")
        logger.info(f"Total topics: {book.total_topics}")

        # Generate content
        logger.info("Generating content...")
        logger.info("(This may take several minutes depending on settings...)")
        book = generator.generate_content(book)
        logger.info(f"Content generated (~{book.word_count} words)")

        # Format as DOCX
        logger.info("Formatting as DOCX...")
        formatter = DOCXFormatter()
        docx_bytes = formatter.format(book)
        logger.info(f"Document formatted ({len(docx_bytes)} bytes)")

        # Save to file (unless --no-save)
        if not args.no_save:
            output_dir = args.output_dir or settings.book_output_dir
            repository = FileRepository(output_dir)
            filepath = repository.save(docx_bytes, book.output_file)

            logger.info("=" * 60)
            logger.info("✅ Book generated successfully!")
            logger.info("=" * 60)
            logger.info(f"Title: {book.title}")
            logger.info(f"File: {filepath}")
            logger.info(f"Word count: ~{book.word_count}")
            logger.info(f"Chapters: {book.total_chapters}")
            logger.info(f"Topics: {book.total_topics}")
            if book.author:
                logger.info(f"Author: {book.author}")
        else:
            logger.info("=" * 60)
            logger.info("✅ Book generated (not saved)")
            logger.info("=" * 60)
            logger.info(f"Title: {book.title}")
            logger.info(f"Word count: ~{book.word_count}")

        return 0

    except BlogAIException as e:
        logger.error(f"\n❌ Book generation failed: {e}")

        # Log exception details if available
        if hasattr(e, "details") and e.details:
            logger.error(f"Details: {e.details}")

        # Provide troubleshooting hints
        logger.info("\n💡 Troubleshooting:")
        logger.info("   • Check your OPENAI_API_KEY in .env file")
        logger.info("   • Verify you have API credits: https://platform.openai.com/usage")
        logger.info("   • Try with --verbose flag for more details")
        logger.info("   • Check rate limits: https://platform.openai.com/docs/guides/rate-limits")
        logger.info("   • Book generation is long-running (may take 10-30 minutes)")

        if args.verbose:
            logger.exception("Full traceback:")
        return 1
    except KeyboardInterrupt:
        logger.info("\n✋ Generation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        logger.info("\n💡 This is a bug. Please report it at:")
        logger.info("   https://github.com/yourusername/blog-ai/issues")
        if args.verbose:
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
