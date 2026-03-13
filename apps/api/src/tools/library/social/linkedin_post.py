"""LinkedIn Post Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    boolean_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class LinkedInPostTool(BaseTool):
    """Generate engaging LinkedIn posts."""

    @property
    def id(self) -> str:
        return "linkedin-post-generator"

    @property
    def name(self) -> str:
        return "LinkedIn Post Generator"

    @property
    def description(self) -> str:
        return "Create professional LinkedIn posts that build your personal brand and drive engagement"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SOCIAL

    @property
    def icon(self) -> str:
        return "work"

    @property
    def tags(self) -> List[str]:
        return ["linkedin", "social media", "professional", "networking", "b2b"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="topic",
                label="Post Topic",
                description="What do you want to talk about?",
                placeholder="e.g., Lessons learned from launching my startup",
            ),
            select_field(
                name="post_type",
                label="Post Type",
                options=[
                    {"label": "Thought Leadership", "value": "thought_leadership"},
                    {"label": "Personal Story", "value": "personal_story"},
                    {"label": "Industry Insights", "value": "industry_insights"},
                    {"label": "Tips & Advice", "value": "tips"},
                    {"label": "Question/Discussion", "value": "question"},
                    {"label": "Announcement", "value": "announcement"},
                    {"label": "Celebration/Win", "value": "celebration"},
                ],
                default="thought_leadership",
            ),
            text_field(
                name="key_message",
                label="Key Message/Takeaway",
                description="The main point you want readers to remember",
                placeholder="e.g., Failure is the best teacher",
            ),
            select_field(
                name="format",
                label="Post Format",
                options=[
                    {"label": "Story Format", "value": "story"},
                    {"label": "List Format", "value": "list"},
                    {"label": "Hook + Content + CTA", "value": "hook_cta"},
                    {"label": "Contrarian Take", "value": "contrarian"},
                ],
                default="hook_cta",
            ),
            boolean_field(
                name="include_hashtags",
                label="Include Hashtags",
                default=True,
            ),
            boolean_field(
                name="include_cta",
                label="Include Call-to-Action",
                default=True,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A LinkedIn post ready to publish"

    @property
    def system_prompt(self) -> str:
        return """You are a LinkedIn content strategist who creates posts that
generate high engagement. You understand the platform's algorithm and what
makes content go viral on LinkedIn while maintaining professionalism."""

    @property
    def prompt_template(self) -> str:
        return """Create a LinkedIn post with these details:

Topic: ${topic}
Post Type: ${post_type}
Key Message: ${key_message}
Format: ${format}
Include Hashtags: ${include_hashtags}
Include CTA: ${include_cta}

Requirements:
- Start with a hook that stops the scroll
- Use short paragraphs and line breaks for readability
- Make it personal and authentic
- Include the key message naturally
- Keep it under 1300 characters (ideal for engagement)
- Add 3-5 relevant hashtags if requested
- End with a question or CTA if requested
- Use line breaks strategically for mobile readability

Write the post:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 500
