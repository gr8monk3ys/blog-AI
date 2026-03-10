"""Content Expander Tool."""

from typing import List

from ...base import (
    TONE_OPTIONS,
    BaseTool,
    InputField,
    select_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ContentExpanderTool(BaseTool):
    """Expand short content into more detailed versions."""

    @property
    def id(self) -> str:
        return "content-expander"

    @property
    def name(self) -> str:
        return "Content Expander"

    @property
    def description(self) -> str:
        return "Expand brief content into more detailed, comprehensive text"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWRITING

    @property
    def icon(self) -> str:
        return "expand"

    @property
    def tags(self) -> List[str]:
        return ["expand", "elaborate", "lengthen", "detail"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="text",
                label="Text to Expand",
                description="Enter the brief content you want to expand",
                min_length=10,
                max_length=2000,
            ),
            select_field(
                name="expansion_level",
                label="Expansion Level",
                options=[
                    {"label": "Light (1.5x length)", "value": "light"},
                    {"label": "Moderate (2x length)", "value": "moderate"},
                    {"label": "Significant (3x length)", "value": "significant"},
                    {"label": "Comprehensive (4x+ length)", "value": "comprehensive"},
                ],
                default="moderate",
            ),
            select_field(
                name="expansion_style",
                label="How to Expand",
                options=[
                    {"label": "Add examples and illustrations", "value": "examples"},
                    {"label": "Add explanations and context", "value": "explanations"},
                    {"label": "Add supporting details", "value": "details"},
                    {"label": "Add all of the above", "value": "all"},
                ],
                default="all",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="informative",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Expanded, more detailed version of your content"

    @property
    def system_prompt(self) -> str:
        return """You are a skilled writer who can take brief content and
expand it into comprehensive, engaging text. You add relevant details,
examples, and explanations while maintaining the original message."""

    @property
    def prompt_template(self) -> str:
        return """Expand the following content:

Original Text:
${text}

Expansion Level: ${expansion_level}
Expansion Style: ${expansion_style}
Tone: ${tone}

Requirements:
- Preserve the original meaning and key points
- Add relevant details based on the expansion style
- Maintain the specified tone throughout
- Reach the target length based on expansion level
- Keep content accurate and relevant
- Use proper paragraph structure
- Make the expanded content flow naturally

Expanded version:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 2500
