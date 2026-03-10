"""Hashtag Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class HashtagGeneratorTool(BaseTool):
    """Generate relevant hashtags for social media posts."""

    @property
    def id(self) -> str:
        return "hashtag-generator"

    @property
    def name(self) -> str:
        return "Hashtag Generator"

    @property
    def description(self) -> str:
        return "Generate optimized hashtag sets to increase your post visibility"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SOCIAL

    @property
    def icon(self) -> str:
        return "tag"

    @property
    def tags(self) -> List[str]:
        return ["hashtags", "social media", "instagram", "reach", "visibility"]

    @property
    def estimated_time_seconds(self) -> int:
        return 10

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="content_description",
                label="Content Description",
                description="What is your post about?",
                placeholder="e.g., Fitness transformation photo at the gym",
            ),
            select_field(
                name="platform",
                label="Platform",
                options=[
                    {"label": "Instagram", "value": "instagram"},
                    {"label": "Twitter/X", "value": "twitter"},
                    {"label": "TikTok", "value": "tiktok"},
                    {"label": "LinkedIn", "value": "linkedin"},
                ],
                default="instagram",
            ),
            text_field(
                name="niche",
                label="Niche/Industry",
                description="Your content niche",
                placeholder="e.g., Fitness, Tech, Food, Travel",
            ),
            number_field(
                name="num_hashtags",
                label="Number of Hashtags",
                default=20,
                min_value=5,
                max_value=30,
            ),
            select_field(
                name="mix_type",
                label="Hashtag Mix",
                options=[
                    {"label": "Balanced (popular + niche)", "value": "balanced"},
                    {"label": "Popular/Trending Focus", "value": "popular"},
                    {"label": "Niche/Targeted Focus", "value": "niche"},
                    {"label": "Community/Engagement Focus", "value": "community"},
                ],
                default="balanced",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A set of optimized hashtags ready to copy"

    @property
    def system_prompt(self) -> str:
        return """You are a social media strategist who understands hashtag
optimization. You know which hashtags drive visibility while avoiding
banned or overused tags that hurt reach."""

    @property
    def prompt_template(self) -> str:
        return """Generate an optimized hashtag set:

Content: ${content_description}
Platform: ${platform}
Niche: ${niche}
Number of Hashtags: ${num_hashtags}
Mix Type: ${mix_type}

Requirements:
- Generate exactly ${num_hashtags} hashtags
- For balanced: 30% popular, 40% medium, 30% niche
- Avoid banned or shadowbanned hashtags
- Include branded/community hashtags when relevant
- Order from most to least popular
- Keep hashtags relevant to the content
- For Twitter/LinkedIn, keep to 3-5 max

Format as:
[Group 1 - Popular]
hashtags here

[Group 2 - Medium]
hashtags here

[Group 3 - Niche]
hashtags here

[Copy-Ready Set]
All hashtags in one block:"""

    @property
    def default_temperature(self) -> float:
        return 0.6

    @property
    def default_max_tokens(self) -> int:
        return 400
