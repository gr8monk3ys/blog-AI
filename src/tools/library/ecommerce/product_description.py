"""Product Description Generator Tool."""

from typing import List

from ...base import (
    TONE_OPTIONS,
    BaseTool,
    InputField,
    keywords_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ProductDescriptionTool(BaseTool):
    """Generate compelling product descriptions."""

    @property
    def id(self) -> str:
        return "product-description-generator"

    @property
    def name(self) -> str:
        return "Product Description Generator"

    @property
    def description(self) -> str:
        return "Create persuasive product descriptions that drive sales"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ECOMMERCE

    @property
    def icon(self) -> str:
        return "shopping_bag"

    @property
    def tags(self) -> List[str]:
        return ["product", "ecommerce", "sales", "description"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="product_name",
                label="Product Name",
                placeholder="e.g., Premium Wireless Noise-Canceling Headphones",
            ),
            textarea_field(
                name="features",
                label="Product Features",
                description="Key features and specifications",
                placeholder="e.g., 40-hour battery, Active noise cancellation, Bluetooth 5.0",
            ),
            text_field(
                name="target_customer",
                label="Target Customer",
                placeholder="e.g., Remote workers, Music lovers, Commuters",
            ),
            textarea_field(
                name="benefits",
                label="Key Benefits",
                description="How it helps the customer",
                placeholder="e.g., Focus without distractions, Crystal-clear calls, All-day comfort",
            ),
            keywords_field(
                name="keywords",
                label="SEO Keywords",
                description="Keywords for search optimization",
                required=False,
            ),
            select_field(
                name="platform",
                label="Platform",
                options=[
                    {"label": "Amazon", "value": "amazon"},
                    {"label": "Shopify/Own Store", "value": "shopify"},
                    {"label": "eBay", "value": "ebay"},
                    {"label": "Etsy", "value": "etsy"},
                    {"label": "General", "value": "general"},
                ],
                default="shopify",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="persuasive",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Complete product description with title, bullets, and description"

    @property
    def system_prompt(self) -> str:
        return """You are an e-commerce copywriter who creates product
descriptions that convert browsers into buyers. You understand platform
requirements, SEO, and persuasive selling techniques."""

    @property
    def prompt_template(self) -> str:
        return """Create a product description:

Product: ${product_name}
Features: ${features}
Target Customer: ${target_customer}
Benefits: ${benefits}
SEO Keywords: ${keywords}
Platform: ${platform}
Tone: ${tone}

Requirements:
- Create a compelling product title (optimized for search)
- Write 5-7 benefit-focused bullet points
- Write a persuasive product description (150-300 words)
- Include social proof elements (if applicable)
- Optimize for the specified platform
- Incorporate keywords naturally
- Focus on benefits over features

Format:

## Product Title
[SEO-optimized title]

## Key Features (Bullet Points)
- [Benefit-focused bullet 1]
- [Benefit-focused bullet 2]
...

## Product Description
[Compelling description that sells]

## Suggested Tags/Categories
[Relevant categories for the platform]"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 1000
