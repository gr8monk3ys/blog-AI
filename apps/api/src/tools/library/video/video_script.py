"""Video Script Generator Tool."""

from typing import List

from ...base import (
    TONE_OPTIONS,
    BaseTool,
    InputField,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class VideoScriptTool(BaseTool):
    """Generate video scripts for YouTube and social media."""

    @property
    def id(self) -> str:
        return "video-script-generator"

    @property
    def name(self) -> str:
        return "Video Script Generator"

    @property
    def description(self) -> str:
        return "Create engaging video scripts that keep viewers watching"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VIDEO

    @property
    def icon(self) -> str:
        return "movie"

    @property
    def tags(self) -> List[str]:
        return ["video", "script", "youtube", "content"]

    @property
    def is_premium(self) -> bool:
        return True

    @property
    def estimated_time_seconds(self) -> int:
        return 60

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="video_title",
                label="Video Title",
                placeholder="e.g., 5 Morning Habits That Changed My Life",
            ),
            textarea_field(
                name="key_points",
                label="Key Points to Cover",
                description="Main points or sections for the video",
                placeholder="e.g., Wake up early, Exercise, Meditation, Journaling, Healthy breakfast",
            ),
            select_field(
                name="video_length",
                label="Target Video Length",
                options=[
                    {"label": "Short (1-3 minutes)", "value": "short"},
                    {"label": "Medium (5-8 minutes)", "value": "medium"},
                    {"label": "Long (10-15 minutes)", "value": "long"},
                    {"label": "Extended (20+ minutes)", "value": "extended"},
                ],
                default="medium",
            ),
            select_field(
                name="platform",
                label="Primary Platform",
                options=[
                    {"label": "YouTube", "value": "youtube"},
                    {"label": "TikTok/Shorts", "value": "short_form"},
                    {"label": "Course/Tutorial", "value": "course"},
                    {"label": "Podcast Video", "value": "podcast"},
                ],
                default="youtube",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="casual",
            ),
            text_field(
                name="cta",
                label="Call-to-Action",
                description="What should viewers do after watching?",
                placeholder="e.g., Subscribe, Download free guide, Comment",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A complete video script with sections"

    @property
    def system_prompt(self) -> str:
        return """You are a professional video scriptwriter who creates
engaging, viewer-retention-optimized scripts. You understand pacing, hooks,
and how to keep audiences engaged from start to finish."""

    @property
    def prompt_template(self) -> str:
        return """Write a video script:

Title: ${video_title}
Key Points: ${key_points}
Target Length: ${video_length}
Platform: ${platform}
Tone: ${tone}
Call-to-Action: ${cta}

Script length guidelines:
- Short: ~300-500 words
- Medium: ~800-1200 words
- Long: ~1500-2000 words
- Extended: ~2500+ words

Requirements:
- Start with a strong hook (first 5-10 seconds are critical)
- Include retention techniques (pattern interrupts, previews)
- Structure with clear sections/chapters
- Add [B-ROLL] suggestions where appropriate
- Include natural transition phrases
- End with the specified CTA
- Match the platform's style conventions

Format the script with:
## Hook
## Section 1: [Title]
## Section 2: [Title]
...
## Outro/CTA

Write the script:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 3000
