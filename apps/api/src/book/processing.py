"""
Post-processing helpers for books.
"""

import logging
from typing import Optional

from ..post_processing.humanizer import humanize_content
from ..post_processing.proofreader import proofread_content
from ..text_generation.core import GenerationOptions, LLMProvider, TextGenerationError
from ..types.content import Book, Chapter, Topic
from .errors import BookGenerationError

logger = logging.getLogger(__name__)


def post_process_book(
    book: Book,
    proofread: bool = True,
    humanize: bool = True,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None,
    proofread_func=proofread_content,
    humanize_func=humanize_content,
) -> Book:
    """
    Post-process a book.
    """
    try:
        processed_book = Book(title=book.title, chapters=[])

        for i, chapter in enumerate(book.chapters):
            processed_topics = []
            for topic in chapter.topics:
                processed_topic = Topic(title=topic.title, content=topic.content)

                if topic.content:
                    if proofread:
                        proofreading_result = proofread_func(
                            topic.content, provider=provider, options=options
                        )
                        if proofreading_result.corrected_text:
                            processed_topic.content = proofreading_result.corrected_text

                    if humanize:
                        processed_topic.content = humanize_func(
                            processed_topic.content, provider=provider, options=options
                        )

                processed_topics.append(processed_topic)

            processed_chapter = Chapter(
                number=i, title=chapter.title, topics=processed_topics
            )
            processed_book.chapters.append(processed_chapter)

        return processed_book
    except TextGenerationError as e:
        raise BookGenerationError(f"Failed during post-processing: {str(e)}") from e
    except ValueError as e:
        raise BookGenerationError(f"Invalid parameters during post-processing: {str(e)}") from e
    except AttributeError as e:
        raise BookGenerationError(
            f"Invalid data structure during post-processing: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error post-processing book: %s", str(e), exc_info=True)
        raise BookGenerationError(f"Unexpected error post-processing book: {str(e)}") from e
