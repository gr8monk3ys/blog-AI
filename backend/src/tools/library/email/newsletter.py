"""Newsletter Generator Tool."""

from typing import List

from ...base import (
    TONE_OPTIONS,
    BaseTool,
    InputField,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class NewsletterTool(BaseTool):
    """Generate engaging newsletter content."""

    @property
    def id(self) -> str:
        return "newsletter-generator"

    @property
    def name(self) -> str:
        return "Newsletter Generator"

    @property
    def description(self) -> str:
        return "Create engaging newsletter content that keeps subscribers coming back"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EMAIL

    @property
    def icon(self) -> str:
        return "newspaper"

    @property
    def tags(self) -> List[str]:
        return ["newsletter", "email marketing", "content", "engagement"]

    @property
    def estimated_time_seconds(self) -> int:
        return 45

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="newsletter_name",
                label="Newsletter Name",
                placeholder="e.g., The Weekly Digest",
            ),
            textarea_field(
                name="main_topic",
                label="Main Topic/Theme",
                description="The primary focus of this newsletter issue",
                placeholder="e.g., Latest trends in remote work technology",
            ),
            textarea_field(
                name="key_points",
                label="Key Points to Cover",
                description="Main items, news, or updates to include",
                placeholder="e.g., New tool launch, industry news, tips section",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="friendly",
            ),
            select_field(
                name="format",
                label="Newsletter Format",
                options=[
                    {"label": "Curated Links", "value": "curated"},
                    {"label": "Original Content", "value": "original"},
                    {"label": "Mixed (Links + Commentary)", "value": "mixed"},
                    {"label": "Educational/Tutorial", "value": "educational"},
                    {"label": "News Roundup", "value": "news"},
                ],
                default="mixed",
            ),
            text_field(
                name="cta",
                label="Main Call-to-Action",
                description="What do you want readers to do?",
                placeholder="e.g., Check out our new feature, Reply with feedback",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Complete newsletter content in markdown format"

    @property
    def system_prompt(self) -> str:
        return """You are an expert newsletter writer who creates engaging,
valuable content that readers look forward to receiving. You balance
information with personality and always provide clear value to subscribers."""

    @property
    def prompt_template(self) -> str:
        return """Create a newsletter issue with the following details:

Newsletter Name: ${newsletter_name}
Main Topic: ${main_topic}
Key Points to Cover: ${key_points}
Tone: ${tone}
Format: ${format}
Call-to-Action: ${cta}

Requirements:
- Start with a brief, engaging introduction
- Organize content into clear sections
- Include relevant emojis sparingly for visual interest
- Add brief commentary or insights, not just links
- End with a clear call-to-action
- Keep the total length readable (500-800 words)
- Make it scannable with headers and bullet points

Format in markdown suitable for email:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 1500
