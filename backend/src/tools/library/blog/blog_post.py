"""Full Blog Post Generator Tool."""

from typing import Any, Dict, List

from ...base import (
    AUDIENCE_OPTIONS,
    LENGTH_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    InputField,
    boolean_field,
    keywords_field,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BlogPostTool(BaseTool):
    """Generate complete blog posts."""

    @property
    def id(self) -> str:
        return "blog-post-generator"

    @property
    def name(self) -> str:
        return "Blog Post Generator"

    @property
    def description(self) -> str:
        return "Generate complete, SEO-optimized blog posts on any topic"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "article"

    @property
    def tags(self) -> List[str]:
        return ["blog", "article", "content", "seo", "long-form"]

    @property
    def is_premium(self) -> bool:
        return True  # Full blog posts are a premium feature

    @property
    def estimated_time_seconds(self) -> int:
        return 120  # Longer generation time

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="topic",
                label="Blog Topic",
                description="The main topic of your blog post",
                placeholder="e.g., The Future of Artificial Intelligence in Healthcare",
            ),
            keywords_field(
                name="keywords",
                label="Target Keywords",
                description="SEO keywords to incorporate throughout the post",
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
                name="length",
                label="Post Length",
                options=LENGTH_OPTIONS,
                default="long",
            ),
            number_field(
                name="sections",
                label="Number of Sections",
                description="How many main sections should the post have?",
                default=5,
                min_value=3,
                max_value=10,
            ),
            boolean_field(
                name="include_faq",
                label="Include FAQ Section",
                description="Add a Frequently Asked Questions section",
                default=False,
            ),
            boolean_field(
                name="include_summary",
                label="Include TL;DR Summary",
                description="Add a summary at the beginning",
                default=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A complete, structured blog post in markdown format"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content writer and SEO specialist who creates
comprehensive, engaging blog posts. Your content is well-researched, properly
structured, and optimized for both readers and search engines. You write in a
clear, accessible style while maintaining expertise and authority on the topic."""

    @property
    def prompt_template(self) -> str:
        return """Write a complete blog post with the following specifications:

Topic: ${topic}
Target Keywords: ${keywords}
Tone: ${tone}
Target Audience: ${audience}
Length: ${length}
Number of Sections: ${sections}
Include FAQ Section: ${include_faq}
Include TL;DR Summary: ${include_summary}

Requirements:
1. Start with an engaging introduction that hooks the reader
2. Use proper heading hierarchy (H1 for title, H2 for sections, H3 for subsections)
3. Include the target keywords naturally throughout the content
4. Make each section substantive and valuable
5. Use bullet points and numbered lists where appropriate
6. Include a strong conclusion with a call-to-action
7. If FAQ requested, add 5 relevant questions and answers
8. If TL;DR requested, add a brief summary at the beginning
9. Maintain the specified tone throughout
10. Write for the target audience's knowledge level

Format the blog post in markdown:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 4000  # Longer for full blog posts

    def pre_process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert boolean fields to readable strings."""
        processed = inputs.copy()
        processed["include_faq"] = "Yes" if inputs.get("include_faq") else "No"
        processed["include_summary"] = "Yes" if inputs.get("include_summary") else "No"
        return processed
