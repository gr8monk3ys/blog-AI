"""Blog Conclusion Generator Tool."""

from typing import List

from ...base import (
    TONE_OPTIONS,
    BaseTool,
    InputField,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class BlogConclusionTool(BaseTool):
    """Generate effective blog post conclusions."""

    @property
    def id(self) -> str:
        return "blog-conclusion-generator"

    @property
    def name(self) -> str:
        return "Blog Conclusion Generator"

    @property
    def description(self) -> str:
        return "Create compelling conclusions that summarize key points and drive action"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def icon(self) -> str:
        return "done_all"

    @property
    def tags(self) -> List[str]:
        return ["conclusion", "summary", "cta", "blog", "ending"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="title",
                label="Blog Post Title",
                description="The title of your blog post",
            ),
            textarea_field(
                name="key_points",
                label="Key Takeaways",
                description="Main points covered in the blog post",
                placeholder="e.g., Point 1: ..., Point 2: ..., Point 3: ...",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="informative",
            ),
            select_field(
                name="cta_type",
                label="Call-to-Action Type",
                options=[
                    {"label": "Subscribe/Newsletter", "value": "subscribe"},
                    {"label": "Comment/Discuss", "value": "comment"},
                    {"label": "Share Article", "value": "share"},
                    {"label": "Download Resource", "value": "download"},
                    {"label": "Contact/Consultation", "value": "contact"},
                    {"label": "Product/Service", "value": "product"},
                    {"label": "Read More", "value": "read_more"},
                    {"label": "No CTA", "value": "none"},
                ],
                default="comment",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A strong conclusion with summary and call-to-action"

    @property
    def system_prompt(self) -> str:
        return """You are an expert content writer who crafts memorable blog
conclusions. Your conclusions effectively summarize key points, reinforce
the main message, and inspire readers to take meaningful action."""

    @property
    def prompt_template(self) -> str:
        return """Write a compelling conclusion for a blog post with these details:

Title: ${title}
Key Takeaways: ${key_points}
Tone: ${tone}
Call-to-Action Type: ${cta_type}

Requirements:
- Summarize the main points without being repetitive
- Reinforce the key message or insight
- Create a sense of completion
- Include a clear call-to-action (unless "No CTA" selected)
- End on a memorable note
- Keep it concise (100-150 words)

Write the conclusion now:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 300
