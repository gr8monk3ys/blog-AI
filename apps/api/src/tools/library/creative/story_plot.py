"""Story Plot Generator Tool."""

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


class StoryPlotTool(BaseTool):
    """Generate creative story plots and outlines."""

    @property
    def id(self) -> str:
        return "story-plot-generator"

    @property
    def name(self) -> str:
        return "Story Plot Generator"

    @property
    def description(self) -> str:
        return "Create compelling story plots with characters, conflict, and resolution"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CREATIVE

    @property
    def icon(self) -> str:
        return "auto_stories"

    @property
    def tags(self) -> List[str]:
        return ["story", "plot", "creative writing", "fiction"]

    @property
    def estimated_time_seconds(self) -> int:
        return 30

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="premise",
                label="Story Premise/Idea",
                description="Basic concept for your story",
                placeholder="e.g., A scientist discovers time travel but can only go back 24 hours",
            ),
            select_field(
                name="genre",
                label="Genre",
                options=[
                    {"label": "Science Fiction", "value": "scifi"},
                    {"label": "Fantasy", "value": "fantasy"},
                    {"label": "Mystery/Thriller", "value": "mystery"},
                    {"label": "Romance", "value": "romance"},
                    {"label": "Horror", "value": "horror"},
                    {"label": "Literary Fiction", "value": "literary"},
                    {"label": "Adventure", "value": "adventure"},
                    {"label": "Drama", "value": "drama"},
                ],
                default="scifi",
            ),
            select_field(
                name="length",
                label="Story Length",
                options=[
                    {"label": "Short Story", "value": "short"},
                    {"label": "Novella", "value": "novella"},
                    {"label": "Novel", "value": "novel"},
                ],
                default="short",
            ),
            select_field(
                name="structure",
                label="Plot Structure",
                options=[
                    {"label": "Three-Act Structure", "value": "three_act"},
                    {"label": "Hero's Journey", "value": "heros_journey"},
                    {"label": "Five-Act Structure", "value": "five_act"},
                    {"label": "Non-Linear", "value": "nonlinear"},
                ],
                default="three_act",
            ),
            text_field(
                name="themes",
                label="Themes (Optional)",
                description="Central themes to explore",
                placeholder="e.g., Redemption, Identity, Love vs Duty",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        return "Complete story plot with characters and structure"

    @property
    def system_prompt(self) -> str:
        return """You are a creative writing instructor and story consultant
who helps writers develop compelling plots. You understand narrative structure,
character development, and what makes stories engaging."""

    @property
    def prompt_template(self) -> str:
        return """Develop a story plot:

Premise: ${premise}
Genre: ${genre}
Story Length: ${length}
Plot Structure: ${structure}
Themes: ${themes}

Create a detailed plot outline including:

## Logline
One-sentence summary of the story

## Main Characters
- Protagonist: Name, background, motivation, flaw
- Antagonist/Opposing Force: Description and motivation
- Supporting Characters: 2-3 key characters

## Plot Structure (using ${structure})
[Break down the story into appropriate acts/stages]

## Key Scenes
5-7 pivotal scenes that drive the story

## Themes & Motifs
How the themes manifest in the story

## Ending
Resolution and character transformation

Write the plot outline:"""

    @property
    def default_temperature(self) -> float:
        return 0.9

    @property
    def default_max_tokens(self) -> int:
        return 1500
