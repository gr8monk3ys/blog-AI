"""YouTube Title Generator Tool."""

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


class YouTubeTitleTool(BaseTool):
    """Generate click-worthy YouTube video titles."""

    @property
    def id(self) -> str:
        return "youtube-title-generator"

    @property
    def name(self) -> str:
        return "YouTube Title Generator"

    @property
    def description(self) -> str:
        return "Create compelling YouTube titles that maximize clicks and views"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VIDEO

    @property
    def icon(self) -> str:
        return "play_circle"

    @property
    def tags(self) -> List[str]:
        return ["youtube", "video", "title", "ctr", "views"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="video_topic",
                label="Video Topic",
                description="What is your video about?",
                placeholder="e.g., How I grew my YouTube channel from 0 to 100K subscribers",
            ),
            select_field(
                name="video_type",
                label="Video Type",
                options=[
                    {"label": "Tutorial/How-To", "value": "tutorial"},
                    {"label": "Vlog/Story", "value": "vlog"},
                    {"label": "Review", "value": "review"},
                    {"label": "List/Top 10", "value": "list"},
                    {"label": "Challenge", "value": "challenge"},
                    {"label": "Commentary/Opinion", "value": "commentary"},
                    {"label": "Educational", "value": "educational"},
                ],
                default="tutorial",
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="Keywords for YouTube SEO",
                required=False,
            ),
            select_field(
                name="style",
                label="Title Style",
                options=[
                    {"label": "Curiosity-Driven", "value": "curiosity"},
                    {"label": "How-To", "value": "howto"},
                    {"label": "List-Based", "value": "list"},
                    {"label": "Question", "value": "question"},
                    {"label": "Shocking/Bold", "value": "shocking"},
                    {"label": "Story-Based", "value": "story"},
                ],
                default="curiosity",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "10 YouTube title options"

    @property
    def system_prompt(self) -> str:
        return """You are a YouTube content strategist who creates titles
optimized for high click-through rates. You understand YouTube's algorithm,
viewer psychology, and what makes titles irresistible."""

    @property
    def prompt_template(self) -> str:
        return """Generate YouTube video titles:

Video Topic: ${video_topic}
Video Type: ${video_type}
Keywords: ${keywords}
Title Style: ${style}

Requirements:
- Generate 10 unique title options
- Keep titles under 60 characters (ideal for mobile)
- Include power words that drive clicks
- Use the specified style as primary approach
- Optimize for both search and browse traffic
- Use capitalization strategically
- Avoid clickbait that doesn't deliver

Format as numbered list 1-10:"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 500
