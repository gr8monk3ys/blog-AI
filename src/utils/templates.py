"""Template management for blog-AI.

This module provides functionality for managing custom content generation templates.
Templates allow users to customize prompts, structure, and generation parameters.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class TemplateMetadata(BaseModel):
    """Metadata for a content generation template."""

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Template description"
    )
    content_type: str = Field(
        ..., description="Content type (blog, book, faq, custom)", pattern="^[a-z_]+$"
    )
    version: str = Field(default="1.0.0", description="Template version")
    author: str | None = Field(default=None, max_length=100, description="Template author")
    tags: list[str] = Field(default_factory=list, description="Template tags")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name."""
        # Must be valid filename
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"Template name cannot contain '{char}'")
        return v.strip()


class PromptTemplate(BaseModel):
    """Template for LLM prompts."""

    system_prompt: str | None = Field(
        default=None, description="System prompt for the LLM"
    )
    user_prompt_template: str = Field(
        ..., min_length=1, description="User prompt template with placeholders"
    )
    placeholders: dict[str, str] = Field(
        default_factory=dict, description="Available placeholders and their descriptions"
    )

    def render(self, **kwargs: Any) -> str:
        """Render the template with provided values.

        Args:
            **kwargs: Values for template placeholders

        Returns:
            Rendered prompt string

        Raises:
            ValueError: If required placeholders are missing
        """
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(
                f"Missing required placeholder: {missing_key}. "
                f"Available: {list(self.placeholders.keys())}"
            )


class StructureTemplate(BaseModel):
    """Template for content structure."""

    sections: int | None = Field(default=None, ge=1, le=50, description="Number of sections")
    subsections_per_section: int | None = Field(
        default=None, ge=1, le=20, description="Subsections per section"
    )
    min_words: int | None = Field(default=None, ge=100, description="Minimum word count")
    max_words: int | None = Field(default=None, ge=100, description="Maximum word count")
    include_introduction: bool = Field(default=True, description="Include introduction")
    include_conclusion: bool = Field(default=True, description="Include conclusion")
    custom_structure: dict[str, Any] | None = Field(
        default=None, description="Custom structure definition"
    )


class GenerationParameters(BaseModel):
    """Template for generation parameters."""

    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int | None = Field(default=None, ge=100, le=100000, description="Max tokens")
    model: str | None = Field(default=None, description="Specific model to use")
    provider: str | None = Field(default=None, description="LLM provider preference")


class ContentTemplate(BaseModel):
    """Complete template for content generation."""

    metadata: TemplateMetadata
    prompts: dict[str, PromptTemplate] = Field(
        default_factory=dict, description="Named prompt templates"
    )
    structure: StructureTemplate | None = Field(default=None, description="Structure template")
    parameters: GenerationParameters | None = Field(
        default=None, description="Generation parameters"
    )
    examples: list[dict[str, Any]] = Field(
        default_factory=list, description="Example inputs/outputs"
    )

    def get_prompt(self, name: str = "default") -> PromptTemplate:
        """Get a prompt template by name.

        Args:
            name: Name of the prompt template

        Returns:
            The prompt template

        Raises:
            KeyError: If prompt template not found
        """
        if name not in self.prompts:
            raise KeyError(
                f"Prompt template '{name}' not found. "
                f"Available: {list(self.prompts.keys())}"
            )
        return self.prompts[name]


@dataclass
class TemplateManager:
    """Manages content generation templates."""

    templates_dir: Path = field(default_factory=lambda: Path("templates"))

    def __post_init__(self) -> None:
        """Ensure templates directory exists."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Template directory: {self.templates_dir}")

    def _get_template_path(self, name: str) -> Path:
        """Get path to template file.

        Args:
            name: Template name

        Returns:
            Path to template file
        """
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))
        return self.templates_dir / f"{safe_name}.json"

    def save(self, template: ContentTemplate) -> Path:
        """Save a template to disk.

        Args:
            template: Template to save

        Returns:
            Path to saved template file
        """
        path = self._get_template_path(template.metadata.name)

        # Convert to JSON
        template_dict = template.model_dump(mode="json", exclude_none=True)

        # Save with pretty formatting
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved template '{template.metadata.name}' to {path}")
        return path

    def load(self, name: str) -> ContentTemplate:
        """Load a template from disk.

        Args:
            name: Template name

        Returns:
            Loaded template

        Raises:
            FileNotFoundError: If template not found
            ValueError: If template is invalid
        """
        path = self._get_template_path(name)

        if not path.exists():
            raise FileNotFoundError(f"Template '{name}' not found at {path}")

        with open(path, encoding="utf-8") as f:
            template_dict = json.load(f)

        try:
            template = ContentTemplate(**template_dict)
            logger.info(f"Loaded template '{name}' from {path}")
            return template
        except Exception as e:
            raise ValueError(f"Invalid template file '{path}': {e}")

    def list(self) -> list[TemplateMetadata]:
        """List all available templates.

        Returns:
            List of template metadata
        """
        templates = []

        for path in self.templates_dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    template_dict = json.load(f)

                # Extract just metadata
                metadata = TemplateMetadata(**template_dict["metadata"])
                templates.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load template from {path}: {e}")
                continue

        # Sort by name
        templates.sort(key=lambda t: t.name)
        return templates

    def delete(self, name: str) -> bool:
        """Delete a template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        path = self._get_template_path(name)

        if path.exists():
            path.unlink()
            logger.info(f"Deleted template '{name}' at {path}")
            return True

        return False

    def exists(self, name: str) -> bool:
        """Check if a template exists.

        Args:
            name: Template name

        Returns:
            True if template exists
        """
        return self._get_template_path(name).exists()

    def export(self, name: str, output_path: Path) -> None:
        """Export a template to a specific location.

        Args:
            name: Template name
            output_path: Output file path
        """
        template = self.load(name)

        template_dict = template.model_dump(mode="json", exclude_none=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported template '{name}' to {output_path}")

    def import_template(self, input_path: Path, name: str | None = None) -> ContentTemplate:
        """Import a template from a file.

        Args:
            input_path: Input file path
            name: Optional new name for the template

        Returns:
            Imported template
        """
        with open(input_path, encoding="utf-8") as f:
            template_dict = json.load(f)

        template = ContentTemplate(**template_dict)

        # Optionally rename
        if name:
            template.metadata.name = name

        # Save to templates directory
        self.save(template)

        logger.info(f"Imported template from {input_path}")
        return template


def create_default_blog_template() -> ContentTemplate:
    """Create default blog post template.

    Returns:
        Default blog template
    """
    return ContentTemplate(
        metadata=TemplateMetadata(
            name="default-blog",
            description="Standard blog post template with SEO optimization",
            content_type="blog",
            version="1.0.0",
            tags=["blog", "seo", "default"],
        ),
        prompts={
            "default": PromptTemplate(
                system_prompt="You are an expert blog writer creating engaging, SEO-optimized content.",
                user_prompt_template="Write a comprehensive blog post about {topic}. "
                "Include {sections} main sections with practical examples and actionable insights.",
                placeholders={
                    "topic": "The main topic of the blog post",
                    "sections": "Number of sections to include",
                },
            ),
        },
        structure=StructureTemplate(
            sections=3,
            subsections_per_section=3,
            min_words=800,
            max_words=2000,
            include_introduction=True,
            include_conclusion=True,
        ),
        parameters=GenerationParameters(
            temperature=0.7,
            model="gpt-4",
        ),
    )


def create_default_faq_template() -> ContentTemplate:
    """Create default FAQ template.

    Returns:
        Default FAQ template
    """
    return ContentTemplate(
        metadata=TemplateMetadata(
            name="default-faq",
            description="Standard FAQ template with Schema.org markup",
            content_type="faq",
            version="1.0.0",
            tags=["faq", "seo", "default"],
        ),
        prompts={
            "default": PromptTemplate(
                system_prompt="You are an expert at creating comprehensive FAQs.",
                user_prompt_template="Create {num_questions} frequently asked questions about {topic}. "
                "Make answers clear, concise, and helpful.",
                placeholders={
                    "topic": "The main topic of the FAQ",
                    "num_questions": "Number of questions to generate",
                },
            ),
        },
        structure=StructureTemplate(
            include_introduction=True,
            include_conclusion=True,
        ),
        parameters=GenerationParameters(
            temperature=0.7,
            model="gpt-4",
        ),
    )
