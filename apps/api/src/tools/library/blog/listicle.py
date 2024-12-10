"""Listicle Generator Tool."""

from typing import List

from ...base import (
    AUDIENCE_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    InputField,
    keywords_field,
    number_field,
    select_field,
    text_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ListicleTool(BaseTool):
    """Generate listicle-style blog posts."""

    @property
    def id(self) -> str:
        return "listicle-generator"

    @property
    def name(self) -> str:
        return "Listicle Generator"

    @property
    def description(self) -> str:
        return "Create engaging list-style articles like 'Top 10' or 'X Ways To' posts"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "format_list_numbered"

    @property
    def tags(self) -> List[str]:
        return ["listicle", "top 10", "list", "blog", "viral"]

    @property
    def estimated_time_seconds(self) -> int:
        return 60

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="topic",
                label="List Topic",
                description="What is your list about?",
                placeholder="e.g., Best Productivity Apps for Students",
            ),
            number_field(
                name="num_items",
                label="Number of Items",
                description="How many items should be in the list?",
                default=10,
                min_value=3,
                max_value=25,
            ),
            select_field(
                name="list_style",
                label="List Style",
                options=[
                    {"label": "Top X Best", "value": "best"},
                    {"label": "X Ways To", "value": "ways"},
                    {"label": "X Tips For", "value": "tips"},
                    {"label": "X Reasons Why", "value": "reasons"},
                    {"label": "X Things You Need", "value": "things"},
                    {"label": "X Mistakes To Avoid", "value": "mistakes"},
                    {"label": "X Secrets Of", "value": "secrets"},
                ],
                default="best",
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
            keywords_field(
                name="keywords",
                label="Target Keywords",
                required=False,
            ),
            select_field(
                name="detail_level",
                label="Detail Level per Item",
                options=[
                    {"label": "Brief (1-2 sentences)", "value": "brief"},
                    {"label": "Standard (1 paragraph)", "value": "standard"},
                    {"label": "Detailed (2-3 paragraphs)", "value": "detailed"},
                ],
                default="standard",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A complete listicle article in markdown format"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content writer who specializes in creating
engaging, shareable listicle articles. Your lists are well-researched,
provide genuine value, and are formatted for easy scanning while still
offering depth for readers who want more detail."""

    @property
    def prompt_template(self) -> str:
        return """Create a listicle article with the following specifications:

Topic: ${topic}
Number of Items: ${num_items}
List Style: ${list_style}
Tone: ${tone}
Target Audience: ${audience}
Target Keywords: ${keywords}
Detail Level: ${detail_level}

Requirements:
1. Write an engaging introduction (2-3 sentences)
2. Create exactly ${num_items} list items
3. Each item should have a catchy subheading
4. Provide the specified level of detail for each item
5. Use the appropriate list style framing
6. Include practical, actionable information
7. Add a brief conclusion with key takeaway
8. Format with proper markdown headings

Write the listicle now:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 2500
