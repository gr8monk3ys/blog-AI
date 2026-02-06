"""Content Summarizer Tool."""

from typing import List

from ...base import (
    BaseTool,
    InputField,
    select_field,
    textarea_field,
)
from ...categories import ToolCategory
from ....types.tools import OutputFormat


class SummarizerTool(BaseTool):
    """Summarize long content into concise versions."""

    @property
    def id(self) -> str:
        return "summarizer"

    @property
    def name(self) -> str:
        return "Content Summarizer"

    @property
    def description(self) -> str:
        return "Condense long articles, documents, or text into key points"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REWRITING

    @property
    def icon(self) -> str:
        return "compress"

    @property
    def tags(self) -> List[str]:
        return ["summarize", "condense", "tldr", "key points"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="text",
                label="Text to Summarize",
                description="Enter the content you want to summarize",
                min_length=100,
                max_length=10000,
            ),
            select_field(
                name="length",
                label="Summary Length",
                options=[
                    {"label": "TL;DR (1-2 sentences)", "value": "tldr"},
                    {"label": "Brief (1 paragraph)", "value": "brief"},
                    {"label": "Standard (2-3 paragraphs)", "value": "standard"},
                    {"label": "Detailed (comprehensive)", "value": "detailed"},
                ],
                default="brief",
            ),
            select_field(
                name="format",
                label="Summary Format",
                options=[
                    {"label": "Prose (paragraph form)", "value": "prose"},
                    {"label": "Bullet Points", "value": "bullets"},
                    {"label": "Numbered List", "value": "numbered"},
                    {"label": "Executive Summary", "value": "executive"},
                ],
                default="prose",
            ),
            select_field(
                name="focus",
                label="Focus On",
                options=[
                    {"label": "Key Points (main ideas)", "value": "key_points"},
                    {"label": "Action Items (what to do)", "value": "actions"},
                    {"label": "Facts & Data", "value": "facts"},
                    {"label": "Conclusions & Recommendations", "value": "conclusions"},
                ],
                default="key_points",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "A concise summary of the content"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at distilling complex information into
clear, concise summaries. You identify the most important points and
present them in an easily digestible format."""

    @property
    def prompt_template(self) -> str:
        return """Summarize the following content:

${text}

Summary Length: ${length}
Format: ${format}
Focus: ${focus}

Requirements:
- Extract the most important information based on the focus area
- Maintain accuracy - don't add information not in the original
- Use the specified format
- Match the target length
- Preserve any critical facts, figures, or conclusions
- Make it easy to understand without reading the full text

Summary:"""

    @property
    def default_temperature(self) -> float:
        return 0.5

    @property
    def default_max_tokens(self) -> int:
        return 1000
