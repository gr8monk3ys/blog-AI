"""Value Proposition Generator Tool."""

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


class ValuePropositionTool(BaseTool):
    """Generate compelling value propositions."""

    @property
    def id(self) -> str:
        return "value-proposition-generator"

    @property
    def name(self) -> str:
        return "Value Proposition Generator"

    @property
    def description(self) -> str:
        return "Create clear, compelling value propositions that differentiate your offering"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BUSINESS

    @property
    def icon(self) -> str:
        return "diamond"

    @property
    def tags(self) -> List[str]:
        return ["value proposition", "marketing", "positioning", "branding"]

    @property
    def estimated_time_seconds(self) -> int:
        return 25

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="product_name",
                label="Product/Service Name",
                placeholder="e.g., TaskFlow",
            ),
            textarea_field(
                name="product_description",
                label="What You Offer",
                description="Describe your product or service",
                placeholder="e.g., A project management tool for remote teams",
            ),
            textarea_field(
                name="target_audience",
                label="Target Audience",
                description="Who is this for?",
                placeholder="e.g., Remote teams at startups with 10-50 employees",
            ),
            textarea_field(
                name="key_benefits",
                label="Key Benefits",
                description="Main benefits for customers",
                placeholder="e.g., Save time, reduce meetings, improve visibility",
            ),
            textarea_field(
                name="differentiator",
                label="What Makes You Different",
                description="Your unique advantage over alternatives",
                placeholder="e.g., AI-powered task prioritization, async-first design",
            ),
            text_field(
                name="competitor",
                label="Main Competitor/Alternative",
                description="What would customers use instead?",
                placeholder="e.g., Asana, Trello, spreadsheets",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Multiple value proposition formats"

    @property
    def system_prompt(self) -> str:
        return """You are a positioning and messaging expert who creates
value propositions that clearly communicate unique value and resonate
with target audiences. You understand frameworks like the Value Proposition
Canvas and can create variations for different contexts."""

    @property
    def prompt_template(self) -> str:
        return """Create value propositions for:

Product: ${product_name}
Description: ${product_description}
Target Audience: ${target_audience}
Key Benefits: ${key_benefits}
Differentiator: ${differentiator}
Main Competitor: ${competitor}

Create the following:

1. **One-Liner** (10-15 words)
   A punchy statement of what you do and for whom

2. **Headline + Subheadline** (website hero format)
   Headline: The main promise
   Subheadline: How you deliver on it

3. **XYZ Format**
   "We help [target] achieve [benefit] by [method]"

4. **Before/After/Bridge**
   Before: The problem
   After: The desired state
   Bridge: Your solution

5. **Competitive Positioning**
   "Unlike [alternative], we [differentiator]"

Make each version clear, specific, and benefit-focused:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 800
