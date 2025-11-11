"""CLI for blog post generation."""

import argparse
import logging
import sys

from ..config import settings
from ..exceptions import BlogAIException
from ..repositories import FileRepository
from ..services import BlogGenerator, MDXFormatter, OpenAIProvider
from ..utils.logging import setup_logging

try:
    from ..services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for blog generation."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered blog posts in MDX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate a blog post:
    %(prog)s "The Future of AI in Healthcare"

  Generate with custom output directory:
    %(prog)s "Machine Learning Basics" --output-dir content/posts

  Generate with verbose logging:
    %(prog)s "Python Best Practices" --verbose
        """,
    )

    parser.add_argument(
        "topic",
        type=str,
        help="Topic for the blog post",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory (default: {settings.blog_output_dir})",
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
        "--sections",
        type=int,
        default=None,
        help=f"Number of sections (default: {settings.blog_sections})",
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
    Main entry point for blog generation CLI.

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
        logger.info("Blog Post Generation")
        logger.info("=" * 60)
        logger.info(f"Topic: {args.topic}")

        # Validate topic
        if not args.topic or not args.topic.strip():
            logger.error("Topic cannot be empty")
            return 1

        # Create settings copy with overrides (don't mutate global singleton)
        config = settings
        if args.sections:
            # Create a copy with modified sections
            config = settings.model_copy(update={"blog_sections": args.sections})
            logger.debug(f"Using custom sections: {args.sections}")

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

        logger.info("Initializing blog generator...")
        generator = BlogGenerator(llm, config)

        # Generate structure
        logger.info("Generating blog structure...")
        blog_post = generator.generate_structure(args.topic)
        logger.info(f"Title: {blog_post.metadata.title}")
        logger.info(f"Sections: {len(blog_post.sections)}")

        # Generate content
        logger.info("Generating content...")
        blog_post = generator.generate_content(blog_post)
        logger.info(f"Content generated (~{blog_post.word_count} words)")

        # Format as MDX
        logger.info("Formatting as MDX...")
        formatter = MDXFormatter()
        mdx_content = formatter.format(blog_post)

        # Save to file (unless --no-save)
        if not args.no_save:
            output_dir = args.output_dir or settings.blog_output_dir
            repository = FileRepository(output_dir)
            filename = blog_post.get_safe_filename()
            filepath = repository.save(mdx_content, filename)

            logger.info("=" * 60)
            logger.info("✅ Blog post generated successfully!")
            logger.info("=" * 60)
            logger.info(f"Title: {blog_post.metadata.title}")
            logger.info(f"File: {filepath}")
            logger.info(f"Word count: ~{blog_post.word_count}")
            logger.info(f"Sections: {len(blog_post.sections)}")
        else:
            logger.info("=" * 60)
            logger.info("✅ Blog post generated (not saved)")
            logger.info("=" * 60)
            logger.info(f"Title: {blog_post.metadata.title}")
            logger.info(f"Word count: ~{blog_post.word_count}")

        return 0

    except BlogAIException as e:
        logger.error(f"\n❌ Blog generation failed: {e}")

        # Log exception details if available
        if hasattr(e, "details") and e.details:
            logger.error(f"Details: {e.details}")

        # Provide troubleshooting hints
        logger.info("\n💡 Troubleshooting:")
        logger.info("   • Check your OPENAI_API_KEY in .env file")
        logger.info("   • Verify you have API credits: https://platform.openai.com/usage")
        logger.info("   • Try with --verbose flag for more details")
        logger.info("   • Check rate limits: https://platform.openai.com/docs/guides/rate-limits")

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
