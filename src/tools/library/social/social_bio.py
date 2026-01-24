"""Social Media Bio Generator Tool."""

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


class SocialBioTool(BaseTool):
    """Generate compelling social media bios."""

    @property
    def id(self) -> str:
        return "social-bio-generator"

    @property
    def name(self) -> str:
        return "Social Media Bio Generator"

    @property
    def description(self) -> str:
        return "Create memorable bios that make a great first impression on any platform"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SOCIAL

    @property
    def icon(self) -> str:
        return "badge"

    @property
    def tags(self) -> List[str]:
        return ["bio", "profile", "social media", "personal brand"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="name",
                label="Name/Brand",
                placeholder="e.g., Jane Smith",
            ),
            textarea_field(
                name="about",
                label="About You/Your Brand",
                description="What do you do? What are you known for?",
                placeholder="e.g., Marketing consultant, speaker, podcast host",
            ),
            select_field(
                name="platform",
                label="Platform",
                options=[
                    {"label": "Twitter/X", "value": "twitter"},
                    {"label": "Instagram", "value": "instagram"},
                    {"label": "LinkedIn", "value": "linkedin"},
                    {"label": "TikTok", "value": "tiktok"},
                    {"label": "YouTube", "value": "youtube"},
                    {"label": "Personal Website", "value": "website"},
                ],
                default="twitter",
            ),
            select_field(
                name="style",
                label="Bio Style",
                options=[
                    {"label": "Professional", "value": "professional"},
                    {"label": "Creative/Fun", "value": "creative"},
                    {"label": "Minimal", "value": "minimal"},
                    {"label": "Story-Based", "value": "story"},
                    {"label": "Achievement-Focused", "value": "achievement"},
                ],
                default="professional",
            ),
            text_field(
                name="key_achievement",
                label="Key Achievement/Credential",
                description="Something impressive to mention",
                placeholder="e.g., Forbes 30 Under 30, Built 3 startups",
                required=False,
            ),
            text_field(
                name="cta",
                label="Call-to-Action/Link Context",
                description="What's your link about?",
                placeholder="e.g., Free newsletter, Latest project",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "5 bio options for your profile"

    @property
    def system_prompt(self) -> str:
        return """You are a personal branding expert who creates compelling
social media bios. You understand character limits, platform cultures, and
how to make a memorable first impression."""

    @property
    def prompt_template(self) -> str:
        return """Create 5 bio options with these details:

Name: ${name}
About: ${about}
Platform: ${platform}
Style: ${style}
Key Achievement: ${key_achievement}
CTA/Link Context: ${cta}

Character limits:
- Twitter/X: 160 characters
- Instagram: 150 characters
- LinkedIn: 220 characters (headline)
- TikTok: 80 characters
- YouTube: 1000 characters (but keep intro punchy)
- Website: No limit (but be concise)

Requirements:
- Create 5 unique options
- Respect the platform's character limit
- Match the specified style
- Include the key achievement if provided
- Use appropriate emojis for the platform
- Make each bio memorable and clear about what you do

Format as numbered list 1-5:"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 600
