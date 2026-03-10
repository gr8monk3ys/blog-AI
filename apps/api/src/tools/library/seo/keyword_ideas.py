"""Keyword Ideas Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    number_field,
    select_field,
    text_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class KeywordIdeasTool(BaseTool):
    """Generate keyword ideas for SEO content planning."""

    @property
    def id(self) -> str:
        return "keyword-ideas-generator"

    @property
    def name(self) -> str:
        return "Keyword Ideas Generator"

    @property
    def description(self) -> str:
        return "Discover keyword opportunities for your content strategy"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SEO

    @property
    def icon(self) -> str:
        return "key"

    @property
    def tags(self) -> List[str]:
        return ["keyword research", "seo", "content strategy", "search"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="seed_keyword",
                label="Seed Keyword",
                description="Starting keyword to expand from",
                placeholder="e.g., digital marketing",
            ),
            text_field(
                name="niche",
                label="Niche/Industry",
                description="Your specific niche or industry",
                placeholder="e.g., B2B SaaS, ecommerce, health & fitness",
            ),
            select_field(
                name="intent",
                label="Search Intent Focus",
                options=[
                    {"label": "All Intent Types", "value": "all"},
                    {"label": "Informational (how, what, why)", "value": "informational"},
                    {"label": "Commercial (best, reviews, comparison)", "value": "commercial"},
                    {"label": "Transactional (buy, pricing, deals)", "value": "transactional"},
                    {"label": "Navigational (brand, specific)", "value": "navigational"},
                ],
                default="all",
            ),
            number_field(
                name="num_keywords",
                label="Number of Keywords",
                default=30,
                min_value=10,
                max_value=50,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Categorized keyword ideas with intent labels"

    @property
    def system_prompt(self) -> str:
        return """You are an SEO keyword research expert who identifies
valuable keyword opportunities. You understand search intent, keyword
difficulty concepts, and how to find untapped opportunities."""

    @property
    def prompt_template(self) -> str:
        return """Generate keyword ideas based on:

Seed Keyword: ${seed_keyword}
Niche: ${niche}
Intent Focus: ${intent}
Number of Keywords: ${num_keywords}

Requirements:
- Generate exactly ${num_keywords} keywords
- Include a mix of head terms and long-tail keywords
- Group by search intent (informational, commercial, transactional)
- Indicate estimated difficulty (low, medium, high)
- Focus on the specified intent if not "all"
- Include question-based keywords
- Consider related topics and modifiers

Format as:

## Informational Keywords
| Keyword | Estimated Difficulty |
|---------|---------------------|
| [keyword] | [difficulty] |

## Commercial Keywords
| Keyword | Estimated Difficulty |
|---------|---------------------|

## Transactional Keywords
| Keyword | Estimated Difficulty |
|---------|---------------------|

## Long-Tail Opportunities
- [keyword ideas]"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 1200
