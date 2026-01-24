"""Business Name Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    keywords_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BusinessNameTool(BaseTool):
    """Generate creative business names."""

    @property
    def id(self) -> str:
        return "business-name-generator"

    @property
    def name(self) -> str:
        return "Business Name Generator"

    @property
    def description(self) -> str:
        return "Create memorable, unique business names that stand out"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NAMING

    @property
    def icon(self) -> str:
        return "store"

    @property
    def tags(self) -> List[str]:
        return ["business name", "branding", "startup", "naming"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="business_description",
                label="Business Description",
                description="What does your business do?",
                placeholder="e.g., An eco-friendly cleaning products company",
            ),
            text_field(
                name="industry",
                label="Industry",
                placeholder="e.g., Cleaning, Sustainability, Consumer Goods",
            ),
            keywords_field(
                name="keywords",
                label="Keywords to Incorporate",
                description="Words or concepts to include",
                required=False,
            ),
            select_field(
                name="style",
                label="Name Style",
                options=[
                    {"label": "Modern/Techy", "value": "modern"},
                    {"label": "Classic/Traditional", "value": "classic"},
                    {"label": "Playful/Fun", "value": "playful"},
                    {"label": "Elegant/Luxurious", "value": "elegant"},
                    {"label": "Descriptive/Clear", "value": "descriptive"},
                    {"label": "Abstract/Unique", "value": "abstract"},
                ],
                default="modern",
            ),
            select_field(
                name="name_type",
                label="Name Type",
                options=[
                    {"label": "Made-up Words", "value": "invented"},
                    {"label": "Real Words", "value": "real"},
                    {"label": "Compound Words", "value": "compound"},
                    {"label": "Acronyms", "value": "acronym"},
                    {"label": "Mix of All", "value": "mix"},
                ],
                default="mix",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "20 business name ideas with brief explanations"

    @property
    def system_prompt(self) -> str:
        return """You are a branding expert who creates memorable, unique
business names. You consider domain availability patterns, trademark
potential, and brand memorability in your suggestions."""

    @property
    def prompt_template(self) -> str:
        return """Generate business name ideas:

Business Description: ${business_description}
Industry: ${industry}
Keywords: ${keywords}
Style: ${style}
Name Type: ${name_type}

Requirements:
- Generate 20 unique business name ideas
- Include a brief explanation for each name
- Consider domain availability (prefer .com-friendly names)
- Avoid names too similar to existing major brands
- Mix different naming techniques
- Ensure names are easy to spell and pronounce

Format as:
1. **[Name]** - [Brief explanation of the name]
2. **[Name]** - [Brief explanation]
..."""

    @property
    def default_temperature(self) -> float:
        return 0.9

    @property
    def default_max_tokens(self) -> int:
        return 1200
