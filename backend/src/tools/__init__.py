"""
Tool Registry System for Blog AI.

This package provides a comprehensive tool registry system that enables
Blog AI to support 60+ content generation tools in a Copy.ai-style interface.

Usage:
    from src.tools import get_registry, BaseTool, ToolCategory

    # Get the registry
    registry = get_registry()

    # Auto-discover tools from the library
    registry.auto_discover()

    # List all tools
    tools = registry.list_tools()

    # Execute a tool
    from src.types.tools import ToolExecutionRequest
    result = registry.execute(ToolExecutionRequest(
        tool_id="blog-title-generator",
        inputs={"topic": "AI in Healthcare"}
    ))

Creating New Tools:
    1. Create a new file in src/tools/library/{category}/
    2. Subclass BaseTool and implement required properties
    3. The tool will be auto-discovered on registry initialization

Example:
    from src.tools import BaseTool, ToolCategory, text_field

    class MyTool(BaseTool):
        @property
        def id(self) -> str:
            return "my-tool"

        @property
        def name(self) -> str:
            return "My Tool"

        @property
        def description(self) -> str:
            return "Description of what the tool does"

        @property
        def category(self) -> ToolCategory:
            return ToolCategory.BLOG

        @property
        def input_fields(self) -> List[InputField]:
            return [
                text_field("topic", "Topic", "Main topic or subject")
            ]

        @property
        def prompt_template(self) -> str:
            return "Generate content about ${topic}"
"""

from .base import (
    AUDIENCE_OPTIONS,
    LENGTH_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    ToolExecutionError,
    boolean_field,
    keywords_field,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from .categories import (
    CATEGORY_GROUPS,
    CATEGORY_INFO,
    get_all_categories,
    get_categories_with_counts,
    get_category_groups,
    get_category_info,
)
from .registry import (
    ToolNotFoundError,
    ToolRegistry,
    get_registry,
    register_tool,
    tool,
)

# Re-export types for convenience
from ..types.tools import (
    CategoryInfo,
    InputField,
    InputFieldType,
    InputSchema,
    OutputFormat,
    OutputSchema,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolListResponse,
    ToolMetadata,
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolExecutionError",
    # Registry
    "ToolRegistry",
    "ToolNotFoundError",
    "get_registry",
    "register_tool",
    "tool",
    # Categories
    "ToolCategory",
    "CategoryInfo",
    "CATEGORY_INFO",
    "CATEGORY_GROUPS",
    "get_category_info",
    "get_all_categories",
    "get_categories_with_counts",
    "get_category_groups",
    # Types
    "InputField",
    "InputFieldType",
    "InputSchema",
    "OutputFormat",
    "OutputSchema",
    "ToolDefinition",
    "ToolMetadata",
    "ToolExecutionRequest",
    "ToolExecutionResult",
    "ToolListResponse",
    # Field helpers
    "text_field",
    "textarea_field",
    "select_field",
    "keywords_field",
    "number_field",
    "boolean_field",
    # Common options
    "TONE_OPTIONS",
    "AUDIENCE_OPTIONS",
    "LENGTH_OPTIONS",
]
