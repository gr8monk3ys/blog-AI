"""
Book generation module (public API + CLI).
"""

import argparse
import logging

from typing import Optional

from ..post_processing.file_saver import save_book
from ..post_processing.humanizer import humanize_content
from ..post_processing.proofreader import proofread_content
from ..text_generation.core import create_provider_from_env, generate_text
from ..planning.topic_clusters import (
    generate_topic_clusters,
    generate_topic_clusters_with_research,
)
from ..research.web_researcher import conduct_web_research
from ..types.post_processing import OutputFormat, SaveOptions
from .chapters import (
    generate_chapter as _generate_chapter,
    generate_chapter_with_research as _generate_chapter_with_research,
    generate_conclusion_chapter as _generate_conclusion_chapter,
    generate_introduction_chapter as _generate_introduction_chapter,
    generate_introduction_chapter_with_research as _generate_introduction_chapter_with_research,
)
from .errors import BookGenerationError
from .generation import generate_book as _generate_book, generate_book_with_research as _generate_book_with_research
from .processing import post_process_book as _post_process_book
from .sections import (
    generate_conclusion_section,
    generate_introduction_section,
    generate_introduction_section_with_research,
    generate_section,
    generate_section_with_research,
)
from .serialization import load_book_from_json, save_book_to_json, save_book_to_markdown

logger = logging.getLogger(__name__)

__all__ = [
    "BookGenerationError",
    "generate_book",
    "generate_book_with_research",
    "generate_chapter",
    "generate_chapter_with_research",
    "generate_introduction_chapter",
    "generate_introduction_chapter_with_research",
    "generate_conclusion_chapter",
    "generate_introduction_section",
    "generate_introduction_section_with_research",
    "generate_section",
    "generate_section_with_research",
    "generate_conclusion_section",
    "post_process_book",
    "save_book_to_markdown",
    "save_book_to_json",
    "load_book_from_json",
    "generate_text",
    "proofread_content",
    "humanize_content",
    "generate_topic_clusters",
    "generate_topic_clusters_with_research",
    "conduct_web_research",
]


def generate_chapter(*args, **kwargs):
    return _generate_chapter(
        *args,
        **kwargs,
        introduction_section_func=generate_introduction_section,
        section_func=generate_section,
        conclusion_section_func=generate_conclusion_section,
    )


def generate_chapter_with_research(*args, **kwargs):
    return _generate_chapter_with_research(
        *args,
        **kwargs,
        introduction_section_func=generate_introduction_section_with_research,
        section_func=generate_section_with_research,
        conclusion_section_func=generate_conclusion_section,
    )


def generate_introduction_chapter(*args, **kwargs):
    return _generate_introduction_chapter(
        *args,
        **kwargs,
        generate_text_func=generate_text,
    )


def generate_introduction_chapter_with_research(*args, **kwargs):
    return _generate_introduction_chapter_with_research(
        *args,
        **kwargs,
        generate_text_func=generate_text,
    )


def generate_conclusion_chapter(*args, **kwargs):
    return _generate_conclusion_chapter(
        *args,
        **kwargs,
        generate_text_func=generate_text,
    )


def generate_book(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords=None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type="openai",
    options=None,
    concurrent_sections: bool = True,
):
    # Explicit signature for a stable public API (tests rely on this).
    return _generate_book(
        title=title,
        num_chapters=num_chapters,
        sections_per_chapter=sections_per_chapter,
        keywords=keywords,
        tone=tone,
        brand_voice=brand_voice,
        provider_type=provider_type,
        options=options,
        concurrent_sections=concurrent_sections,
        provider_factory=create_provider_from_env,
        topic_cluster_generator=generate_topic_clusters,
        chapter_generator=generate_chapter,
        introduction_chapter_generator=generate_introduction_chapter,
        conclusion_chapter_generator=generate_conclusion_chapter,
    )


def generate_book_with_research(
    title: str,
    num_chapters: int = 5,
    sections_per_chapter: int = 3,
    keywords=None,
    tone: str = "informative",
    brand_voice: Optional[str] = None,
    provider_type="openai",
    options=None,
    concurrent_sections: bool = True,
):
    return _generate_book_with_research(
        title=title,
        num_chapters=num_chapters,
        sections_per_chapter=sections_per_chapter,
        keywords=keywords,
        tone=tone,
        brand_voice=brand_voice,
        provider_type=provider_type,
        options=options,
        concurrent_sections=concurrent_sections,
        provider_factory=create_provider_from_env,
        research_func=conduct_web_research,
        topic_cluster_generator=generate_topic_clusters_with_research,
        chapter_generator=generate_chapter_with_research,
        introduction_chapter_generator=generate_introduction_chapter_with_research,
        conclusion_chapter_generator=generate_conclusion_chapter,
    )


def post_process_book(*args, **kwargs):
    return _post_process_book(
        *args,
        **kwargs,
        proofread_func=proofread_content,
        humanize_func=humanize_content,
    )


def main():
    """
    Main function for the book generation module.
    """
    parser = argparse.ArgumentParser(description="Generate a book")
    parser.add_argument("title", help="The title of the book")
    parser.add_argument("--output", help="The output file path", default="book.md")
    parser.add_argument(
        "--chapters", help="The number of chapters", type=int, default=5
    )
    parser.add_argument(
        "--sections", help="The number of sections per chapter", type=int, default=3
    )
    parser.add_argument(
        "--keywords", help="The keywords to include in the book", nargs="+"
    )
    parser.add_argument("--tone", help="The tone of the book", default="informative")
    parser.add_argument(
        "--research", help="Whether to use research", action="store_true"
    )
    parser.add_argument(
        "--proofread", help="Whether to proofread the book", action="store_true"
    )
    parser.add_argument(
        "--humanize", help="Whether to humanize the book", action="store_true"
    )
    parser.add_argument("--provider", help="The provider to use", default="openai")

    args = parser.parse_args()

    try:
        if args.research:
            book = generate_book_with_research(
                title=args.title,
                num_chapters=args.chapters,
                sections_per_chapter=args.sections,
                keywords=args.keywords,
                tone=args.tone,
                provider_type=args.provider,
            )
        else:
            book = generate_book(
                title=args.title,
                num_chapters=args.chapters,
                sections_per_chapter=args.sections,
                keywords=args.keywords,
                tone=args.tone,
                provider_type=args.provider,
            )

        if args.proofread or args.humanize:
            book = post_process_book(
                book=book,
                proofread=args.proofread,
                humanize=args.humanize,
                provider=create_provider_from_env(args.provider),
            )

        if args.output.endswith(".md"):
            save_book_to_markdown(book, args.output)
        elif args.output.endswith(".json"):
            save_book_to_json(book, args.output)
        else:
            save_options = SaveOptions(
                file_path=args.output, format=OutputFormat.MARKDOWN
            )
            save_book(book, save_options)

        print(f"Book generated successfully: {args.output}")
    except Exception as e:
        print(f"Error generating book: {str(e)}")
        raise


if __name__ == "__main__":
    main()
