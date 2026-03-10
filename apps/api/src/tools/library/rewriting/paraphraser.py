"""Paraphraser Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    select_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ParaphraserTool(BaseTool):
    """Paraphrase and rewrite content while preserving meaning."""

    @property
    def id(self) -> str:
        return "paraphraser"

    @property
    def name(self) -> str:
        return "Paraphraser"

    @property
    def description(self) -> str:
        return "Rewrite content in different ways while keeping the original meaning"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWRITING

    @property
    def icon(self) -> str:
        return "refresh"

    @property
    def tags(self) -> List[str]:
        return ["paraphrase", "rewrite", "rephrase", "unique content"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="text",
                label="Text to Paraphrase",
                description="Enter the text you want to rewrite",
                min_length=10,
                max_length=3000,
            ),
            select_field(
                name="style",
                label="Paraphrasing Style",
                options=[
                    {"label": "Standard (Similar length)", "value": "standard"},
                    {"label": "Creative (More varied)", "value": "creative"},
                    {"label": "Formal (More professional)", "value": "formal"},
                    {"label": "Simplified (Easier to read)", "value": "simplified"},
                    {"label": "Fluent (Natural flow)", "value": "fluent"},
                ],
                default="standard",
            ),
            select_field(
                name="variations",
                label="Number of Variations",
                options=[
                    {"label": "1 variation", "value": "1"},
                    {"label": "2 variations", "value": "2"},
                    {"label": "3 variations", "value": "3"},
                ],
                default="1",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "Paraphrased version(s) of your text"

    @property
    def system_prompt(self) -> str:
        return """You are an expert editor who excels at paraphrasing content.
You maintain the original meaning and key information while creating fresh,
unique versions. You never plagiarize and always improve readability."""

    @property
    def prompt_template(self) -> str:
        return """Paraphrase the following text:

Original Text:
${text}

Style: ${style}
Number of Variations: ${variations}

Requirements:
- Preserve the original meaning completely
- Change sentence structure and word choice
- Maintain the same approximate length for "standard" style
- Apply the specified style transformation
- If multiple variations requested, make each distinctly different
- Ensure the output is natural and readable

Paraphrased version(s):"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 2000
