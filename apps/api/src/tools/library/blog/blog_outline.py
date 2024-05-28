"""Blog Outline Generator Tool."""

from typing import List

from ...base import (
    AUDIENCE_OPTIONS,
    BaseTool,
    InputField,
    keywords_field,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BlogOutlineTool(BaseTool):
    """Generate structured blog post outlines."""

    @property
    def id(self) -> str:
        return "blog-outline-generator"

    @property
    def name(self) -> str:
        return "Blog Outline Generator"

    @property
    def description(self) -> str:
        return "Create detailed, structured outlines for blog posts to guide your writing"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "format_list_numbered"

    @property
    def tags(self) -> List[str]:
        return ["outline", "structure", "planning", "blog", "organization"]

    @property
    def estimated_time_seconds(self) -> int:
        return 25

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="topic",
                label="Blog Topic",
                description="The main topic of your blog post",
                placeholder="e.g., How to Start a Successful Podcast",
            ),
            textarea_field(
                name="key_points",
                label="Key Points to Include",
                description="Specific points or subtopics to cover (optional)",
                placeholder="e.g., Equipment needed, recording tips, publishing platforms",
                required=False,
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="SEO keywords to incorporate",
                required=False,
            ),
            select_field(
                name="audience",
                label="Target Audience",
                options=AUDIENCE_OPTIONS,
                default="general",
            ),
            number_field(
                name="sections",
                label="Number of Main Sections",
                description="How many main sections should the outline have?",
                default=5,
                min_value=3,
                max_value=10,
            ),
            select_field(
                name="depth",
                label="Outline Depth",
                options=[
                    {"label": "Basic (headings only)", "value": "basic"},
                    {"label": "Standard (headings + subpoints)", "value": "standard"},
                    {"label": "Detailed (full structure)", "value": "detailed"},
                ],
                default="standard",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A structured blog post outline with headings and subpoints"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content strategist who creates comprehensive,
well-structured blog outlines. Your outlines are logical, SEO-friendly, and
designed to guide writers in creating high-quality, engaging content."""

    @property
    def prompt_template(self) -> str:
        return """Create a detailed blog post outline for the following:

Topic: ${topic}
Key Points to Include: ${key_points}
Target Keywords: ${keywords}
Target Audience: ${audience}
Number of Main Sections: ${sections}
Outline Depth: ${depth}

Requirements:
- Create a logical flow from introduction to conclusion
- Include an engaging introduction hook
- Structure main sections with H2 headings
- Add subpoints or H3 headings based on depth preference
- Include a call-to-action in the conclusion
- Incorporate target keywords naturally
- Consider SEO best practices
- Add brief notes about what each section should cover

Format the outline using markdown with proper heading hierarchy:"""

    @property
    def default_temperature(self) -> float:
        return 0.6

    @property
    def default_max_tokens(self) -> int:
        return 1000
