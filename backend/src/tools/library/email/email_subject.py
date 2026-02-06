"""Email Subject Line Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class EmailSubjectLineTool(BaseTool):
    """Generate compelling email subject lines."""

    @property
    def id(self) -> str:
        return "email-subject-generator"

    @property
    def name(self) -> str:
        return "Email Subject Line Generator"

    @property
    def description(self) -> str:
        return "Create attention-grabbing subject lines that boost email open rates"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EMAIL

    @property
    def icon(self) -> str:
        return "subject"

    @property
    def tags(self) -> List[str]:
        return ["subject line", "email", "open rate", "marketing"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="email_content",
                label="Email Content Summary",
                description="Brief description of what your email is about",
                placeholder="e.g., Announcing our new product feature that saves users 2 hours per week",
            ),
            select_field(
                name="email_type",
                label="Email Type",
                options=[
                    {"label": "Newsletter", "value": "newsletter"},
                    {"label": "Promotional", "value": "promotional"},
                    {"label": "Welcome Email", "value": "welcome"},
                    {"label": "Follow-up", "value": "followup"},
                    {"label": "Cold Outreach", "value": "cold"},
                    {"label": "Event Invitation", "value": "event"},
                    {"label": "Product Update", "value": "update"},
                    {"label": "Transactional", "value": "transactional"},
                ],
                default="newsletter",
            ),
            select_field(
                name="style",
                label="Subject Line Style",
                options=[
                    {"label": "Curiosity-Driven", "value": "curiosity"},
                    {"label": "Benefit-Focused", "value": "benefit"},
                    {"label": "Urgency/Scarcity", "value": "urgency"},
                    {"label": "Question", "value": "question"},
                    {"label": "Personalized", "value": "personalized"},
                    {"label": "How-To", "value": "howto"},
                    {"label": "Numbers/Stats", "value": "numbers"},
                ],
                default="benefit",
            ),
            text_field(
                name="brand_voice",
                label="Brand Voice",
                description="Describe your brand's tone",
                placeholder="e.g., Professional, Playful, Bold",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "10 email subject line options"

    @property
    def system_prompt(self) -> str:
        return """You are an email marketing expert who specializes in crafting
subject lines that maximize open rates. You understand the psychology of what
makes people click and can adapt your style to different brand voices."""

    @property
    def prompt_template(self) -> str:
        return """Generate 10 compelling email subject lines:

Email Content: ${email_content}
Email Type: ${email_type}
Subject Line Style: ${style}
Brand Voice: ${brand_voice}

Requirements:
- Create exactly 10 unique subject lines
- Keep each under 50 characters when possible
- Avoid spam trigger words
- Use the specified style as the primary approach
- Include a mix of techniques (curiosity, benefit, urgency)
- Make them mobile-friendly
- Avoid ALL CAPS and excessive punctuation

Format as a numbered list 1-10:"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 500
