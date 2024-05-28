"""Follow-Up Email Generator Tool."""

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


class FollowUpEmailTool(BaseTool):
    """Generate effective follow-up emails."""

    @property
    def id(self) -> str:
        return "follow-up-email-generator"

    @property
    def name(self) -> str:
        return "Follow-Up Email Generator"

    @property
    def description(self) -> str:
        return "Create polite, effective follow-up emails that get responses"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EMAIL

    @property
    def icon(self) -> str:
        return "reply"

    @property
    def tags(self) -> List[str]:
        return ["follow-up", "reminder", "email", "sales", "networking"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="recipient_name",
                label="Recipient Name",
                placeholder="e.g., John",
            ),
            textarea_field(
                name="original_context",
                label="Original Email/Meeting Context",
                description="What was your previous interaction about?",
                placeholder="e.g., Discussed a potential partnership opportunity last week",
            ),
            select_field(
                name="follow_up_number",
                label="Follow-Up Number",
                options=[
                    {"label": "First Follow-Up", "value": "first"},
                    {"label": "Second Follow-Up", "value": "second"},
                    {"label": "Third Follow-Up", "value": "third"},
                    {"label": "Final Follow-Up", "value": "final"},
                ],
                default="first",
            ),
            textarea_field(
                name="desired_action",
                label="Desired Action",
                description="What do you want them to do?",
                placeholder="e.g., Schedule a call, Reply with their decision",
            ),
            text_field(
                name="new_value",
                label="New Value/Information (Optional)",
                description="Any new information to share",
                placeholder="e.g., We just released a case study that might interest you",
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
        return "A polite follow-up email"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at writing follow-up emails that are
persistent but not pushy. You find creative ways to add value in each
follow-up while respecting the recipient's time."""

    @property
    def prompt_template(self) -> str:
        return """Write a follow-up email with these details:

Recipient: ${recipient_name}
Original Context: ${original_context}
Follow-Up Number: ${follow_up_number}
Desired Action: ${desired_action}
New Value to Add: ${new_value}
Tone: ${tone}

Requirements:
- Keep it brief (under 100 words for body)
- Reference the original conversation naturally
- Add new value if possible
- Include a clear, specific call-to-action
- Adjust persistence based on follow-up number
- For final follow-up, create a graceful exit
- Avoid guilt-tripping or being passive-aggressive

Write the email (subject line and body):"""

    @property
    def default_temperature(self) -> float:
        return 0.6

    @property
    def default_max_tokens(self) -> int:
        return 300
