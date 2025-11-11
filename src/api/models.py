"""API request and response models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types."""

    BLOG = "blog"
    BOOK = "book"
    FAQ = "faq"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class OutputFormat(str, Enum):
    """Supported output formats."""

    MARKDOWN = "markdown"
    MDX = "mdx"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"


# === Blog Requests ===


class BlogGenerateRequest(BaseModel):
    """Request for blog post generation."""

    topic: str = Field(..., min_length=3, max_length=500, description="Blog post topic")
    sections: int = Field(default=3, ge=1, le=20, description="Number of sections")
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature")
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON, description="Output format"
    )
    save_to_file: bool = Field(default=False, description="Save to file")


class BlogGenerateResponse(BaseModel):
    """Response for blog post generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    content: dict[str, Any] | str = Field(..., description="Generated content")
    metadata: dict[str, Any] = Field(..., description="Generation metadata")
    file_path: str | None = Field(default=None, description="Saved file path if requested")


# === Book Requests ===


class BookGenerateRequest(BaseModel):
    """Request for book generation."""

    topic: str = Field(..., min_length=3, max_length=500, description="Book topic")
    author: str = Field(..., min_length=1, max_length=200, description="Author name")
    subtitle: str | None = Field(default=None, max_length=500, description="Book subtitle")
    chapters: int = Field(default=11, ge=1, le=100, description="Number of chapters")
    topics_per_chapter: int = Field(default=4, ge=1, le=20, description="Topics per chapter")
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature")
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON, description="Output format"
    )
    save_to_file: bool = Field(default=False, description="Save to file")


class BookGenerateResponse(BaseModel):
    """Response for book generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    content: dict[str, Any] | str = Field(..., description="Generated content")
    metadata: dict[str, Any] = Field(..., description="Generation metadata")
    file_path: str | None = Field(default=None, description="Saved file path if requested")


# === FAQ Requests ===


class FAQGenerateRequest(BaseModel):
    """Request for FAQ generation."""

    topic: str = Field(..., min_length=3, max_length=500, description="FAQ topic")
    questions: int = Field(default=8, ge=1, le=50, description="Number of questions")
    include_intro: bool = Field(default=True, description="Include introduction")
    include_conclusion: bool = Field(default=True, description="Include conclusion")
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature")
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON, description="Output format"
    )
    save_to_file: bool = Field(default=False, description="Save to file")


class FAQGenerateResponse(BaseModel):
    """Response for FAQ generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    content: dict[str, Any] | str = Field(..., description="Generated content")
    metadata: dict[str, Any] = Field(..., description="Generation metadata")
    file_path: str | None = Field(default=None, description="Saved file path if requested")


# === Batch Requests ===


class BatchGenerateRequest(BaseModel):
    """Request for batch generation."""

    content_type: ContentType = Field(..., description="Content type to generate")
    topics: list[str] = Field(..., min_length=1, max_length=100, description="Topics to generate")
    concurrent: int = Field(default=3, ge=1, le=10, description="Concurrent generations")
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature")
    save_to_files: bool = Field(default=False, description="Save to files")


class BatchGenerateResponse(BaseModel):
    """Response for batch generation."""

    job_id: str = Field(..., description="Batch job ID")
    status: str = Field(..., description="Job status")
    total: int = Field(..., description="Total items")
    completed: int = Field(..., description="Completed items")
    failed: int = Field(..., description="Failed items")


# === Error Response ===


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Error details")
    code: str | None = Field(default=None, description="Error code")


# === Health Check ===


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    providers: dict[str, bool] = Field(..., description="Available LLM providers")
