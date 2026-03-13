"""Resume Summary Generator Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class ResumeSummaryTool(BaseTool):
    """Generate professional resume summaries."""

    @property
    def id(self) -> str:
        return "resume-summary-generator"

    @property
    def name(self) -> str:
        return "Resume Summary Generator"

    @property
    def description(self) -> str:
        return "Create impactful resume summaries and professional headlines"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PERSONAL

    @property
    def icon(self) -> str:
        return "assignment_ind"

    @property
    def tags(self) -> List[str]:
        return ["resume", "summary", "career", "professional"]

    @property
    def estimated_time_seconds(self) -> int:
        return 15

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="job_title",
                label="Target Job Title",
                placeholder="e.g., Product Manager",
            ),
            textarea_field(
                name="experience",
                label="Career Experience",
                description="Brief overview of your experience",
                placeholder="e.g., 8 years in product management, B2B SaaS focus",
            ),
            textarea_field(
                name="skills",
                label="Key Skills",
                description="Top skills and competencies",
                placeholder="e.g., Agile, User Research, Data Analysis, Stakeholder Management",
            ),
            textarea_field(
                name="achievements",
                label="Top Achievements",
                description="Key accomplishments with metrics",
                placeholder="e.g., Launched product used by 1M users, Grew revenue 50%",
            ),
            number_field(
                name="years_experience",
                label="Years of Experience",
                default=5,
                min_value=0,
                max_value=50,
            ),
            select_field(
                name="career_level",
                label="Career Level",
                options=[
                    {"label": "Entry Level", "value": "entry"},
                    {"label": "Mid Level", "value": "mid"},
                    {"label": "Senior", "value": "senior"},
                    {"label": "Executive", "value": "executive"},
                    {"label": "Career Changer", "value": "changer"},
                ],
                default="mid",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Resume summary and headline options"

    @property
    def system_prompt(self) -> str:
        return """You are a professional resume writer who creates summaries
that immediately communicate value. You know how to position candidates for
their target roles and stand out in applicant tracking systems."""

    @property
    def prompt_template(self) -> str:
        return """Create resume summary options for:

Target Role: ${job_title}
Experience: ${experience}
Key Skills: ${skills}
Achievements: ${achievements}
Years of Experience: ${years_experience}
Career Level: ${career_level}

Create the following:

## Professional Headlines (3 options)
Short taglines for LinkedIn or resume header (under 120 chars)

## Summary Option 1: Achievement-Focused
3-4 sentences highlighting measurable results

## Summary Option 2: Skills-Focused
3-4 sentences emphasizing expertise and capabilities

## Summary Option 3: Value Proposition
3-4 sentences focused on what you bring to employers

Requirements:
- Each summary should be 50-75 words
- Include quantifiable achievements where possible
- Avoid first person pronouns (I, my, me)
- Use strong action verbs
- Tailor to the career level
- Make it ATS-friendly with relevant keywords

Write the summaries:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 800
