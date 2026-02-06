"""Tone Changer Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    select_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ToneChangerTool(BaseTool):
    """Change the tone of content while preserving the message."""

    @property
    def id(self) -> str:
        return "tone-changer"

    @property
    def name(self) -> str:
        return "Tone Changer"

    @property
    def description(self) -> str:
        return "Transform your content's tone from casual to formal, or vice versa"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWRITING

    @property
    def icon(self) -> str:
        return "tune"

    @property
    def tags(self) -> List[str]:
        return ["tone", "style", "rewrite", "formal", "casual"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="text",
                label="Text to Transform",
                description="Enter the text you want to change the tone of",
                min_length=10,
                max_length=3000,
            ),
            select_field(
                name="target_tone",
                label="Target Tone",
                options=[
                    {"label": "Professional/Formal", "value": "formal"},
                    {"label": "Casual/Conversational", "value": "casual"},
                    {"label": "Friendly/Warm", "value": "friendly"},
                    {"label": "Authoritative/Expert", "value": "authoritative"},
                    {"label": "Enthusiastic/Exciting", "value": "enthusiastic"},
                    {"label": "Empathetic/Supportive", "value": "empathetic"},
                    {"label": "Humorous/Witty", "value": "humorous"},
                    {"label": "Direct/Concise", "value": "direct"},
                ],
                default="formal",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "Your text with the new tone applied"

    @property
    def system_prompt(self) -> str:
        return """You are a skilled editor who can transform the tone of any
content while preserving its core message. You understand the nuances of
different writing styles and can seamlessly shift between them."""

    @property
    def prompt_template(self) -> str:
        return """Transform the tone of this text:

Original Text:
${text}

Target Tone: ${target_tone}

Requirements:
- Preserve all the key information and meaning
- Transform the language, word choice, and style to match the target tone
- Adjust formality, sentence structure, and vocabulary accordingly
- Maintain the same approximate length
- Ensure the output sounds natural for the target tone

Transformed text:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 2000
