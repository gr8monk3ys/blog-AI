"""FAQ (Frequently Asked Questions) models for blog-AI.

Provides Pydantic models for structured FAQ generation with questions,
answers, categories, and metadata.
"""

import re
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from .base import ContentModel


class FAQItem(ContentModel):
    """Single FAQ question and answer pair."""

    question: str = Field(
        ...,
        description="The FAQ question",
        min_length=5,
        max_length=500,
    )
    answer: str = Field(
        ...,
        description="The detailed answer",
        min_length=10,
    )
    category: str | None = Field(
        default=None,
        description="Optional category for grouping",
        max_length=100,
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and search",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Ensure question is properly formatted."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")

        # Ensure question ends with question mark
        if not v.endswith("?"):
            v += "?"

        return v

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        """Ensure answer is properly formatted."""
        v = v.strip()
        if not v:
            raise ValueError("Answer cannot be empty")
        return v

    def word_count(self) -> int:
        """Get total word count for Q&A pair."""
        return len(self.question.split()) + len(self.answer.split())


class FAQMetadata(ContentModel):
    """Metadata for FAQ document."""

    title: str = Field(
        ...,
        description="FAQ document title",
        min_length=5,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        description="Brief description of FAQ document",
        max_length=500,
    )
    topic: str = Field(
        ...,
        description="Main topic/subject",
        min_length=2,
        max_length=200,
    )
    author: str | None = Field(
        default=None,
        description="Author name",
        max_length=100,
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp",
    )
    categories: list[str] = Field(
        default_factory=list,
        description="FAQ categories",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Overall tags for the FAQ",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is properly formatted."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    def generate_slug(self) -> str:
        """Generate URL-safe slug from title."""
        slug = self.title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")


class FAQ(ContentModel):
    """Complete FAQ document with questions, answers, and metadata."""

    metadata: FAQMetadata = Field(
        ...,
        description="FAQ metadata",
    )
    items: list[FAQItem] = Field(
        default_factory=list,
        description="FAQ question-answer pairs",
    )
    introduction: str | None = Field(
        default=None,
        description="Optional introduction text",
    )
    conclusion: str | None = Field(
        default=None,
        description="Optional conclusion text",
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[FAQItem]) -> list[FAQItem]:
        """Ensure FAQ has at least one item."""
        if not v:
            raise ValueError("FAQ must have at least one question-answer pair")
        return v

    def word_count(self) -> int:
        """Get total word count for entire FAQ."""
        count = 0

        # Count items
        for item in self.items:
            count += item.word_count()

        # Count introduction
        if self.introduction:
            count += len(self.introduction.split())

        # Count conclusion
        if self.conclusion:
            count += len(self.conclusion.split())

        return count

    def get_categories(self) -> list[str]:
        """Get all unique categories from items."""
        categories = set()
        for item in self.items:
            if item.category:
                categories.add(item.category)
        return sorted(categories)

    def get_items_by_category(self, category: str) -> list[FAQItem]:
        """Get all items in a specific category."""
        return [item for item in self.items if item.category == category]

    def get_all_tags(self) -> list[str]:
        """Get all unique tags from metadata and items."""
        tags = set(self.metadata.tags)
        for item in self.items:
            tags.update(item.tags)
        return sorted(tags)

    def model_dump_summary(self) -> dict[str, Any]:
        """Generate summary dictionary for logging/display."""
        return {
            "title": self.metadata.title,
            "topic": self.metadata.topic,
            "total_items": len(self.items),
            "categories": self.get_categories(),
            "word_count": self.word_count(),
            "has_introduction": self.introduction is not None,
            "has_conclusion": self.conclusion is not None,
        }
