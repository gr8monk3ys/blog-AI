"""
Type definitions for the tool registry system.

This module defines the core types used throughout the tool system,
including input/output schemas, tool metadata, and execution context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field


class ToolCategory(str, Enum):
    """Categories for organizing tools."""

    BLOG = "blog"
    EMAIL = "email"
    SOCIAL = "social"
    BUSINESS = "business"
    NAMING = "naming"
    VIDEO = "video"
    SEO = "seo"
    REWRITING = "rewriting"
    ADS = "ads"
    ECOMMERCE = "ecommerce"
    PERSONAL = "personal"
    CREATIVE = "creative"


class OutputFormat(str, Enum):
    """Supported output formats for tools."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    LIST = "list"
    STRUCTURED = "structured"


class InputFieldType(str, Enum):
    """Types of input fields for tool schemas."""

    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    NUMBER = "number"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    KEYWORDS = "keywords"


class InputField(BaseModel):
    """Definition of a single input field for a tool."""

    name: str = Field(..., description="Field identifier (snake_case)")
    label: str = Field(..., description="Human-readable label")
    field_type: InputFieldType = Field(..., description="Type of input field")
    description: str = Field(default="", description="Help text for the field")
    required: bool = Field(default=True, description="Whether field is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    placeholder: Optional[str] = Field(default=None, description="Placeholder text")
    options: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Options for select/multiselect fields"
    )
    min_length: Optional[int] = Field(default=None, description="Minimum text length")
    max_length: Optional[int] = Field(default=None, description="Maximum text length")
    min_value: Optional[float] = Field(default=None, description="Minimum numeric value")
    max_value: Optional[float] = Field(default=None, description="Maximum numeric value")

    model_config = ConfigDict(use_enum_values=True)


class InputSchema(BaseModel):
    """Complete input schema for a tool."""

    fields: List[InputField] = Field(..., description="List of input fields")

    def get_required_fields(self) -> List[InputField]:
        """Return only required fields."""
        return [f for f in self.fields if f.required]

    def get_field(self, name: str) -> Optional[InputField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def validate_input(self, data: Dict[str, Any]) -> List[str]:
        """Validate input data against schema, returning list of errors."""
        errors = []

        for field in self.fields:
            value = data.get(field.name)

            # Check required fields
            if field.required and (value is None or value == ""):
                errors.append(f"Field '{field.label}' is required")
                continue

            if value is None:
                continue

            # Type-specific validation
            if field.field_type == InputFieldType.TEXT or field.field_type == InputFieldType.TEXTAREA:
                if not isinstance(value, str):
                    errors.append(f"Field '{field.label}' must be text")
                elif field.min_length and len(value) < field.min_length:
                    errors.append(f"Field '{field.label}' must be at least {field.min_length} characters")
                elif field.max_length and len(value) > field.max_length:
                    errors.append(f"Field '{field.label}' must be at most {field.max_length} characters")

            elif field.field_type == InputFieldType.NUMBER:
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field.label}' must be a number")
                elif field.min_value is not None and value < field.min_value:
                    errors.append(f"Field '{field.label}' must be at least {field.min_value}")
                elif field.max_value is not None and value > field.max_value:
                    errors.append(f"Field '{field.label}' must be at most {field.max_value}")

            elif field.field_type == InputFieldType.SELECT:
                if field.options:
                    valid_values = [opt["value"] for opt in field.options]
                    if value not in valid_values:
                        errors.append(f"Field '{field.label}' must be one of: {', '.join(valid_values)}")

            elif field.field_type == InputFieldType.MULTISELECT:
                if not isinstance(value, list):
                    errors.append(f"Field '{field.label}' must be a list")
                elif field.options:
                    valid_values = [opt["value"] for opt in field.options]
                    for v in value:
                        if v not in valid_values:
                            errors.append(f"Invalid option '{v}' for field '{field.label}'")

        return errors


class OutputSchema(BaseModel):
    """Schema defining the output structure of a tool."""

    format: OutputFormat = Field(..., description="Output format type")
    fields: Optional[List[str]] = Field(
        default=None,
        description="Field names for structured output"
    )
    description: str = Field(default="", description="Description of the output")

    model_config = ConfigDict(use_enum_values=True)


class ToolMetadata(BaseModel):
    """Metadata for a tool, used for discovery and display."""

    id: str = Field(..., description="Unique tool identifier (slug)")
    name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(..., description="Tool category")
    icon: Optional[str] = Field(default=None, description="Icon identifier or emoji")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    is_premium: bool = Field(default=False, description="Whether tool requires premium")
    is_beta: bool = Field(default=False, description="Whether tool is in beta")
    estimated_time_seconds: int = Field(
        default=30,
        description="Estimated execution time"
    )
    popularity_score: int = Field(default=0, description="Usage-based popularity")

    model_config = ConfigDict(use_enum_values=True)


class ToolDefinition(BaseModel):
    """Complete definition of a tool."""

    metadata: ToolMetadata = Field(..., description="Tool metadata")
    input_schema: InputSchema = Field(..., description="Input schema")
    output_schema: OutputSchema = Field(..., description="Output schema")
    prompt_template: str = Field(..., description="Prompt template with placeholders")
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt"
    )
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Example inputs/outputs"
    )

    def get_id(self) -> str:
        """Get the tool ID."""
        return self.metadata.id

    def get_category(self) -> ToolCategory:
        """Get the tool category."""
        return self.metadata.category


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""

    tool_id: str = Field(..., description="Tool identifier")
    inputs: Dict[str, Any] = Field(..., description="Input values")
    provider_type: Literal["openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generation options"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for tracking"
    )


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    tool_id: str = Field(..., description="Tool that was executed")
    output: Optional[str] = Field(default=None, description="Generated output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class ToolListResponse(BaseModel):
    """Response containing a list of tools."""

    tools: List[ToolMetadata] = Field(..., description="List of tool metadata")
    total: int = Field(..., description="Total number of tools")
    categories: List[str] = Field(..., description="Available categories")


class CategoryInfo(BaseModel):
    """Information about a tool category."""

    id: str = Field(..., description="Category identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Category description")
    icon: str = Field(..., description="Category icon")
    tool_count: int = Field(default=0, description="Number of tools in category")
    color: str = Field(default="#6366f1", description="Theme color for category")
