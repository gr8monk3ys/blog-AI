"""FAQ generator service for blog-AI.

Generates structured FAQ documents with questions, answers, and categories
using LLM providers.
"""

import logging
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from ...config import settings
from ...exceptions import GenerationError, ValidationError
from ...models.faq import FAQ, FAQItem, FAQMetadata
from ...services.llm.base import LLMProvider
from .base import ContentGenerator

logger = logging.getLogger(__name__)


class FAQGenerator(ContentGenerator[FAQ]):
    """
    Generate FAQ documents using LLM providers.

    Generates comprehensive FAQ with:
    - Metadata (title, description, categories)
    - Multiple question-answer pairs
    - Optional introduction and conclusion
    - Organized by categories

    Example:
        >>> generator = FAQGenerator(llm_provider=OpenAIProvider())
        >>> faq = generator.generate("Python Programming Basics")
        >>> print(f"Generated {len(faq.items)} FAQ items")
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        num_questions: int | None = None,
        categories: list[str] | None = None,
        include_intro: bool = True,
        include_conclusion: bool = True,
    ):
        """
        Initialize FAQ generator.

        Args:
            llm_provider: LLM provider for text generation
            num_questions: Number of questions to generate (default: 8)
            categories: Predefined categories (default: auto-generate)
            include_intro: Include introduction section (default: True)
            include_conclusion: Include conclusion section (default: True)
        """
        super().__init__(llm_provider)
        self._num_questions = num_questions or 8
        self._categories = categories
        self._include_intro = include_intro
        self._include_conclusion = include_conclusion

    def generate(self, topic: str) -> FAQ:
        """
        Generate FAQ document for a topic.

        Args:
            topic: Main topic for the FAQ

        Returns:
            Complete FAQ document

        Raises:
            GenerationError: If FAQ generation fails
            ValidationError: If generated content is invalid
        """
        logger.info(f"Generating FAQ for topic: {topic}")

        try:
            # Step 1: Generate structure (metadata + question list)
            logger.info("Step 1/3: Generating FAQ structure...")
            structure = self._generate_structure(topic)

            # Step 2: Generate answers for each question
            logger.info("Step 2/3: Generating detailed answers...")
            items = self._generate_answers(structure)

            # Step 3: Generate introduction and conclusion
            logger.info("Step 3/3: Generating intro and conclusion...")
            intro, conclusion = self._generate_intro_conclusion(topic, items)

            # Build final FAQ
            faq = FAQ(
                metadata=structure["metadata"],
                items=items,
                introduction=intro,
                conclusion=conclusion,
            )

            logger.info(
                f"✓ FAQ generated successfully: {len(faq.items)} Q&A pairs, "
                f"{faq.word_count()} words total"
            )

            return faq

        except (PydanticValidationError, ValidationError) as e:
            logger.error(f"FAQ validation failed: {e}")
            raise ValidationError(
                f"Generated FAQ doesn't match expected structure: {e}",
                details={"topic": topic, "validation_errors": str(e)},
            ) from e
        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            raise GenerationError(
                f"Failed to generate FAQ: {e}",
                details={"topic": topic},
            ) from e

    def _generate_structure(self, topic: str) -> dict[str, Any]:
        """Generate FAQ structure with metadata and question list."""
        prompt = f"""Generate a comprehensive FAQ structure for the topic: "{topic}"

Create {self._num_questions} diverse, high-quality questions that users commonly ask about this topic.
Organize questions into logical categories.

Return ONLY valid JSON in this exact format:
{{
    "metadata": {{
        "title": "FAQ: [Topic]",
        "description": "Brief description of what this FAQ covers",
        "topic": "{topic}",
        "categories": ["Category1", "Category2", "Category3"]
    }},
    "questions": [
        {{
            "question": "Question 1?",
            "category": "Category1"
        }},
        {{
            "question": "Question 2?",
            "category": "Category2"
        }}
    ]
}}

Guidelines:
- Questions should be clear, specific, and commonly asked
- Cover beginner to advanced topics
- Use 3-5 categories for organization
- Questions must end with '?'
- Mix practical, conceptual, and troubleshooting questions
"""

        try:
            response_text = self._llm_provider.generate(
                prompt=prompt,
                temperature=settings.temperature,
            )

            # Parse JSON response
            import json

            response_text = self._extract_json(response_text)
            structure = json.loads(response_text)

            # Validate structure
            if "metadata" not in structure or "questions" not in structure:
                raise ValidationError(
                    "FAQ structure missing required fields",
                    details={"response": response_text[:500]},
                )

            # Create metadata object
            structure["metadata"] = FAQMetadata(**structure["metadata"])

            logger.debug(f"Generated structure with {len(structure['questions'])} questions")
            return structure

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FAQ structure JSON: {e}")
            logger.debug(f"Raw response: {response_text[:1000]}")
            raise ValidationError(
                f"Invalid JSON in FAQ structure: {e}",
                details={"response": response_text[:500]},
            ) from e

    def _generate_answers(self, structure: dict[str, Any]) -> list[FAQItem]:
        """Generate detailed answers for each question."""
        items = []
        questions = structure["questions"]

        for i, q_data in enumerate(questions, 1):
            question = q_data["question"]
            category = q_data.get("category")

            logger.debug(f"Generating answer {i}/{len(questions)}: {question[:50]}...")

            prompt = f"""Answer this FAQ question about "{structure['metadata'].topic}":

Question: {question}

Provide a comprehensive, accurate, and helpful answer.

Guidelines:
- Answer should be 100-200 words
- Be clear, accurate, and actionable
- Use examples when helpful
- Address the question directly
- Maintain professional but friendly tone

Return ONLY the answer text, no JSON or additional formatting.
"""

            try:
                answer = self._llm_provider.generate(
                    prompt=prompt,
                    temperature=settings.temperature * 0.9,  # Slightly lower for factual accuracy
                )

                # Create FAQ item
                item = FAQItem(
                    question=question,
                    answer=answer.strip(),
                    category=category,
                )

                items.append(item)

            except Exception as e:
                logger.warning(f"Failed to generate answer for question {i}: {e}")
                # Continue with remaining questions
                continue

        if not items:
            raise GenerationError(
                "Failed to generate any FAQ answers",
                details={"num_questions": len(questions)},
            )

        return items

    def _generate_intro_conclusion(
        self, topic: str, items: list[FAQItem]
    ) -> tuple[str | None, str | None]:
        """Generate introduction and conclusion sections."""
        intro = None
        conclusion = None

        if self._include_intro:
            intro_prompt = f"""Write a brief introduction (50-100 words) for an FAQ document about "{topic}".

The introduction should:
- Welcome the reader
- Explain what the FAQ covers
- Set a helpful, friendly tone
- Be concise and engaging

Return ONLY the introduction text.
"""
            try:
                intro = self._llm_provider.generate(
                    prompt=intro_prompt,
                    temperature=settings.temperature,
                )
                logger.debug("Generated introduction")
            except Exception as e:
                logger.warning(f"Failed to generate introduction: {e}")

        if self._include_conclusion:
            conclusion_prompt = f"""Write a brief conclusion (50-100 words) for an FAQ document about "{topic}".

The FAQ covers {len(items)} questions about this topic.

The conclusion should:
- Summarize key takeaways
- Encourage further questions
- Provide next steps or additional resources
- End on a positive, helpful note

Return ONLY the conclusion text.
"""
            try:
                conclusion = self._llm_provider.generate(
                    prompt=conclusion_prompt,
                    temperature=settings.temperature,
                )
                logger.debug("Generated conclusion")
            except Exception as e:
                logger.warning(f"Failed to generate conclusion: {e}")

        return intro, conclusion

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        text = text.strip()

        # Check for markdown code block
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # Skip first line (```json or ```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        return text

    async def generate_async(self, topic: str) -> FAQ:
        """
        Async version of generate.

        Args:
            topic: Main topic for the FAQ

        Returns:
            Complete FAQ document

        Raises:
            GenerationError: If FAQ generation fails
            ValidationError: If generated content is invalid
        """
        import asyncio

        logger.info(f"Generating FAQ async for topic: {topic}")

        try:
            # Step 1: Generate structure
            logger.info("Step 1/3: Generating FAQ structure...")
            structure = await asyncio.to_thread(self._generate_structure, topic)

            # Step 2: Generate answers concurrently
            logger.info("Step 2/3: Generating detailed answers concurrently...")
            items = await self._generate_answers_async(structure)

            # Step 3: Generate intro and conclusion concurrently
            logger.info("Step 3/3: Generating intro and conclusion...")
            intro, conclusion = await self._generate_intro_conclusion_async(topic, items)

            # Build final FAQ
            faq = FAQ(
                metadata=structure["metadata"],
                items=items,
                introduction=intro,
                conclusion=conclusion,
            )

            logger.info(
                f"✓ FAQ generated successfully (async): {len(faq.items)} Q&A pairs, "
                f"{faq.word_count()} words total"
            )

            return faq

        except (PydanticValidationError, ValidationError) as e:
            logger.error(f"FAQ validation failed: {e}")
            raise ValidationError(
                f"Generated FAQ doesn't match expected structure: {e}",
                details={"topic": topic},
            ) from e
        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            raise GenerationError(
                f"Failed to generate FAQ: {e}",
                details={"topic": topic},
            ) from e

    async def _generate_answers_async(self, structure: dict[str, Any]) -> list[FAQItem]:
        """Generate answers concurrently using async methods."""
        import asyncio

        questions = structure["questions"]
        topic = structure["metadata"].topic

        async def generate_single_answer(q_data: dict, index: int) -> FAQItem | None:
            """Generate answer for a single question."""
            question = q_data["question"]
            category = q_data.get("category")

            logger.debug(f"Generating answer {index}/{len(questions)}: {question[:50]}...")

            prompt = f"""Answer this FAQ question about "{topic}":

Question: {question}

Provide a comprehensive, accurate, and helpful answer (100-200 words).

Return ONLY the answer text, no JSON or additional formatting.
"""

            try:
                answer = await self._llm_provider.generate_async(
                    prompt=prompt,
                    temperature=settings.temperature * 0.9,
                )

                return FAQItem(
                    question=question,
                    answer=answer.strip(),
                    category=category,
                )

            except Exception as e:
                logger.warning(f"Failed to generate answer {index}: {e}")
                return None

        # Generate all answers concurrently
        tasks = [
            generate_single_answer(q_data, i + 1) for i, q_data in enumerate(questions)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None values and exceptions
        items = [item for item in results if isinstance(item, FAQItem)]

        if not items:
            raise GenerationError(
                "Failed to generate any FAQ answers",
                details={"num_questions": len(questions)},
            )

        return items

    async def _generate_intro_conclusion_async(
        self, topic: str, items: list[FAQItem]
    ) -> tuple[str | None, str | None]:
        """Generate introduction and conclusion concurrently."""
        import asyncio

        async def generate_intro() -> str | None:
            """Generate introduction."""
            if not self._include_intro:
                return None

            prompt = f"""Write a brief introduction (50-100 words) for an FAQ about "{topic}".

Return ONLY the introduction text.
"""
            try:
                return await self._llm_provider.generate_async(prompt=prompt)
            except Exception as e:
                logger.warning(f"Failed to generate introduction: {e}")
                return None

        async def generate_conclusion() -> str | None:
            """Generate conclusion."""
            if not self._include_conclusion:
                return None

            prompt = f"""Write a brief conclusion (50-100 words) for an FAQ about "{topic}" with {len(items)} questions.

Return ONLY the conclusion text.
"""
            try:
                return await self._llm_provider.generate_async(prompt=prompt)
            except Exception as e:
                logger.warning(f"Failed to generate conclusion: {e}")
                return None

        # Generate both concurrently
        intro, conclusion = await asyncio.gather(generate_intro(), generate_conclusion())

        return intro, conclusion
