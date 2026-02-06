"""Meta Description Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    keywords_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class MetaDescriptionTool(BaseTool):
    """Generate SEO-optimized meta descriptions."""

    @property
    def id(self) -> str:
        return "meta-description-generator"

    @property
    def name(self) -> str:
        return "Meta Description Generator"

    @property
    def description(self) -> str:
        return "Create compelling meta descriptions that improve click-through rates"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SEO

    @property
    def icon(self) -> str:
        return "search"

    @property
    def tags(self) -> List[str]:
        return ["meta description", "seo", "serp", "ctr"]

    @property
    def estimated_time_seconds(self) -> int:
        return 10

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="page_title",
                label="Page Title",
                description="The title of the page",
                placeholder="e.g., 10 Best Productivity Apps for 2024",
            ),
            textarea_field(
                name="page_content",
                label="Page Content Summary",
                description="Brief description of what the page is about",
                placeholder="e.g., A comprehensive guide comparing productivity apps...",
            ),
            keywords_field(
                name="target_keywords",
                label="Target Keywords",
                description="Primary keywords to include",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "5 meta description options (150-160 characters each)"

    @property
    def system_prompt(self) -> str:
        return """You are an SEO specialist who writes meta descriptions
that maximize click-through rates. You balance keyword optimization with
compelling copy that makes searchers want to click."""

    @property
    def prompt_template(self) -> str:
        return """Create 5 meta descriptions for:

Page Title: ${page_title}
Content: ${page_content}
Target Keywords: ${target_keywords}

Requirements:
- Each description must be 150-160 characters
- Include the primary keyword naturally
- Use action-oriented language
- Create a sense of value or urgency
- Make each option unique in approach
- Include a call-to-action where appropriate

Format as numbered list with character count:
1. [description] (X chars)
2. [description] (X chars)
..."""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 400
