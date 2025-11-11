"""Interactive mode for blog-AI content generation."""

import logging
import sys
from pathlib import Path
from typing import Any

from ..config import settings

try:
    import questionary
    from questionary import Style

    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

logger = logging.getLogger(__name__)


def check_questionary() -> None:
    """Check if questionary is installed."""
    if not QUESTIONARY_AVAILABLE:
        print("❌ Error: questionary is required for interactive mode")
        print("\nInstall it with:")
        print("  uv sync --all-extras")
        print("  or")
        print("  pip install questionary")
        sys.exit(1)


# Custom style
INTERACTIVE_STYLE = Style(
    [
        ("qmark", "fg:#673ab7 bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", "fg:#673ab7 bold"),
        ("highlighted", "fg:#673ab7 bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
        ("disabled", "fg:#858585 italic"),
    ]
)


def generate_blog_interactive() -> dict[str, Any]:
    """Interactive blog generation."""
    print("\n" + "=" * 70)
    print("Blog Post Generation")
    print("=" * 70)

    config: dict[str, Any] = {}

    # Topic
    config["topic"] = questionary.text(
        "What topic would you like to write about?",
        style=INTERACTIVE_STYLE,
    ).ask()

    if not config["topic"]:
        print("❌ Topic is required")
        sys.exit(1)

    # Number of sections
    config["sections"] = int(
        questionary.text(
            "How many sections? (default: 3)",
            default="3",
            style=INTERACTIVE_STYLE,
        ).ask()
    )

    # Output format
    config["format"] = questionary.select(
        "Output format:",
        choices=["markdown", "mdx"],
        default="mdx",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Output filename
    use_custom_name = questionary.confirm(
        "Customize output filename?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if use_custom_name:
        config["output"] = questionary.text(
            "Output filename (without extension):",
            style=INTERACTIVE_STYLE,
        ).ask()

    # LLM Provider
    config["provider"] = questionary.select(
        "LLM provider:",
        choices=["openai", "anthropic"],
        default="openai",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Advanced options
    configure_advanced = questionary.confirm(
        "Configure advanced options?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if configure_advanced:
        config["temperature"] = float(
            questionary.text(
                f"Temperature (0.0-2.0, default: {settings.temperature}):",
                default=str(settings.temperature),
                style=INTERACTIVE_STYLE,
            ).ask()
        )

        config["verbose"] = questionary.confirm(
            "Enable verbose output?",
            default=False,
            style=INTERACTIVE_STYLE,
        ).ask()

    return config


def generate_book_interactive() -> dict[str, Any]:
    """Interactive book generation."""
    print("\n" + "=" * 70)
    print("Book Generation")
    print("=" * 70)

    config: dict[str, Any] = {}

    # Topic
    config["topic"] = questionary.text(
        "What is your book about?",
        style=INTERACTIVE_STYLE,
    ).ask()

    if not config["topic"]:
        print("❌ Topic is required")
        sys.exit(1)

    # Author
    config["author"] = questionary.text(
        "Author name:",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Subtitle
    add_subtitle = questionary.confirm(
        "Add a subtitle?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if add_subtitle:
        config["subtitle"] = questionary.text(
            "Subtitle:",
            style=INTERACTIVE_STYLE,
        ).ask()

    # Number of chapters
    config["chapters"] = int(
        questionary.text(
            "How many chapters? (default: 11)",
            default="11",
            style=INTERACTIVE_STYLE,
        ).ask()
    )

    # Topics per chapter
    config["topics"] = int(
        questionary.text(
            "Topics per chapter? (default: 4)",
            default="4",
            style=INTERACTIVE_STYLE,
        ).ask()
    )

    # Output filename
    use_custom_name = questionary.confirm(
        "Customize output filename?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if use_custom_name:
        config["output"] = questionary.text(
            "Output filename (without extension):",
            style=INTERACTIVE_STYLE,
        ).ask()

    # LLM Provider
    config["provider"] = questionary.select(
        "LLM provider:",
        choices=["openai", "anthropic"],
        default="openai",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Advanced options
    configure_advanced = questionary.confirm(
        "Configure advanced options?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if configure_advanced:
        config["temperature"] = float(
            questionary.text(
                f"Temperature (0.0-2.0, default: {settings.temperature}):",
                default=str(settings.temperature),
                style=INTERACTIVE_STYLE,
            ).ask()
        )

        config["verbose"] = questionary.confirm(
            "Enable verbose output?",
            default=False,
            style=INTERACTIVE_STYLE,
        ).ask()

    return config


def generate_faq_interactive() -> dict[str, Any]:
    """Interactive FAQ generation."""
    print("\n" + "=" * 70)
    print("FAQ Generation")
    print("=" * 70)

    config: dict[str, Any] = {}

    # Topic
    config["topic"] = questionary.text(
        "What topic is this FAQ about?",
        style=INTERACTIVE_STYLE,
    ).ask()

    if not config["topic"]:
        print("❌ Topic is required")
        sys.exit(1)

    # Number of questions
    config["questions"] = int(
        questionary.text(
            "How many questions? (default: 8)",
            default="8",
            style=INTERACTIVE_STYLE,
        ).ask()
    )

    # Output format
    config["format"] = questionary.select(
        "Output format:",
        choices=["markdown", "html", "both"],
        default="markdown",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Include intro/conclusion
    config["no_intro"] = not questionary.confirm(
        "Include introduction?",
        default=True,
        style=INTERACTIVE_STYLE,
    ).ask()

    config["no_conclusion"] = not questionary.confirm(
        "Include conclusion?",
        default=True,
        style=INTERACTIVE_STYLE,
    ).ask()

    # Output filename
    use_custom_name = questionary.confirm(
        "Customize output filename?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if use_custom_name:
        config["output"] = questionary.text(
            "Output filename (without extension):",
            style=INTERACTIVE_STYLE,
        ).ask()

    # LLM Provider
    config["provider"] = questionary.select(
        "LLM provider:",
        choices=["openai", "anthropic"],
        default="openai",
        style=INTERACTIVE_STYLE,
    ).ask()

    # Advanced options
    configure_advanced = questionary.confirm(
        "Configure advanced options?",
        default=False,
        style=INTERACTIVE_STYLE,
    ).ask()

    if configure_advanced:
        config["temperature"] = float(
            questionary.text(
                f"Temperature (0.0-2.0, default: {settings.temperature}):",
                default=str(settings.temperature),
                style=INTERACTIVE_STYLE,
            ).ask()
        )

        config["verbose"] = questionary.confirm(
            "Enable verbose output?",
            default=False,
            style=INTERACTIVE_STYLE,
        ).ask()

    return config


def run_generation(content_type: str, config: dict[str, Any]) -> int:
    """Run the generation based on content type and config."""
    from ..repositories.file import FileRepository
    from ..services.formatters.docx import DOCXFormatter
    from ..services.formatters.faq_html import FAQHTMLFormatter
    from ..services.formatters.faq_md import FAQMarkdownFormatter
    from ..services.formatters.mdx import MDXFormatter
    from ..services.generators.blog import BlogGenerator
    from ..services.generators.book import BookGenerator
    from ..services.generators.faq import FAQGenerator
    from ..services.llm.openai import OpenAIProvider

    try:
        from ..services.llm.anthropic import AnthropicProvider

        ANTHROPIC_AVAILABLE = True
    except ImportError:
        ANTHROPIC_AVAILABLE = False

    # Initialize LLM provider
    provider = config.get("provider", "openai")

    if provider == "anthropic" and not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic provider not available. Install with: pip install anthropic")
        return 1

    if provider == "openai":
        llm = OpenAIProvider(
            temperature=config.get("temperature"),
            verbose=config.get("verbose", False),
        )
    else:
        llm = AnthropicProvider(
            temperature=config.get("temperature"),
            verbose=config.get("verbose", False),
        )

    repository = FileRepository()

    try:
        if content_type == "blog":
            # Generate blog post
            generator = BlogGenerator(llm_provider=llm, num_sections=config.get("sections", 3))

            print(f"\nGenerating blog post about: {config['topic']}")
            blog = generator.generate(config["topic"])

            # Format and save
            output_format = config.get("format", "mdx")
            formatter = MDXFormatter()
            content = formatter.format(blog)

            # Determine filename
            if config.get("output"):
                filename = f"{config['output']}.{output_format}"
            else:
                filename = f"{blog.metadata.generate_slug()}.{output_format}"

            output_dir = Path(config.get("output_dir", "content/blog"))
            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / filename

            repository.save(content, file_path)

            print("\n" + "=" * 70)
            print("✓ Blog Post Generated Successfully!")
            print("=" * 70)
            print(f"Title: {blog.title}")
            print(f"Sections: {len(blog.sections)}")
            print(f"Word count: {blog.word_count()}")
            print(f"Output: {file_path}")
            print("=" * 70)

        elif content_type == "book":
            # Generate book
            generator = BookGenerator(
                llm_provider=llm,
                num_chapters=config.get("chapters", 11),
                topics_per_chapter=config.get("topics", 4),
            )

            print(f"\nGenerating book about: {config['topic']}")
            book = generator.generate(
                topic=config["topic"],
                author=config.get("author", "Anonymous"),
                subtitle=config.get("subtitle"),
            )

            # Format and save
            formatter = DOCXFormatter()
            content = formatter.format(book)

            # Determine filename
            if config.get("output"):
                filename = f"{config['output']}.docx"
            else:
                filename = f"{book.generate_slug()}.docx"

            output_dir = Path(config.get("output_dir", "content/books"))
            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / filename

            repository.save(content, file_path)

            print("\n" + "=" * 70)
            print("✓ Book Generated Successfully!")
            print("=" * 70)
            print(f"Title: {book.title}")
            print(f"Author: {book.author}")
            print(f"Chapters: {len(book.chapters)}")
            print(f"Word count: {book.word_count()}")
            print(f"Output: {file_path}")
            print("=" * 70)

        elif content_type == "faq":
            # Generate FAQ
            generator = FAQGenerator(
                llm_provider=llm,
                num_questions=config.get("questions", 8),
                include_intro=not config.get("no_intro", False),
                include_conclusion=not config.get("no_conclusion", False),
            )

            print(f"\nGenerating FAQ about: {config['topic']}")
            faq = generator.generate(config["topic"])

            # Format and save
            output_format = config.get("format", "markdown")
            output_dir = Path(config.get("output_dir", "content/faq"))
            output_dir.mkdir(parents=True, exist_ok=True)

            # Determine base filename
            if config.get("output"):
                base_filename = config["output"]
            else:
                base_filename = faq.metadata.generate_slug()

            outputs = []

            if output_format in ["markdown", "both"]:
                formatter = FAQMarkdownFormatter()
                content = formatter.format(faq)
                file_path = output_dir / f"{base_filename}.md"
                repository.save(content, file_path)
                outputs.append(("Markdown", file_path))

            if output_format in ["html", "both"]:
                formatter = FAQHTMLFormatter()
                content = formatter.format(faq)
                file_path = output_dir / f"{base_filename}.html"
                repository.save(content, file_path)
                outputs.append(("HTML", file_path))

            print("\n" + "=" * 70)
            print("✓ FAQ Generated Successfully!")
            print("=" * 70)
            print(f"Title: {faq.metadata.title}")
            print(f"Questions: {len(faq.items)}")
            print(f"Word count: {faq.word_count()}")
            print("Output files:")
            for format_name, path in outputs:
                print(f"  {format_name}: {path}")
            print("=" * 70)

        return 0

    except Exception as e:
        logger.exception(f"Generation error: {e}")
        print(f"\n❌ Error: {e}")
        return 1


def run_interactive() -> int:
    """Run interactive mode."""
    check_questionary()

    print("=" * 70)
    print("blog-AI Interactive Mode")
    print("=" * 70)
    print("\nWelcome! Let's generate some AI-powered content.\n")

    # Select content type
    content_type = questionary.select(
        "What would you like to generate?",
        choices=[
            questionary.Choice("📝 Blog Post", value="blog"),
            questionary.Choice("📚 Book", value="book"),
            questionary.Choice("❓ FAQ", value="faq"),
        ],
        style=INTERACTIVE_STYLE,
    ).ask()

    if not content_type:
        print("\n❌ Cancelled")
        return 1

    # Gather configuration
    if content_type == "blog":
        config = generate_blog_interactive()
    elif content_type == "book":
        config = generate_book_interactive()
    elif content_type == "faq":
        config = generate_faq_interactive()
    else:
        print(f"\n❌ Unknown content type: {content_type}")
        return 1

    # Confirm and generate
    print("\n" + "=" * 70)
    print("Review Configuration")
    print("=" * 70)
    for key, value in config.items():
        print(f"{key}: {value}")
    print("=" * 70)

    confirm = questionary.confirm(
        "\nGenerate content with these settings?",
        default=True,
        style=INTERACTIVE_STYLE,
    ).ask()

    if not confirm:
        print("\n❌ Cancelled")
        return 1

    # Run generation
    return run_generation(content_type, config)


def main() -> int:
    """Main entry point for interactive mode."""
    try:
        return run_interactive()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
