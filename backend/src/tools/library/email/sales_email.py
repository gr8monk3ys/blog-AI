"""Sales Email Generator Tool."""

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


class SalesEmailTool(BaseTool):
    """Generate persuasive sales emails."""

    @property
    def id(self) -> str:
        return "sales-email-generator"

    @property
    def name(self) -> str:
        return "Sales Email Generator"

    @property
    def description(self) -> str:
        return "Create persuasive sales emails that convert leads into customers"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.EMAIL

    @property
    def icon(self) -> str:
        return "sell"

    @property
    def tags(self) -> List[str]:
        return ["sales", "email", "conversion", "b2b", "persuasion"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="product_name",
                label="Product/Service Name",
                placeholder="e.g., CloudSync Pro",
            ),
            textarea_field(
                name="product_description",
                label="Product Description",
                description="Brief description of what you're selling",
                placeholder="e.g., Cloud-based file synchronization for teams",
            ),
            textarea_field(
                name="key_benefits",
                label="Key Benefits",
                description="Main benefits for the customer",
                placeholder="e.g., Save 5 hours/week, 99.9% uptime, Easy setup",
            ),
            textarea_field(
                name="target_pain_points",
                label="Customer Pain Points",
                description="Problems your product solves",
                placeholder="e.g., Lost files, slow sync, security concerns",
            ),
            select_field(
                name="sales_stage",
                label="Sales Stage",
                options=[
                    {"label": "Awareness (Introduction)", "value": "awareness"},
                    {"label": "Interest (After Demo/Trial)", "value": "interest"},
                    {"label": "Decision (Close the Deal)", "value": "decision"},
                    {"label": "Win-Back (Lost Customer)", "value": "winback"},
                ],
                default="awareness",
            ),
            text_field(
                name="offer",
                label="Special Offer (Optional)",
                description="Any promotion or incentive",
                placeholder="e.g., 30-day free trial, 20% off first year",
                required=False,
            ),
            select_field(
                name="urgency",
                label="Urgency Level",
                options=[
                    {"label": "None", "value": "none"},
                    {"label": "Soft (Limited availability)", "value": "soft"},
                    {"label": "Strong (Time-limited offer)", "value": "strong"},
                ],
                default="soft",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A persuasive sales email"

    @property
    def system_prompt(self) -> str:
        return """You are a skilled sales copywriter who creates emails that
convert. You focus on customer benefits, address objections proactively, and
create compelling calls-to-action without being pushy or manipulative."""

    @property
    def prompt_template(self) -> str:
        return """Create a sales email with these details:

Product: ${product_name}
Description: ${product_description}
Key Benefits: ${key_benefits}
Customer Pain Points: ${target_pain_points}
Sales Stage: ${sales_stage}
Special Offer: ${offer}
Urgency Level: ${urgency}

Requirements:
- Lead with the customer's pain points
- Focus on benefits, not features
- Include social proof if appropriate
- Create a clear, compelling call-to-action
- Keep it concise (150-200 words)
- Match the approach to the sales stage
- Add urgency naturally if specified

Write the email (subject line and body):"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 400
