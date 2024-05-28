"""Google Ad Copy Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    keywords_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class GoogleAdCopyTool(BaseTool):
    """Generate Google Ads copy (RSA format)."""

    @property
    def id(self) -> str:
        return "google-ad-copy-generator"

    @property
    def name(self) -> str:
        return "Google Ad Copy Generator"

    @property
    def description(self) -> str:
        return "Create high-converting Google Ads with headlines and descriptions"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ADS

    @property
    def icon(self) -> str:
        return "ads_click"

    @property
    def tags(self) -> List[str]:
        return ["google ads", "ppc", "advertising", "search ads"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="product_service",
                label="Product/Service",
                placeholder="e.g., Cloud Accounting Software",
            ),
            textarea_field(
                name="key_benefits",
                label="Key Benefits",
                description="Main selling points",
                placeholder="e.g., Save 10 hours/week, Real-time insights, Bank sync",
            ),
            text_field(
                name="target_audience",
                label="Target Audience",
                placeholder="e.g., Small business owners",
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="Keywords the ad will target",
            ),
            text_field(
                name="offer",
                label="Offer/CTA",
                description="Special offer or call-to-action",
                placeholder="e.g., Free 30-Day Trial, 20% Off Today",
                required=False,
            ),
            text_field(
                name="competitor",
                label="Main Competitor (Optional)",
                description="For positioning",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Complete RSA with 15 headlines and 4 descriptions"

    @property
    def system_prompt(self) -> str:
        return """You are a Google Ads specialist who creates high-CTR ad copy.
You understand character limits, keyword insertion, and persuasive copywriting
for search advertising."""

    @property
    def prompt_template(self) -> str:
        return """Create Google Responsive Search Ad copy:

Product/Service: ${product_service}
Key Benefits: ${key_benefits}
Target Audience: ${target_audience}
Keywords: ${keywords}
Offer: ${offer}
Competitor: ${competitor}

Requirements for Responsive Search Ads:
- 15 Headlines (max 30 characters each)
- 4 Descriptions (max 90 characters each)
- Include keywords naturally
- Vary the messaging approach
- Include the offer in some variations
- Add urgency and social proof elements
- Make headlines and descriptions work in any combination

Format as:

## Headlines (30 chars max each)
1. [Headline] (X chars)
2. [Headline] (X chars)
...15 total

## Descriptions (90 chars max each)
1. [Description] (X chars)
2. [Description] (X chars)
...4 total

## Recommended Pin Positions
- Position 1: [headline number]
- Position 2: [headline number]
- Position 3: [headline number]"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 1000
