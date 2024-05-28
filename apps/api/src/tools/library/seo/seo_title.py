"""SEO Title Tag Generator Tool."""

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


class SEOTitleTool(BaseTool):
    """Generate SEO-optimized title tags."""

    @property
    def id(self) -> str:
        return "seo-title-generator"

    @property
    def name(self) -> str:
        return "SEO Title Tag Generator"

    @property
    def description(self) -> str:
        return "Create search-optimized title tags that rank and drive clicks"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SEO

    @property
    def icon(self) -> str:
        return "title"

    @property
    def tags(self) -> List[str]:
        return ["title tag", "seo", "serp", "ranking"]

    @property
    def estimated_time_seconds(self) -> int:
        return 10

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="page_topic",
                label="Page Topic",
                description="What is the page about?",
                placeholder="e.g., Guide to choosing the best running shoes for beginners",
            ),
            keywords_field(
                name="primary_keyword",
                label="Primary Keyword",
                description="The main keyword you want to rank for",
            ),
            text_field(
                name="brand_name",
                label="Brand Name (Optional)",
                description="Your brand to append to title",
                placeholder="e.g., Runner's World",
                required=False,
            ),
            select_field(
                name="page_type",
                label="Page Type",
                options=[
                    {"label": "Blog Post/Article", "value": "article"},
                    {"label": "Product Page", "value": "product"},
                    {"label": "Category Page", "value": "category"},
                    {"label": "Homepage", "value": "homepage"},
                    {"label": "Landing Page", "value": "landing"},
                    {"label": "Service Page", "value": "service"},
                ],
                default="article",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "10 SEO title options (50-60 characters each)"

    @property
    def system_prompt(self) -> str:
        return """You are an SEO expert who creates title tags that balance
keyword optimization with click appeal. You know Google's guidelines and
how to maximize visibility in search results."""

    @property
    def prompt_template(self) -> str:
        return """Create 10 SEO title tags for:

Page Topic: ${page_topic}
Primary Keyword: ${primary_keyword}
Brand Name: ${brand_name}
Page Type: ${page_type}

Requirements:
- Each title must be 50-60 characters (including brand if provided)
- Put the primary keyword near the beginning
- Make titles compelling for clicks
- If brand is provided, append with | or - separator
- Vary the formats: how-to, lists, questions, etc.
- Avoid keyword stuffing
- Consider search intent for the page type

Format as numbered list with character count:
1. [title] (X chars)
2. [title] (X chars)
..."""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 500
