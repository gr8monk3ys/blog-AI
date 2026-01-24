"""Poem Generator Tool."""

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


class PoemGeneratorTool(BaseTool):
    """Generate poetry in various styles."""

    @property
    def id(self) -> str:
        return "poem-generator"

    @property
    def name(self) -> str:
        return "Poem Generator"

    @property
    def description(self) -> str:
        return "Create beautiful poems in various styles and forms"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CREATIVE

    @property
    def icon(self) -> str:
        return "format_quote"

    @property
    def tags(self) -> List[str]:
        return ["poem", "poetry", "creative", "verse"]

    @property
    def estimated_time_seconds(self) -> int:
        return 20

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="subject",
                label="Poem Subject/Theme",
                description="What should the poem be about?",
                placeholder="e.g., The feeling of watching a sunset alone after a long day",
            ),
            select_field(
                name="style",
                label="Poetry Style",
                options=[
                    {"label": "Free Verse", "value": "free_verse"},
                    {"label": "Sonnet", "value": "sonnet"},
                    {"label": "Haiku", "value": "haiku"},
                    {"label": "Limerick", "value": "limerick"},
                    {"label": "Rhyming", "value": "rhyming"},
                    {"label": "Blank Verse", "value": "blank_verse"},
                    {"label": "Villanelle", "value": "villanelle"},
                ],
                default="free_verse",
            ),
            select_field(
                name="mood",
                label="Mood",
                options=[
                    {"label": "Melancholic", "value": "melancholic"},
                    {"label": "Joyful", "value": "joyful"},
                    {"label": "Romantic", "value": "romantic"},
                    {"label": "Contemplative", "value": "contemplative"},
                    {"label": "Hopeful", "value": "hopeful"},
                    {"label": "Dark/Mysterious", "value": "dark"},
                    {"label": "Nostalgic", "value": "nostalgic"},
                ],
                default="contemplative",
            ),
            text_field(
                name="imagery",
                label="Key Imagery (Optional)",
                description="Specific images to include",
                placeholder="e.g., Ocean, stars, autumn leaves",
                required=False,
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

    @property
    def output_description(self) -> str:
        return "An original poem"

    @property
    def system_prompt(self) -> str:
        return """You are a skilled poet who writes evocative, meaningful poetry.
You master various poetic forms and use imagery, metaphor, and rhythm to
create emotional resonance. Your poetry is original and authentic."""

    @property
    def prompt_template(self) -> str:
        return """Write a poem with these elements:

Subject: ${subject}
Style: ${style}
Mood: ${mood}
Key Imagery: ${imagery}

Style requirements:
- Free Verse: No strict meter or rhyme, but with intentional line breaks
- Sonnet: 14 lines, iambic pentameter, ABAB CDCD EFEF GG
- Haiku: Three lines, 5-7-5 syllables
- Limerick: AABBA rhyme scheme, humorous
- Rhyming: Consistent rhyme scheme, any length
- Blank Verse: Unrhymed iambic pentameter
- Villanelle: 19 lines, specific repeating lines

Write an original poem that:
- Captures the specified mood
- Uses vivid, sensory imagery
- Has emotional depth
- Follows the chosen form's structure
- Avoids cliches

Poem:"""

    @property
    def default_temperature(self) -> float:
        return 0.9

    @property
    def default_max_tokens(self) -> int:
        return 500
