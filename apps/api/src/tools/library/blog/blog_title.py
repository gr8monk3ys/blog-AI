"""Blog Title Generator Tool."""

from typing import List

from ...base import (
    AUDIENCE_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    InputField,
    keywords_field,
    select_field,
    text_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BlogTitleGeneratorTool(BaseTool):
    """Generate compelling blog post titles."""

    @property
    def id(self) -> str:
        return "blog-title-generator"

    @property
    def name(self) -> str:
        return "Blog Title Generator"

    @property
    def description(self) -> str:
        return "Generate attention-grabbing blog post titles that drive clicks and engagement"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "title"

    @property
    def tags(self) -> List[str]:
        return ["title", "headline", "blog", "seo", "clickbait"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="topic",
                label="Blog Topic",
                description="What is your blog post about?",
                placeholder="e.g., Productivity tips for remote workers",
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="Keywords to include for SEO (optional)",
                required=False,
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                description="The tone of your title",
                default="professional",
            ),
            select_field(
                name="audience",
                label="Target Audience",
                options=AUDIENCE_OPTIONS,
                description="Who is your target reader?",
                default="general",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "10 compelling blog title options"

    @property
    def system_prompt(self) -> str:
        return """You are an expert copywriter and SEO specialist who creates
compelling blog titles that drive clicks while accurately representing content.
Your titles are creative, engaging, and optimized for search engines."""

    @property
    def prompt_template(self) -> str:
        return """Generate 10 compelling blog post titles for the following topic:

Topic: ${topic}
Target Keywords: ${keywords}
Tone: ${tone}
Target Audience: ${audience}

Requirements:
- Create exactly 10 unique title options
- Include numbers or statistics where appropriate
- Use power words that drive engagement
- Ensure titles are SEO-friendly (50-60 characters ideal)
- Make titles specific and actionable
- Avoid clickbait that doesn't deliver

Format each title on its own line, numbered 1-10."""

    @property
    def examples(self) -> List[dict]:
        return [
            {
                "inputs": {
                    "topic": "Productivity tips for remote workers",
                    "keywords": "remote work, productivity, home office",
                    "tone": "professional",
                    "audience": "business",
                },
                "output": """1. 15 Proven Productivity Hacks for Remote Workers in 2024
2. The Ultimate Guide to Staying Focused While Working From Home
3. How Top Remote Workers Achieve 10x Productivity
4. Remote Work Productivity: 7 Science-Backed Strategies
5. From Distracted to Dedicated: Mastering Home Office Productivity
6. The Remote Worker's Blueprint for Peak Performance
7. Why 73% of Remote Workers Struggle (And How to Beat the Odds)
8. Transform Your Home Office: Productivity Tips That Actually Work
9. The 5-Hour Workday: Productivity Secrets of Elite Remote Workers
10. Stop Procrastinating: A Remote Worker's Guide to Deep Focus"""
            }
        ]

    @property
    def default_temperature(self) -> float:
        return 0.8  # Higher creativity for title generation

    @property
    def default_max_tokens(self) -> int:
        return 500
