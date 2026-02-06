"""Tagline Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class TaglineTool(BaseTool):
    """Generate memorable taglines and slogans."""

    @property
    def id(self) -> str:
        return "tagline-generator"

    @property
    def name(self) -> str:
        return "Tagline & Slogan Generator"

    @property
    def description(self) -> str:
        return "Create catchy taglines and slogans that capture your brand essence"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NAMING

    @property
    def icon(self) -> str:
        return "format_quote"

    @property
    def tags(self) -> List[str]:
        return ["tagline", "slogan", "branding", "copywriting"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="brand_name",
                label="Brand/Product Name",
                placeholder="e.g., EcoClean",
            ),
            textarea_field(
                name="brand_description",
                label="Brand Description",
                description="What does your brand do?",
                placeholder="e.g., Eco-friendly cleaning products for modern homes",
            ),
            textarea_field(
                name="unique_value",
                label="Unique Value Proposition",
                description="What makes you different?",
                placeholder="e.g., Plant-based formulas that work as well as chemicals",
            ),
            select_field(
                name="tone",
                label="Tagline Tone",
                options=[
                    {"label": "Inspiring/Aspirational", "value": "inspiring"},
                    {"label": "Bold/Confident", "value": "bold"},
                    {"label": "Friendly/Approachable", "value": "friendly"},
                    {"label": "Clever/Witty", "value": "clever"},
                    {"label": "Simple/Direct", "value": "simple"},
                    {"label": "Emotional/Heartfelt", "value": "emotional"},
                ],
                default="bold",
            ),
            select_field(
                name="length",
                label="Tagline Length",
                options=[
                    {"label": "Ultra Short (2-3 words)", "value": "ultra_short"},
                    {"label": "Short (4-6 words)", "value": "short"},
                    {"label": "Medium (7-10 words)", "value": "medium"},
                ],
                default="short",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "15 tagline options"

    @property
    def system_prompt(self) -> str:
        return """You are a creative copywriter who specializes in memorable
taglines and slogans. You create lines that stick in people's minds and
capture brand essence in just a few words."""

    @property
    def prompt_template(self) -> str:
        return """Generate taglines for:

Brand Name: ${brand_name}
Description: ${brand_description}
Unique Value: ${unique_value}
Tone: ${tone}
Length: ${length}

Requirements:
- Generate 15 unique tagline options
- Match the specified tone and length
- Make each memorable and distinctive
- Avoid cliches and overused phrases
- Consider how it sounds when spoken
- Ensure it works standalone and with brand name

Format as numbered list 1-15:"""

    @property
    def default_temperature(self) -> float:
        return 0.9

    @property
    def default_max_tokens(self) -> int:
        return 500
