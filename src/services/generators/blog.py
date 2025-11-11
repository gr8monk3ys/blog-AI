"""Blog post generator service."""

import json
import logging

from ...config import Settings
from ...exceptions import GenerationError, ValidationError
from ...models import BlogMetadata, BlogPost, BlogSection, Topic
from ...services.llm.base import LLMProvider
from .base import ContentGenerator

logger = logging.getLogger(__name__)


class BlogGenerator(ContentGenerator[BlogPost]):
    """
    Blog post generator service.

    Generates SEO-optimized blog posts with structured sections
    and subtopics.
    """

    def __init__(self, llm: LLMProvider, config: Settings):
        """Initialize blog generator."""
        super().__init__(llm, config)

    def generate_title(self, topic: str) -> str:
        """
        Generate SEO-optimized blog title.

        Args:
            topic: Blog topic

        Returns:
            Optimized title string

        Raises:
            GenerationError: If title generation fails
        """
        prompt = f"""You are a blog writer and your job is to create an SEO optimized title for a blog post about the following topic: {topic}

Please generate an SEO Optimized Article Title.

Parameters:
Max 10 words & 1 sentence flow
DO NOT put quotes around the title."""

        try:
            title = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
            )
            # Clean title
            return title.strip().strip('"').strip("'")
        except Exception as e:
            raise GenerationError(
                f"Failed to generate blog title: {e}",
                details={"topic": topic},
            ) from e

    def generate_description(self, title: str) -> str:
        """
        Generate SEO-optimized blog description.

        Args:
            title: Blog title

        Returns:
            Meta description (max 160 chars)

        Raises:
            GenerationError: If description generation fails
        """
        prompt = f"""You are a professional blogger. In one to two sentences write a description with optimal SEO in mind about "{title}" """

        try:
            description = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
            )
            # Clean and validate length
            cleaned = description.strip().strip('"').strip("'")
            if len(cleaned) > 160:
                self.logger.warning(
                    f"Description too long ({len(cleaned)} chars), truncating to 160"
                )
                cleaned = cleaned[:157] + "..."
            return cleaned
        except Exception as e:
            raise GenerationError(
                f"Failed to generate blog description: {e}",
                details={"title": title},
            ) from e

    def generate_structure(self, topic: str, **kwargs) -> BlogPost:
        """
        Generate blog post structure with sections and subtopics.

        Args:
            topic: Blog topic
            **kwargs: Additional parameters

        Returns:
            BlogPost with empty content

        Raises:
            GenerationError: If structure generation fails
        """
        try:
            self.logger.info(f"Generating blog structure for: {topic}")

            # Generate title
            title = self.generate_title(topic)
            self.logger.debug(f"Generated title: {title}")

            # Generate description
            description = self.generate_description(title)
            self.logger.debug(f"Generated description: {description}")

            # Generate sections structure
            prompt = f"""Create a blog post structure about {topic}. The blog should have {self.config.blog_sections} main sections, each with {self.config.blog_subtopics_min}-{self.config.blog_subtopics_max} subtopics.
        Return the structure as a JSON object with the following format:
        {{
            "sections": [
                {{
                    "title": "section title",
                    "subtopics": [
                        "subtopic 1",
                        "subtopic 2"
                    ]
                }}
            ]
        }}
        Make sure the sections and subtopics flow logically and cover the topic comprehensively."""

            response = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
            )

            # Parse JSON response
            try:
                # Extract JSON from potential markdown code blocks
                json_text = response.strip()
                logger.debug(f"Raw LLM response (first 500 chars): {json_text[:500]}")

                # Handle markdown code blocks (```json ... ``` or ``` ... ```)
                if json_text.startswith("```"):
                    lines = json_text.split("\n")
                    # Remove first line (```json or ```) and last line (```)
                    if len(lines) >= 3:
                        # Find the actual start of JSON (skip language identifier)
                        start_idx = 1
                        # Find the closing ```
                        end_idx = len(lines) - 1
                        for i in range(len(lines) - 1, 0, -1):
                            if lines[i].strip().startswith("```"):
                                end_idx = i
                                break
                        json_text = "\n".join(lines[start_idx:end_idx])
                    logger.debug(f"Extracted from markdown: {json_text[:200]}")

                structure_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Attempted to parse: {json_text[:1000]}")
                raise ValidationError(
                    f"Failed to parse blog structure JSON: {e}",
                    details={
                        "response": response[:1000],
                        "extracted_json": json_text[:1000],
                        "error": str(e),
                    },
                ) from e

            # Convert to Pydantic models
            sections = []
            for section_data in structure_data["sections"]:
                subtopics = [Topic(title=st) for st in section_data["subtopics"]]
                sections.append(
                    BlogSection(
                        title=section_data["title"],
                        subtopics=subtopics,
                    )
                )

            # Create metadata
            metadata = BlogMetadata(
                title=title,
                description=description,
            )

            # Return blog post structure
            blog_post = BlogPost(
                metadata=metadata,
                sections=sections,
            )

            self.logger.info(
                f"Blog structure created: {len(sections)} sections, "
                f"{sum(len(s.subtopics) for s in sections)} subtopics"
            )

            return blog_post

        except (GenerationError, ValidationError):
            raise
        except Exception as e:
            raise GenerationError(
                f"Unexpected error generating blog structure: {e}",
                details={"topic": topic},
            ) from e

    def generate_content(self, structure: BlogPost, **kwargs) -> BlogPost:
        """
        Generate content for each subtopic in the blog structure.

        Args:
            structure: Blog post structure with empty content
            **kwargs: Additional parameters

        Returns:
            BlogPost with all content filled

        Raises:
            GenerationError: If content generation fails
        """
        try:
            total_subtopics = sum(len(section.subtopics) for section in structure.sections)
            current = 0

            self.logger.info(f"Generating content for {total_subtopics} subtopics")

            for section in structure.sections:
                self.logger.debug(f"Processing section: {section.title}")

                for subtopic in section.subtopics:
                    current += 1
                    self._log_progress(
                        f"Generating content for '{subtopic.title}'",
                        current,
                        total_subtopics,
                    )

                    prompt = f"""Write a detailed, informative paragraph about '{subtopic.title}' as part of the section '{section.title}' in a blog post.
            The content should be engaging, informative, and SEO-optimized.
            Keep paragraphs concise and avoid unnecessary transitions or redundant text.
            Focus on providing value to the reader."""

                    try:
                        content = self.llm.generate_with_memory(
                            prompt=prompt,
                            context=[
                                {
                                    "role": "user",
                                    "content": f"Section: {section.title}",
                                }
                            ],
                            temperature=self.config.temperature,
                        )
                        subtopic.content = content.strip()
                    except Exception as e:
                        self.logger.error(
                            f"Failed to generate content for subtopic '{subtopic.title}': {e}"
                        )
                        raise GenerationError(
                            f"Failed to generate content for subtopic: {e}",
                            details={
                                "section": section.title,
                                "subtopic": subtopic.title,
                            },
                        ) from e

            self.logger.info(f"Content generation complete. Total words: ~{structure.word_count}")
            return structure

        except GenerationError:
            raise
        except Exception as e:
            raise GenerationError(
                f"Unexpected error generating blog content: {e}",
            ) from e
