"""Main CLI entry point for blog-AI."""

import argparse
import sys

from . import blog, book


def create_parser() -> argparse.ArgumentParser:
    """Create main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="blog-ai",
        description="AI-powered content generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  blog          Generate blog posts in MDX format
  book          Generate books in DOCX format

Examples:
  Generate a blog post:
    blog-ai blog "The Future of AI"

  Generate a book:
    blog-ai book "Python Programming" --chapters 5

For help on a specific command:
    blog-ai blog --help
    blog-ai book --help
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute",
        required=True,
    )

    # Add blog subcommand
    subparsers.add_parser(
        "blog",
        help="Generate blog posts",
        parents=[blog.create_parser()],
        add_help=False,
    )

    # Add book subcommand
    subparsers.add_parser(
        "book",
        help="Generate books",
        parents=[book.create_parser()],
        add_help=False,
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args, remaining = parser.parse_known_args()

    # Route to appropriate subcommand
    if args.command == "blog":
        return blog.main(remaining)
    elif args.command == "book":
        return book.main(remaining)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
