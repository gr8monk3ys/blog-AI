"""Cover Letter Generator Tool."""

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


class CoverLetterTool(BaseTool):
    """Generate professional cover letters."""

    @property
    def id(self) -> str:
        return "cover-letter-generator"

    @property
    def name(self) -> str:
        return "Cover Letter Generator"

    @property
    def description(self) -> str:
        return "Create personalized, professional cover letters that get interviews"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PERSONAL

    @property
    def icon(self) -> str:
        return "work"

    @property
    def tags(self) -> List[str]:
        return ["cover letter", "job application", "career", "resume"]

    @property
    def estimated_time_seconds(self) -> int:
        return 30

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field(
                name="job_title",
                label="Job Title",
                placeholder="e.g., Senior Software Engineer",
            ),
            text_field(
                name="company_name",
                label="Company Name",
                placeholder="e.g., TechCorp Inc.",
            ),
            textarea_field(
                name="job_requirements",
                label="Key Job Requirements",
                description="Main requirements from the job posting",
                placeholder="e.g., 5+ years Python, AWS experience, Team leadership",
            ),
            textarea_field(
                name="your_experience",
                label="Your Relevant Experience",
                description="Your background that matches the role",
                placeholder="e.g., 7 years in software development, Led team of 5...",
            ),
            textarea_field(
                name="achievements",
                label="Key Achievements",
                description="Quantifiable achievements to highlight",
                placeholder="e.g., Increased system performance by 40%, Led $2M project",
            ),
            text_field(
                name="company_appeal",
                label="Why This Company",
                description="What attracts you to the company",
                placeholder="e.g., Their commitment to open source, Recent expansion",
                required=False,
            ),
            select_field(
                name="tone",
                label="Tone",
                options=[
                    {"label": "Professional", "value": "professional"},
                    {"label": "Enthusiastic", "value": "enthusiastic"},
                    {"label": "Confident", "value": "confident"},
                    {"label": "Conversational", "value": "conversational"},
                ],
                default="professional",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "A complete, personalized cover letter"

    @property
    def system_prompt(self) -> str:
        return """You are a career coach and professional writer who creates
cover letters that get candidates noticed. You know how to match qualifications
to requirements and present candidates compellingly."""

    @property
    def prompt_template(self) -> str:
        return """Write a cover letter for:

Position: ${job_title} at ${company_name}
Key Requirements: ${job_requirements}
Candidate Experience: ${your_experience}
Key Achievements: ${achievements}
Company Appeal: ${company_appeal}
Tone: ${tone}

Requirements:
- Professional business letter format
- Strong opening that captures attention
- Connect experience directly to job requirements
- Include 1-2 quantifiable achievements
- Show genuine interest in the company
- Clear call-to-action to discuss further
- Keep to 300-400 words
- Avoid generic phrases and cliches

Write the cover letter:"""

    @property
    def default_temperature(self) -> float:
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        return 800
