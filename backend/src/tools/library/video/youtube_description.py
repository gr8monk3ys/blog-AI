"""YouTube Description Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    boolean_field,
    keywords_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class YouTubeDescriptionTool(BaseTool):
    """Generate SEO-optimized YouTube video descriptions."""

    @property
    def id(self) -> str:
        return "youtube-description-generator"

    @property
    def name(self) -> str:
        return "YouTube Description Generator"

    @property
    def description(self) -> str:
        return "Create SEO-friendly video descriptions that boost discoverability"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.VIDEO

    @property
    def icon(self) -> str:
        return "description"

    @property
    def tags(self) -> List[str]:
        return ["youtube", "description", "seo", "video"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="video_title",
                label="Video Title",
                placeholder="e.g., How to Start a Podcast in 2024",
            ),
            textarea_field(
                name="video_summary",
                label="Video Summary",
                description="What is the video about?",
                placeholder="e.g., Complete guide covering equipment, software, recording tips...",
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="Keywords for YouTube search",
            ),
            textarea_field(
                name="timestamps",
                label="Chapter Timestamps (Optional)",
                description="Key moments in the video",
                placeholder="e.g., 0:00 Intro, 2:30 Equipment, 5:00 Recording...",
                required=False,
            ),
            text_field(
                name="links",
                label="Links to Include (Optional)",
                description="Products, resources, or social links",
                placeholder="e.g., Free guide link, affiliate links, social profiles",
                required=False,
            ),
            boolean_field(
                name="include_hashtags",
                label="Include Hashtags",
                default=True,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A complete YouTube video description"

    @property
    def system_prompt(self) -> str:
        return """You are a YouTube SEO expert who writes descriptions that
rank well in search while engaging viewers. You know how to structure
descriptions for maximum visibility and click-through."""

    @property
    def prompt_template(self) -> str:
        return """Create a YouTube video description:

Video Title: ${video_title}
Video Summary: ${video_summary}
Target Keywords: ${keywords}
Timestamps: ${timestamps}
Links to Include: ${links}
Include Hashtags: ${include_hashtags}

Requirements:
- First 150 characters are crucial (shown in search)
- Front-load keywords naturally
- Include a compelling hook in the first 2-3 lines
- Add timestamps if provided (improves SEO)
- Structure with clear sections
- Include placeholder areas for links
- Add 3-5 relevant hashtags at the end if requested
- Keep total length 200-500 words

Format:
[Hook/Summary - first 2-3 lines visible before "Show more"]

[Expanded description]

[Timestamps if provided]

[Links section]

[Hashtags if requested]

Write the description:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 800
