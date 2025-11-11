"""Book generator service."""

import json
import logging

from ...config import Settings
from ...exceptions import GenerationError, ValidationError
from ...models import Book, Chapter, Topic
from ...services.llm.base import LLMProvider
from .base import ContentGenerator

logger = logging.getLogger(__name__)


class BookGenerator(ContentGenerator[Book]):
    """
    Book generator service.

    Generates full-length books with chapters and topics.
    """

    def __init__(self, llm: LLMProvider, config: Settings):
        """Initialize book generator."""
        super().__init__(llm, config)

    def generate_title(self, topic: str) -> str:
        """
        Generate book title.

        Args:
            topic: Book topic

        Returns:
            Book title

        Raises:
            GenerationError: If title generation fails
        """
        prompt = f"""Create a compelling and creative book title about {topic}.
The title should be catchy and memorable, but not longer than 8 words.
Return only the title, without quotes or any additional text."""

        try:
            title = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
            )
            return title.strip().strip('"').strip("'")
        except Exception as e:
            raise GenerationError(
                f"Failed to generate book title: {e}",
                details={"topic": topic},
            ) from e

    def generate_structure(self, topic: str, **kwargs) -> Book:
        """
        Generate book structure with chapters and topics.

        Args:
            topic: Book topic
            **kwargs: Additional parameters (output_file, etc.)

        Returns:
            Book with empty content

        Raises:
            GenerationError: If structure generation fails
        """
        try:
            self.logger.info(f"Generating book structure for: {topic}")

            # Generate title
            title = self.generate_title(topic)
            self.logger.debug(f"Generated title: {title}")

            # Generate chapter structure
            prompt = f"""Create a detailed book structure for a book titled '{title}'.
Return the structure as a JSON object with exactly {self.config.book_chapters} chapters, each having exactly {self.config.book_topics_per_chapter} topics.
Use this format:
{{
    "chapters": [
        {{
            "number": 1,
            "title": "chapter title",
            "topics": [
                "topic 1",
                "topic 2",
                "topic 3",
                "topic 4"
            ]
        }}
    ]
}}
Make sure the chapters and topics flow logically and cover the subject comprehensively."""

            response = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
            )

            # Parse JSON response
            try:
                json_text = response.strip()
                if json_text.startswith("```"):
                    lines = json_text.split("\n")
                    json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

                structure_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Failed to parse book structure JSON: {e}",
                    details={"response": response[:500]},
                ) from e

            # Convert to Pydantic models
            chapters = []
            for chapter_data in structure_data["chapters"]:
                topics = [Topic(title=t) for t in chapter_data["topics"]]
                chapters.append(
                    Chapter(
                        number=chapter_data["number"],
                        title=chapter_data["title"],
                        topics=topics,
                    )
                )

            # Create book
            book = Book(
                title=title,
                chapters=chapters,
                output_file=kwargs.get("output_file", "book.docx"),
            )

            self.logger.info(
                f"Book structure created: {len(chapters)} chapters, "
                f"{sum(len(ch.topics) for ch in chapters)} topics"
            )

            return book

        except (GenerationError, ValidationError):
            raise
        except Exception as e:
            raise GenerationError(
                f"Unexpected error generating book structure: {e}",
                details={"topic": topic},
            ) from e

    def generate_content(self, structure: Book, **kwargs) -> Book:
        """
        Generate content for each topic in the book.

        Args:
            structure: Book structure with empty content
            **kwargs: Additional parameters

        Returns:
            Book with all content filled

        Raises:
            GenerationError: If content generation fails
        """
        try:
            total_topics = sum(len(chapter.topics) for chapter in structure.chapters)
            current = 0

            self.logger.info(
                f"Generating content for {total_topics} topics across "
                f"{len(structure.chapters)} chapters"
            )

            for chapter in structure.chapters:
                self.logger.debug(f"Processing Chapter {chapter.number}: {chapter.title}")

                for topic in chapter.topics:
                    current += 1
                    self._log_progress(
                        f"Ch.{chapter.number} - '{topic.title}'",
                        current,
                        total_topics,
                    )

                    prompt = f"""Write a detailed section about '{topic.title}' for chapter '{chapter.title}' of the book '{structure.title}'.
The content should be engaging, informative, and approximately {self.config.book_target_words_per_topic} words.
Focus on providing value to the reader with clear explanations and relevant examples.
Avoid unnecessary transitions or redundant text.
Each paragraph should naturally flow into the next."""

                    try:
                        content = self.llm.generate_with_memory(
                            prompt=prompt,
                            context=[
                                {
                                    "role": "user",
                                    "content": f"Book: {structure.title}, Chapter: {chapter.title}",
                                }
                            ],
                            temperature=0.7,  # Slightly lower for longer content
                        )
                        topic.content = content.strip()

                        word_count = len(content.split())
                        self.logger.debug(f"Generated {word_count} words for '{topic.title}'")

                    except Exception as e:
                        self.logger.error(
                            f"Failed to generate content for topic '{topic.title}': {e}"
                        )
                        raise GenerationError(
                            f"Failed to generate content for topic: {e}",
                            details={
                                "chapter": chapter.title,
                                "topic": topic.title,
                            },
                        ) from e

            self.logger.info(f"Content generation complete. Total words: ~{structure.word_count}")
            return structure

        except GenerationError:
            raise
        except Exception as e:
            raise GenerationError(
                f"Unexpected error generating book content: {e}",
            ) from e
