"""Elevator Pitch Generator Tool."""

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


class ElevatorPitchTool(BaseTool):
    """Generate compelling elevator pitches."""

    @property
    def id(self) -> str:
        return "elevator-pitch-generator"

    @property
    def name(self) -> str:
        return "Elevator Pitch Generator"

    @property
    def description(self) -> str:
        return "Create memorable 30-60 second pitches that hook your audience"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BUSINESS

    @property
    def icon(self) -> str:
        return "elevator"

    @property
    def tags(self) -> List[str]:
        return ["elevator pitch", "startup", "networking", "sales"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="business_name",
                label="Business/Product Name",
                placeholder="e.g., EcoBox",
            ),
            textarea_field(
                name="what_you_do",
                label="What You Do",
                description="Explain your business simply",
                placeholder="e.g., We make sustainable packaging for e-commerce",
            ),
            textarea_field(
                name="problem",
                label="Problem You Solve",
                description="What pain point do you address?",
                placeholder="e.g., E-commerce generates 1B+ pounds of plastic waste yearly",
            ),
            textarea_field(
                name="solution",
                label="Your Solution",
                description="How do you solve it?",
                placeholder="e.g., Biodegradable packaging that costs the same as plastic",
            ),
            select_field(
                name="audience",
                label="Pitch Audience",
                options=[
                    {"label": "Investors", "value": "investors"},
                    {"label": "Potential Customers", "value": "customers"},
                    {"label": "Partners", "value": "partners"},
                    {"label": "General Networking", "value": "networking"},
                    {"label": "Media/Press", "value": "media"},
                ],
                default="investors",
            ),
            select_field(
                name="duration",
                label="Pitch Duration",
                options=[
                    {"label": "30 seconds", "value": "30"},
                    {"label": "60 seconds", "value": "60"},
                    {"label": "90 seconds", "value": "90"},
                ],
                default="60",
            ),
            text_field(
                name="traction",
                label="Traction/Proof (Optional)",
                description="Key metrics or achievements",
                placeholder="e.g., 100 customers, $50K MRR, Featured in TechCrunch",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A polished elevator pitch script"

    @property
    def system_prompt(self) -> str:
        return """You are an expert pitch coach who has helped hundreds of
founders craft memorable elevator pitches. You know how to hook attention,
communicate value quickly, and end with a compelling call to action."""

    @property
    def prompt_template(self) -> str:
        return """Create an elevator pitch with these details:

Business: ${business_name}
What You Do: ${what_you_do}
Problem: ${problem}
Solution: ${solution}
Audience: ${audience}
Duration: ${duration} seconds
Traction: ${traction}

Requirements:
- Start with a hook that grabs attention
- Clearly state the problem and why it matters
- Explain your solution simply
- Include traction/proof if provided
- Tailor the emphasis to the audience type
- End with a clear ask or next step
- Keep it conversational, not salesy
- Time it to the specified duration

Word count guidelines:
- 30 seconds: ~75 words
- 60 seconds: ~150 words
- 90 seconds: ~225 words

Write the pitch:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 400
