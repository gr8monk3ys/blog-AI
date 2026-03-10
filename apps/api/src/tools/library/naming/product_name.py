"""Product Name Generator Tool."""

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


class ProductNameTool(BaseTool):
    """Generate creative product names."""

    @property
    def id(self) -> str:
        return "product-name-generator"

    @property
    def name(self) -> str:
        return "Product Name Generator"

    @property
    def description(self) -> str:
        return "Create catchy, marketable product names that sell"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NAMING

    @property
    def icon(self) -> str:
        return "inventory_2"

    @property
    def tags(self) -> List[str]:
        return ["product name", "branding", "marketing", "naming"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="product_description",
                label="Product Description",
                description="What is your product?",
                placeholder="e.g., A smart water bottle that tracks hydration",
            ),
            text_field(
                name="target_audience",
                label="Target Audience",
                placeholder="e.g., Health-conscious millennials",
            ),
            textarea_field(
                name="key_benefits",
                label="Key Benefits",
                description="Main benefits of the product",
                placeholder="e.g., Tracks water intake, reminds to drink, syncs with fitness apps",
            ),
            keywords_field(
                name="keywords",
                label="Keywords",
                description="Words to incorporate or evoke",
                required=False,
            ),
            select_field(
                name="brand_personality",
                label="Brand Personality",
                options=[
                    {"label": "Innovative/Tech-Forward", "value": "innovative"},
                    {"label": "Natural/Organic", "value": "natural"},
                    {"label": "Premium/Luxury", "value": "premium"},
                    {"label": "Fun/Youthful", "value": "fun"},
                    {"label": "Professional/Corporate", "value": "professional"},
                    {"label": "Minimalist/Clean", "value": "minimalist"},
                ],
                default="innovative",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "15 product name ideas"

    @property
    def system_prompt(self) -> str:
        return """You are a product naming specialist who creates names that
are memorable, marketable, and resonate with target audiences. You understand
consumer psychology and brand positioning."""

    @property
    def prompt_template(self) -> str:
        return """Generate product name ideas:

Product: ${product_description}
Target Audience: ${target_audience}
Key Benefits: ${key_benefits}
Keywords: ${keywords}
Brand Personality: ${brand_personality}

Requirements:
- Generate 15 unique product name ideas
- Each name should be easy to say and remember
- Consider how the name looks on packaging
- Match the brand personality
- Include a mix of naming styles
- Add a brief tagline suggestion for each

Format as:
1. **[Name]** - "[Tagline suggestion]"
2. **[Name]** - "[Tagline]"
..."""

    @property
    def default_temperature(self) -> float:
        return 0.9

    @property
    def default_max_tokens(self) -> int:
        return 800
