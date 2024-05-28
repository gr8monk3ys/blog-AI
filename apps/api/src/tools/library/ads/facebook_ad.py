"""Facebook Ad Copy Generator Tool."""

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


class FacebookAdCopyTool(BaseTool):
    """Generate Facebook/Meta ad copy."""

    @property
    def id(self) -> str:
        return "facebook-ad-copy-generator"

    @property
    def name(self) -> str:
        return "Facebook Ad Copy Generator"

    @property
    def description(self) -> str:
        return "Create scroll-stopping Facebook and Instagram ad copy"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ADS

    @property
    def icon(self) -> str:
        return "campaign"

    @property
    def tags(self) -> List[str]:
        return ["facebook ads", "instagram ads", "social ads", "meta"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="product_service",
                label="Product/Service",
                placeholder="e.g., Online Fitness Coaching",
            ),
            textarea_field(
                name="key_benefits",
                label="Key Benefits",
                description="Main selling points",
                placeholder="e.g., Personalized plans, 24/7 coach access, Proven results",
            ),
            text_field(
                name="target_audience",
                label="Target Audience",
                placeholder="e.g., Busy professionals wanting to get fit",
            ),
            textarea_field(
                name="offer",
                label="Offer/Promotion",
                description="What are you offering?",
                placeholder="e.g., 7-day free trial, First month 50% off",
            ),
            select_field(
                name="ad_objective",
                label="Ad Objective",
                options=[
                    {"label": "Conversions (Sales/Signups)", "value": "conversions"},
                    {"label": "Lead Generation", "value": "leads"},
                    {"label": "Traffic (Website Visits)", "value": "traffic"},
                    {"label": "Awareness (Brand)", "value": "awareness"},
                    {"label": "Engagement (Likes/Comments)", "value": "engagement"},
                ],
                default="conversions",
            ),
            select_field(
                name="ad_format",
                label="Ad Format",
                options=[
                    {"label": "Single Image/Video", "value": "single"},
                    {"label": "Carousel", "value": "carousel"},
                    {"label": "Stories", "value": "stories"},
                    {"label": "Reels", "value": "reels"},
                ],
                default="single",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Complete Facebook ad with primary text, headline, and description"

    @property
    def system_prompt(self) -> str:
        return """You are a Facebook/Meta advertising expert who creates
high-performing ad copy. You understand platform best practices, character
limits, and how to stop the scroll on social feeds."""

    @property
    def prompt_template(self) -> str:
        return """Create Facebook/Meta ad copy:

Product/Service: ${product_service}
Key Benefits: ${key_benefits}
Target Audience: ${target_audience}
Offer: ${offer}
Ad Objective: ${ad_objective}
Ad Format: ${ad_format}

Requirements:
- Primary Text: 125 chars visible (can be longer with "See more")
- Headline: 40 chars max
- Description: 30 chars max
- Link Description: 30 chars max

Create 3 variations:

## Variation 1: [Approach - e.g., "Pain Point Focus"]

**Primary Text:**
[Compelling copy that hooks and converts]

**Headline:** [40 chars max]

**Description:** [30 chars max]

## Variation 2: [Approach]
...

## Variation 3: [Approach]
...

## Recommended A/B Testing:
- Test [element] across variations

Write the ad copy:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 1200
