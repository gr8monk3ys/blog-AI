"""Blog Introduction Generator Tool."""

from typing import List

from ...base import (
    AUDIENCE_OPTIONS,
    LENGTH_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    InputField,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BlogIntroductionTool(BaseTool):
    """Generate engaging blog post introductions."""

    @property
    def id(self) -> str:
        return "blog-introduction-generator"

    @property
    def name(self) -> str:
        return "Blog Introduction Generator"

    @property
    def description(self) -> str:
        return "Create captivating introductions that hook readers and set up your blog post"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "start"

    @property
    def tags(self) -> List[str]:
        return ["introduction", "hook", "opening", "blog", "engagement"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="title",
                label="Blog Post Title",
                description="The title of your blog post",
                placeholder="e.g., 10 Ways to Boost Your Productivity",
            ),
            textarea_field(
                name="main_points",
                label="Main Points",
                description="Key points your blog post will cover",
                placeholder="e.g., Time management techniques, focus strategies, tool recommendations",
                required=False,
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="informative",
            ),
            select_field(
                name="audience",
                label="Target Audience",
                options=AUDIENCE_OPTIONS,
                default="general",
            ),
            select_field(
                name="hook_style",
                label="Hook Style",
                options=[
                    {"label": "Question", "value": "question"},
                    {"label": "Statistic", "value": "statistic"},
                    {"label": "Story", "value": "story"},
                    {"label": "Bold Statement", "value": "bold"},
                    {"label": "Problem-Solution", "value": "problem"},
                ],
                default="question",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "An engaging blog introduction (2-3 paragraphs)"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content writer who specializes in creating
compelling blog introductions. Your introductions hook readers immediately,
establish relevance, and create anticipation for the content to follow."""

    @property
    def prompt_template(self) -> str:
        return """Write an engaging introduction for a blog post with the following details:

Title: ${title}
Main Points to Cover: ${main_points}
Tone: ${tone}
Target Audience: ${audience}
Hook Style: ${hook_style}

Requirements:
- Start with a compelling hook using the specified style
- Establish why this topic matters to the reader
- Create a clear promise of value
- Transition smoothly to the main content
- Keep it to 2-3 short paragraphs (100-200 words total)
- Make readers want to continue reading

Write the introduction now:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 400
