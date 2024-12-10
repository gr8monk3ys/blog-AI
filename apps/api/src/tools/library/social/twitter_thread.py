"""Twitter/X Thread Generator Tool."""

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


class TwitterThreadTool(BaseTool):
    """Generate engaging Twitter/X threads."""

    @property
    def id(self) -> str:
        return "twitter-thread-generator"

    @property
    def name(self) -> str:
        return "Twitter/X Thread Generator"

    @property
    def description(self) -> str:
        return "Create viral Twitter/X threads that educate and engage your audience"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SOCIAL

    @property
    def icon(self) -> str:
        return "chat"

    @property
    def tags(self) -> List[str]:
        return ["twitter", "x", "thread", "viral", "social media"]

    @property
    def estimated_time_seconds(self) -> int:
        return 30

    @property
    def input_fields(self) -> List[InputField]:
        return [
            textarea_field(
                name="topic",
                label="Thread Topic",
                description="What is your thread about?",
                placeholder="e.g., How I grew my newsletter from 0 to 10K subscribers",
            ),
            textarea_field(
                name="key_points",
                label="Key Points to Cover",
                description="Main points you want to include",
                placeholder="e.g., Starting strategy, Growth tactics, Lessons learned",
            ),
            number_field(
                name="num_tweets",
                label="Number of Tweets",
                description="How many tweets in the thread?",
                default=8,
                min_value=5,
                max_value=15,
            ),
            select_field(
                name="thread_style",
                label="Thread Style",
                options=[
                    {"label": "How-To/Tutorial", "value": "howto"},
                    {"label": "Story/Journey", "value": "story"},
                    {"label": "Listicle/Tips", "value": "listicle"},
                    {"label": "Analysis/Breakdown", "value": "analysis"},
                    {"label": "Lessons Learned", "value": "lessons"},
                    {"label": "Myth Busting", "value": "myths"},
                ],
                default="howto",
            ),
            select_field(
                name="tone",
                label="Tone",
                options=[
                    {"label": "Educational", "value": "educational"},
                    {"label": "Casual/Conversational", "value": "casual"},
                    {"label": "Bold/Provocative", "value": "bold"},
                    {"label": "Inspiring", "value": "inspiring"},
                ],
                default="educational",
            ),
        ]

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.LIST

    @property
    def output_description(self) -> str:
        return "A numbered Twitter thread ready to post"

    @property
    def system_prompt(self) -> str:
        return """You are a Twitter/X content expert who creates viral threads.
You understand the platform's dynamics, how to hook readers on the first tweet,
and how to keep them engaged through the entire thread."""

    @property
    def prompt_template(self) -> str:
        return """Create a Twitter/X thread with these details:

Topic: ${topic}
Key Points: ${key_points}
Number of Tweets: ${num_tweets}
Style: ${thread_style}
Tone: ${tone}

Requirements:
- First tweet must hook the reader (use curiosity, promise value)
- Each tweet should be under 280 characters
- One main idea per tweet
- Use line breaks within tweets for readability
- Include a "Thread" indicator on tweet 1
- Add relevant emojis sparingly
- End with a summary + CTA to engage
- Number each tweet (1/, 2/, etc.)

Format as:
1/ [First tweet with hook]

2/ [Second tweet]

... and so on:"""

    @property
    def default_temperature(self) -> float:
        return 0.8

    @property
    def default_max_tokens(self) -> int:
        return 1500
