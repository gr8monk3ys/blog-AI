"""Instagram Caption Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    boolean_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class InstagramCaptionTool(BaseTool):
    """Generate engaging Instagram captions."""

    @property
    def id(self) -> str:
        return "instagram-caption-generator"

    @property
    def name(self) -> str:
        return "Instagram Caption Generator"

    @property
    def description(self) -> str:
        return "Create scroll-stopping Instagram captions that boost engagement"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SOCIAL

    @property
    def icon(self) -> str:
        return "photo_camera"

    @property
    def tags(self) -> List[str]:
        return ["instagram", "caption", "social media", "engagement"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="image_description",
                label="Image/Post Description",
                description="Describe what your post is about",
                placeholder="e.g., A photo of my morning coffee setup with a new book",
            ),
            select_field(
                name="account_type",
                label="Account Type",
                options=[
                    {"label": "Personal", "value": "personal"},
                    {"label": "Business/Brand", "value": "business"},
                    {"label": "Influencer/Creator", "value": "influencer"},
                    {"label": "E-commerce/Shop", "value": "ecommerce"},
                ],
                default="personal",
            ),
            select_field(
                name="mood",
                label="Mood/Vibe",
                options=[
                    {"label": "Inspirational", "value": "inspirational"},
                    {"label": "Fun/Playful", "value": "fun"},
                    {"label": "Aesthetic/Minimal", "value": "aesthetic"},
                    {"label": "Educational", "value": "educational"},
                    {"label": "Behind-the-Scenes", "value": "bts"},
                    {"label": "Promotional", "value": "promotional"},
                ],
                default="inspirational",
            ),
            select_field(
                name="length",
                label="Caption Length",
                options=[
                    {"label": "Short (1-2 sentences)", "value": "short"},
                    {"label": "Medium (paragraph)", "value": "medium"},
                    {"label": "Long (storytelling)", "value": "long"},
                ],
                default="medium",
            ),
            boolean_field(
                name="include_hashtags",
                label="Include Hashtags",
                default=True,
            ),
            boolean_field(
                name="include_cta",
                label="Include Call-to-Action",
                default=True,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "An Instagram caption with optional hashtags"

    @property
    def system_prompt(self) -> str:
        return """You are an Instagram content expert who creates captions that
drive engagement. You understand the platform's culture, trending formats,
and how to create content that resonates with different audiences."""

    @property
    def prompt_template(self) -> str:
        return """Create an Instagram caption for:

Post Description: ${image_description}
Account Type: ${account_type}
Mood/Vibe: ${mood}
Length: ${length}
Include Hashtags: ${include_hashtags}
Include CTA: ${include_cta}

Requirements:
- Start with a hook that stops the scroll
- Match the mood and account type
- Use appropriate emojis (not excessive)
- Add line breaks for readability
- If hashtags requested, add 15-20 relevant ones at the end
- If CTA requested, encourage engagement (save, share, comment)
- Be authentic and relatable

Write the caption:"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 600
