"""
Book serialization helpers.
"""

import json
import logging
import os
from typing import Any, Dict

from ..types.content import Book, Chapter, Topic
from .errors import BookGenerationError

logger = logging.getLogger(__name__)


def save_book_to_markdown(book: Book, file_path: str) -> None:
    """
    Save a book to a Markdown file.
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        markdown = f"# {book.title}\n\n"

        markdown += "---\n"
        markdown += f"title: {book.title}\n"

        if hasattr(book, "date"):
            markdown += f"date: {book.date}\n"

        if hasattr(book, "tags") and book.tags:
            markdown += f"tags: {', '.join(book.tags)}\n"

        markdown += "---\n\n"

        for chapter in book.chapters:
            markdown += f"## {chapter.title}\n\n"

            sections: Dict[str, list[str]] = {}
            for topic in chapter.topics:
                sections.setdefault(topic.title, []).append(topic.content)

            for section_title, contents in sections.items():
                markdown += f"### {section_title}\n\n"
                for content in contents:
                    if content:
                        markdown += f"{content}\n\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    except PermissionError as e:
        raise BookGenerationError(
            f"Permission denied writing book to Markdown: {str(e)}"
        ) from e
    except OSError as e:
        raise BookGenerationError(
            f"File system error saving book to Markdown: {str(e)}"
        ) from e
    except TypeError as e:
        raise BookGenerationError(
            f"Invalid data type during Markdown serialization: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error saving book to Markdown: %s", str(e), exc_info=True)
        raise BookGenerationError(
            f"Unexpected error saving book to Markdown: {str(e)}"
        ) from e


def save_book_to_json(book: Book, file_path: str) -> None:
    """
    Save a book to a JSON file.
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        book_data: Dict[str, Any] = {"title": book.title, "chapters": []}

        if hasattr(book, "date"):
            book_data["date"] = book.date

        if hasattr(book, "tags") and book.tags:
            book_data["tags"] = book.tags

        for chapter in book.chapters:
            chapter_data = {"number": chapter.number, "title": chapter.title, "topics": []}
            for topic in chapter.topics:
                chapter_data["topics"].append(
                    {"title": topic.title, "content": topic.content}
                )
            book_data["chapters"].append(chapter_data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2)
    except PermissionError as e:
        raise BookGenerationError(
            f"Permission denied writing book to JSON: {str(e)}"
        ) from e
    except OSError as e:
        raise BookGenerationError(
            f"File system error saving book to JSON: {str(e)}"
        ) from e
    except TypeError as e:
        raise BookGenerationError(f"JSON serialization error: {str(e)}") from e
    except Exception as e:
        logger.error("Unexpected error saving book to JSON: %s", str(e), exc_info=True)
        raise BookGenerationError(
            f"Unexpected error saving book to JSON: {str(e)}"
        ) from e


def load_book_from_json(file_path: str) -> Book:
    """
    Load a book from a JSON file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        chapters = []

        for chapter_data in book_data["chapters"]:
            if "topics" in chapter_data:
                topics = []
                for topic_data in chapter_data["topics"]:
                    topic = Topic(
                        title=topic_data["title"], content=topic_data["content"]
                    )
                    topics.append(topic)

                chapter = Chapter(
                    number=chapter_data.get("number", 0),
                    title=chapter_data["title"],
                    topics=topics,
                )
            else:
                topics = []
                for section_data in chapter_data.get("sections", []):
                    for subtopic_data in section_data.get("subtopics", []):
                        topic = Topic(
                            title=section_data["title"],
                            content=subtopic_data.get("content", ""),
                        )
                        topics.append(topic)

                chapter = Chapter(
                    number=0,
                    title=chapter_data["title"],
                    topics=topics,
                )

            chapters.append(chapter)

        book_args = {"title": book_data["title"], "chapters": chapters}
        if "tags" in book_data:
            book_args["tags"] = book_data["tags"]
        if "date" in book_data:
            book_args["date"] = book_data["date"]

        return Book(**book_args)
    except FileNotFoundError as e:
        raise BookGenerationError(f"Book file not found: {file_path}") from e
    except PermissionError as e:
        raise BookGenerationError(
            f"Permission denied reading book from JSON: {str(e)}"
        ) from e
    except json.JSONDecodeError as e:
        raise BookGenerationError(
            f"Invalid JSON format in book file: {str(e)}"
        ) from e
    except KeyError as e:
        raise BookGenerationError(
            f"Missing required field in book JSON: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error loading book from JSON: %s", str(e), exc_info=True)
        raise BookGenerationError(
            f"Unexpected error loading book from JSON: {str(e)}"
        ) from e
