"""
Format adapters for the Content Remix Engine.

Each adapter transforms analyzed content into a specific format
with platform-specific optimizations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import re

from src.text_generation.core import GenerationOptions, generate_text, create_provider_from_env
from src.types.remix import (
    ContentAnalysis,
    ContentFormat,
    QualityScore,
    TwitterThread,
    LinkedInPost,
    EmailNewsletter,
    YouTubeScript,
    InstagramCarousel,
    PodcastNotes,
    FORMAT_METADATA,
)


class FormatAdapter(ABC):
    """Base class for format adapters."""

    format: ContentFormat
    max_length: int = 5000

    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        self.provider = create_provider_from_env(provider_type)
        self.options = GenerationOptions(
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9,
        )

    @abstractmethod
    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        """Generate the prompt for transforming content to this format."""
        pass

    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured format."""
        pass

    def transform(
        self,
        analysis: ContentAnalysis,
        brand_voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transform content to this format."""
        prompt = self.get_transformation_prompt(analysis, brand_voice)
        response = generate_text(prompt, self.provider, self.options)
        return self.parse_response(response)

    def score_quality(self, content: Dict[str, Any], analysis: ContentAnalysis) -> QualityScore:
        """Score the quality of the transformed content."""
        # Default implementation - can be overridden
        word_count = self._count_words(content)
        format_fit = min(1.0, word_count / (self.max_length / 5))

        return QualityScore(
            overall=0.75,
            format_fit=format_fit,
            voice_match=0.8,
            completeness=0.7,
            engagement=0.75,
            platform_optimization=0.8,
        )

    def _count_words(self, content: Dict[str, Any]) -> int:
        """Count words in content recursively."""
        count = 0
        for value in content.values():
            if isinstance(value, str):
                count += len(value.split())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        count += len(item.split())
                    elif isinstance(item, dict):
                        count += self._count_words(item)
            elif isinstance(value, dict):
                count += self._count_words(value)
        return count


class TwitterThreadAdapter(FormatAdapter):
    """Transform content into a Twitter thread."""

    format = ContentFormat.TWITTER_THREAD
    max_length = 4200

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into an engaging Twitter thread (10-15 tweets).

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
Main Argument: {analysis.main_argument}
{voice_instruction}

REQUIREMENTS:
1. Start with a powerful hook tweet that grabs attention
2. Each tweet should be under 280 characters
3. Use line breaks for readability
4. Include engagement elements (questions, bold statements)
5. End with a clear call-to-action
6. Suggest 3-5 relevant hashtags

OUTPUT FORMAT (JSON):
{{
    "hook": "First tweet that hooks the reader",
    "tweets": [
        "Tweet 1...",
        "Tweet 2...",
        "..."
    ],
    "cta": "Final call-to-action tweet",
    "hashtags": ["hashtag1", "hashtag2"]
}}

Generate the thread:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return TwitterThread(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: parse as plain text
        lines = [l.strip() for l in response.split('\n') if l.strip()]
        tweets = []
        for line in lines:
            # Remove tweet numbers like "1.", "2/15", etc.
            clean = re.sub(r'^[\d]+[./\)]?\s*', '', line)
            if clean and len(clean) <= 280:
                tweets.append(clean)

        return TwitterThread(
            hook=tweets[0] if tweets else "Check out these insights...",
            tweets=tweets[:15],
            cta=tweets[-1] if tweets else "Follow for more!",
            hashtags=[]
        ).model_dump()


class LinkedInPostAdapter(FormatAdapter):
    """Transform content into a LinkedIn post."""

    format = ContentFormat.LINKEDIN_POST
    max_length = 3000

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into a compelling LinkedIn post.

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
Target Audience: {analysis.target_audience}
{voice_instruction}

REQUIREMENTS:
1. Start with a hook (personal story, surprising stat, or bold statement)
2. Use short paragraphs and line breaks for mobile readability
3. Include professional insights and lessons learned
4. Add a thought-provoking question or call-to-action
5. Keep under 3000 characters
6. Suggest 3-5 professional hashtags

OUTPUT FORMAT (JSON):
{{
    "hook": "Opening hook line that stops the scroll",
    "body": "Main content with line breaks...",
    "cta": "Call to action or question",
    "hashtags": ["leadership", "growth", "..."]
}}

Generate the LinkedIn post:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return LinkedInPost(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback
        return LinkedInPost(
            hook="Here's something I learned recently...",
            body=response[:2500],
            cta="What are your thoughts? Share in the comments.",
            hashtags=["professional", "insights"]
        ).model_dump()


class EmailNewsletterAdapter(FormatAdapter):
    """Transform content into an email newsletter."""

    format = ContentFormat.EMAIL_NEWSLETTER
    max_length = 5000

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into an engaging email newsletter.

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
Keywords: {', '.join(analysis.keywords[:5])}
{voice_instruction}

REQUIREMENTS:
1. Create a compelling subject line (under 60 chars)
2. Write preview text (under 100 chars)
3. Start with a personal greeting
4. Include 2-4 clear sections with headers
5. End with a strong call-to-action
6. Keep scannable and mobile-friendly

OUTPUT FORMAT (JSON):
{{
    "subject_line": "Compelling subject line",
    "preview_text": "Preview text shown in inbox",
    "greeting": "Hey [First Name],",
    "intro": "Opening paragraph that hooks...",
    "sections": [
        {{"title": "Section Title", "content": "Section content..."}},
        ...
    ],
    "cta": "Clear call to action",
    "signoff": "Best,\\nYour Name"
}}

Generate the newsletter:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return EmailNewsletter(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        return EmailNewsletter(
            subject_line="You need to see this",
            preview_text="Some valuable insights inside...",
            greeting="Hey there,",
            intro=response[:500],
            sections=[{"title": "Key Insights", "content": response[500:2000]}],
            cta="Reply and let me know what you think!",
            signoff="Best,\nThe Team"
        ).model_dump()


class YouTubeScriptAdapter(FormatAdapter):
    """Transform content into a YouTube video script."""

    format = ContentFormat.YOUTUBE_SCRIPT
    max_length = 8000

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into a YouTube video script.

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
{voice_instruction}

REQUIREMENTS:
1. Create a compelling video title
2. Start with a 5-second hook that stops scrollers
3. Include a brief intro (who you are, what we'll cover)
4. Break into clear sections (each 1-3 minutes)
5. Add transition phrases between sections
6. End with outro and call-to-action (subscribe, comment)
7. Estimate total duration (aim for 8-12 minutes)

OUTPUT FORMAT (JSON):
{{
    "title": "Video Title",
    "hook": "5-second attention-grabbing hook",
    "intro": "Introduction script...",
    "sections": [
        {{"title": "Section Name", "content": "Script content...", "duration": "2 min"}},
        ...
    ],
    "outro": "Wrap-up and summary",
    "cta": "Subscribe and comment CTA",
    "estimated_duration": "10 minutes"
}}

Generate the video script:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return YouTubeScript(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        return YouTubeScript(
            title="Must-Watch Video",
            hook="What if I told you...",
            intro=response[:500],
            sections=[{"title": "Main Points", "content": response[500:3000], "duration": "5 min"}],
            outro="That's a wrap!",
            cta="Subscribe for more content like this!",
            estimated_duration="8 minutes"
        ).model_dump()


class InstagramCarouselAdapter(FormatAdapter):
    """Transform content into an Instagram carousel."""

    format = ContentFormat.INSTAGRAM_CAROUSEL
    max_length = 2200

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into an Instagram carousel post (7-10 slides).

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
{voice_instruction}

REQUIREMENTS:
1. First slide: Eye-catching title/hook
2. Middle slides: One key point per slide (short, punchy text)
3. Last slide: Summary or call-to-action
4. Each slide should have minimal text (1-2 sentences max)
5. Include image prompt suggestions for each slide
6. Write a caption under 2200 characters
7. Suggest relevant hashtags (up to 30)

OUTPUT FORMAT (JSON):
{{
    "caption": "Engaging caption with line breaks...",
    "slides": [
        {{"title": "Slide 1 Title", "content": "Brief content", "image_prompt": "Image description"}},
        ...
    ],
    "hashtags": ["hashtag1", "hashtag2", ...],
    "cta": "Save this for later! 📌"
}}

Generate the carousel:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return InstagramCarousel(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        return InstagramCarousel(
            caption="Swipe through for some valuable insights! 👆",
            slides=[
                {"title": "Key Insight", "content": "Content here", "image_prompt": "Minimalist design"}
            ],
            hashtags=["content", "tips", "growth"],
            cta="Save this for later!"
        ).model_dump()


class PodcastNotesAdapter(FormatAdapter):
    """Transform content into podcast show notes."""

    format = ContentFormat.PODCAST_NOTES
    max_length = 3000

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into podcast show notes.

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
{voice_instruction}

REQUIREMENTS:
1. Create an episode title
2. Write a compelling episode summary (2-3 sentences)
3. List 5-7 key takeaways
4. Create timestamps (as if for a 30-min episode)
5. Suggest resources/links mentioned
6. Include a brief transcript excerpt for the intro

OUTPUT FORMAT (JSON):
{{
    "episode_title": "Episode Title",
    "summary": "Episode summary...",
    "key_takeaways": ["Takeaway 1", "Takeaway 2", ...],
    "timestamps": [
        {{"time": "00:00", "topic": "Introduction"}},
        {{"time": "02:30", "topic": "First topic"}},
        ...
    ],
    "resources": [
        {{"title": "Resource name", "url": "https://..."}}
    ],
    "transcript_excerpt": "Opening segment transcript..."
}}

Generate the show notes:"""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return PodcastNotes(**data).model_dump()
        except (json.JSONDecodeError, ValueError):
            pass

        return PodcastNotes(
            episode_title="Episode Title",
            summary="Episode summary here.",
            key_takeaways=["Key point 1", "Key point 2"],
            timestamps=[{"time": "00:00", "topic": "Introduction"}],
            resources=[],
            transcript_excerpt="Welcome to the show..."
        ).model_dump()


class GenericAdapter(FormatAdapter):
    """Generic adapter for formats without specific implementations."""

    def __init__(self, format: ContentFormat, provider_type: str = "openai"):
        super().__init__(provider_type)
        self.format = format
        metadata = FORMAT_METADATA.get(format, {})
        self.max_length = metadata.get("max_length", 5000)

    def get_transformation_prompt(self, analysis: ContentAnalysis, brand_voice: Optional[str] = None) -> str:
        metadata = FORMAT_METADATA.get(self.format, {})
        format_name = metadata.get("name", self.format.value)
        description = metadata.get("description", "")
        voice_instruction = f"\n\nBrand voice to maintain: {brand_voice}" if brand_voice else ""

        return f"""Transform this blog content into a {format_name}.

{description}

SOURCE CONTENT:
Title: {analysis.title}
Summary: {analysis.summary}
Key Points: {', '.join(analysis.key_points)}
Main Argument: {analysis.main_argument}
{voice_instruction}

Generate optimized content for this format. Output as JSON with appropriate fields for {format_name}."""

    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "content": response,
            "format": self.format.value
        }


# Adapter registry
ADAPTERS: Dict[ContentFormat, type] = {
    ContentFormat.TWITTER_THREAD: TwitterThreadAdapter,
    ContentFormat.LINKEDIN_POST: LinkedInPostAdapter,
    ContentFormat.EMAIL_NEWSLETTER: EmailNewsletterAdapter,
    ContentFormat.YOUTUBE_SCRIPT: YouTubeScriptAdapter,
    ContentFormat.INSTAGRAM_CAROUSEL: InstagramCarouselAdapter,
    ContentFormat.PODCAST_NOTES: PodcastNotesAdapter,
}


def get_adapter(format: ContentFormat, provider_type: str = "openai") -> FormatAdapter:
    """Get the appropriate adapter for a format."""
    adapter_class = ADAPTERS.get(format)
    if adapter_class:
        return adapter_class(provider_type)
    return GenericAdapter(format, provider_type)
