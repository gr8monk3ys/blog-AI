"""Cold Email Generator Tool."""

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


class ColdEmailTool(BaseTool):
    """Generate effective cold outreach emails."""

    @property
    def id(self) -> str:
        return "cold-email-generator"

    @property
    def name(self) -> str:
        return "Cold Email Generator"

    @property
    def description(self) -> str:
        return "Create personalized cold emails that get responses and build connections"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EMAIL

    @property
    def icon(self) -> str:
        return "outgoing_mail"

    @property
    def tags(self) -> List[str]:
        return ["cold email", "outreach", "sales", "networking", "b2b"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="recipient_name",
                label="Recipient Name",
                description="Name of the person you're reaching out to",
                placeholder="e.g., Sarah Johnson",
            ),
            text_field(
                name="recipient_company",
                label="Recipient Company",
                description="Company or organization name",
                placeholder="e.g., TechCorp Inc.",
            ),
            text_field(
                name="recipient_role",
                label="Recipient Role",
                description="Their job title or role",
                placeholder="e.g., VP of Marketing",
            ),
            text_field(
                name="your_name",
                label="Your Name",
                placeholder="e.g., John Smith",
            ),
            text_field(
                name="your_company",
                label="Your Company/Role",
                placeholder="e.g., Founder at StartupXYZ",
            ),
            textarea_field(
                name="purpose",
                label="Email Purpose",
                description="What do you want to achieve with this email?",
                placeholder="e.g., Schedule a demo of our product, Request a partnership meeting",
            ),
            textarea_field(
                name="value_proposition",
                label="Value Proposition",
                description="What value can you provide to them?",
                placeholder="e.g., Our tool can reduce their marketing costs by 40%",
            ),
            text_field(
                name="personalization",
                label="Personalization Hook",
                description="Something specific about them to reference",
                placeholder="e.g., Their recent article about AI, Their company's expansion",
                required=False,
            ),
            select_field(
                name="tone",
                label="Tone",
                options=TONE_OPTIONS,
                default="professional",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A personalized cold email ready to send"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at writing cold emails that get responses.
Your emails are concise, personalized, and focused on providing value to the
recipient. You avoid salesy language and instead build genuine connections."""

    @property
    def prompt_template(self) -> str:
        return """Write a cold email with the following details:

Recipient: ${recipient_name}, ${recipient_role} at ${recipient_company}
From: ${your_name}, ${your_company}
Purpose: ${purpose}
Value Proposition: ${value_proposition}
Personalization Hook: ${personalization}
Tone: ${tone}

Requirements:
- Keep the email under 150 words
- Start with a personalized hook if provided
- Focus on their needs, not your product
- Include a clear, low-friction call-to-action
- Be specific about the value you can provide
- Avoid generic phrases like "I hope this email finds you well"
- Use short paragraphs (1-2 sentences each)
- End with a specific ask

Write the email (subject line and body):"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 400
