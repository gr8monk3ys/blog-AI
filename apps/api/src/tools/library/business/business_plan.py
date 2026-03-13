"""Business Plan Summary Generator Tool."""

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


class BusinessPlanSummaryTool(BaseTool):
    """Generate executive summaries for business plans."""

    @property
    def id(self) -> str:
        return "business-plan-summary"

    @property
    def name(self) -> str:
        return "Business Plan Executive Summary"

    @property
    def description(self) -> str:
        return "Create compelling executive summaries that capture investor interest"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BUSINESS

    @property
    def icon(self) -> str:
        return "description"

    @property
    def tags(self) -> List[str]:
        return ["business plan", "executive summary", "startup", "investor"]

    @property
    def is_premium(self) -> bool:
        return True

    @property
    def estimated_time_seconds(self) -> int:
        return 45

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="company_name",
                label="Company Name",
            ),
            textarea_field(
                name="mission",
                label="Mission Statement",
                description="Your company's core purpose",
                placeholder="e.g., To make sustainable energy accessible to every homeowner",
            ),
            textarea_field(
                name="problem",
                label="Problem",
                description="The problem you're solving",
            ),
            textarea_field(
                name="solution",
                label="Solution",
                description="Your product/service solution",
            ),
            textarea_field(
                name="market",
                label="Target Market",
                description="Who you serve and market size",
            ),
            textarea_field(
                name="business_model",
                label="Business Model",
                description="How you make money",
            ),
            textarea_field(
                name="traction",
                label="Traction & Milestones",
                description="Key achievements and metrics",
                required=False,
            ),
            textarea_field(
                name="team",
                label="Team Highlights",
                description="Key team members and relevant experience",
                required=False,
            ),
            text_field(
                name="funding_ask",
                label="Funding Ask (Optional)",
                description="How much you're raising and what for",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A structured executive summary (1-2 pages)"

    @property
    def system_prompt(self) -> str:
        return """You are a business strategy consultant who has helped
companies raise millions in funding. You know how to structure executive
summaries that are clear, compelling, and investor-ready."""

    @property
    def prompt_template(self) -> str:
        return """Create an executive summary for:

Company: ${company_name}
Mission: ${mission}
Problem: ${problem}
Solution: ${solution}
Target Market: ${market}
Business Model: ${business_model}
Traction: ${traction}
Team: ${team}
Funding Ask: ${funding_ask}

Structure the executive summary with these sections:
1. Company Overview (1-2 paragraphs)
2. The Problem
3. Our Solution
4. Market Opportunity
5. Business Model
6. Traction & Milestones (if provided)
7. The Team (if provided)
8. The Ask (if funding is specified)

Requirements:
- Keep it to 1-2 pages (500-800 words)
- Lead with the most compelling points
- Use specific numbers and metrics where possible
- Write in third person, professional tone
- Make it scannable with clear sections
- End with a strong closing statement

Write the executive summary:"""

    @property
    def default_temperature(self) -> float:
        return 0.6

    @property
    def default_max_tokens(self) -> int:
        return 1500
