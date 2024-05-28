"""Marketing templates: social_media category."""

from src.templates._fields import (
    _BRAND_VOICE,
    _CTA,
    _KEY_BENEFIT,
    _KEYWORDS,
    _PRODUCT_NAME,
    _TARGET_AUDIENCE,
    _TONE_FIELD,
    _TONE_OPTIONS,
    _select_field,
    _text_field,
    _textarea_field,
)

TEMPLATES = [
    {
        "id": "twitter-thread",
        "name": "Twitter/X Thread",
        "category": "social_media",
        "description": "Create engaging Twitter/X threads that educate, entertain, or promote.",
        "fields": [
            _text_field("topic", placeholder="Thread topic"),
            _textarea_field(
                "key_points", required=True, placeholder="Key points to cover"
            ),
            _select_field("thread_length", ["5", "7", "10", "15"], default="7"),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "Write a {thread_length}-tweet Twitter/X thread about '{topic}'.\n"
            "Key points:\n{key_points}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Each tweet max 280 characters\n"
            "- First tweet: strong hook, promise value\n"
            "- Number each tweet (1/n format)\n"
            "- Use line breaks for readability\n"
            "- Last tweet: CTA + invite to retweet/follow\n"
            "- No hashtags in thread (except optionally in last tweet)\n\n"
            "Return as JSON with key 'tweets' (list of strings)."
        ),
        "output_format": {"tweets": "list[str]"},
        "char_limits": {"tweet": 280},
    },
    {
        "id": "linkedin-article-intro",
        "name": "LinkedIn Article Intro",
        "category": "social_media",
        "description": "Write compelling LinkedIn article introductions that hook professional readers.",
        "fields": [
            _text_field("article_topic", placeholder="Article topic"),
            _textarea_field(
                "key_insight", required=True, placeholder="Main insight or argument"
            ),
            _TARGET_AUDIENCE,
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write a LinkedIn article introduction about '{article_topic}'.\n"
            "Main insight: {key_insight}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n\n"
            "Requirements:\n"
            "- Headline: max 70 characters, curiosity-driven\n"
            "- Opening hook: 1-2 sentences, challenge conventional wisdom or share a stat\n"
            "- Context paragraph: 2-3 sentences, establish credibility\n"
            "- Promise statement: what the reader will learn\n"
            "- 100-150 words total\n"
            "- Generate 2 variations\n\n"
            "Return as JSON with key 'variations' (list of dicts with "
            "'headline', 'hook', 'context', 'promise')."
        ),
        "output_format": {"variations": "list[dict]"},
        "char_limits": {"headline": 70},
    },
    {
        "id": "instagram-carousel-script",
        "name": "Instagram Carousel Script",
        "category": "social_media",
        "description": "Write text content for Instagram carousel posts (slide-by-slide).",
        "fields": [
            _text_field("topic", placeholder="Carousel topic"),
            _textarea_field(
                "key_points", required=True, placeholder="Key points to cover"
            ),
            _select_field("slide_count", ["5", "7", "10"], default="7"),
            _TARGET_AUDIENCE,
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write a {slide_count}-slide Instagram carousel about '{topic}'.\n"
            "Key points:\n{key_points}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n\n"
            "Requirements:\n"
            "- Slide 1: Eye-catching title/hook\n"
            "- Middle slides: One point per slide, concise text\n"
            "- Last slide: CTA (save, share, follow)\n"
            "- Each slide: headline (max 5 words) + body (max 30 words)\n"
            "- Include a caption for the post\n\n"
            "Return as JSON with keys 'slides' (list of dicts with 'headline' and 'body') "
            "and 'caption' (string)."
        ),
        "output_format": {"slides": "list[dict]", "caption": "str"},
        "char_limits": {},
    },
    {
        "id": "youtube-video-description",
        "name": "YouTube Video Description",
        "category": "social_media",
        "description": "Write SEO-optimized YouTube video descriptions with timestamps and links.",
        "fields": [
            _text_field("video_title", placeholder="Video title"),
            _textarea_field(
                "video_summary",
                required=True,
                placeholder="Brief summary of the video content",
            ),
            _KEYWORDS,
            _text_field(
                "channel_name", required=False, placeholder="Your channel name"
            ),
            _CTA,
        ],
        "prompt_template": (
            "Write a YouTube video description for '{video_title}'.\n"
            "Video summary: {video_summary}\n"
            "Keywords: {keywords}\n"
            "Channel: {channel_name}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- First 2 lines: Hook + primary keyword (visible before 'Show more')\n"
            "- Detailed description: 150-200 words\n"
            "- Suggested timestamps section (5-8 entries)\n"
            "- Include keywords naturally\n"
            "- Links section placeholder\n"
            "- Hashtags: 3-5 relevant\n\n"
            "Return as JSON with keys 'description' (string), "
            "'timestamps' (list of dicts with 'time' and 'label'), "
            "and 'hashtags' (list of strings)."
        ),
        "output_format": {
            "description": "str",
            "timestamps": "list[dict]",
            "hashtags": "list[str]",
        },
        "char_limits": {},
    },
    {
        "id": "tiktok-caption",
        "name": "TikTok Caption",
        "category": "social_media",
        "description": "Write TikTok captions optimized for discoverability and engagement.",
        "fields": [
            _text_field("video_topic", placeholder="What the video is about"),
            _text_field(
                "hook", required=False, placeholder="Opening hook or text overlay"
            ),
            _TARGET_AUDIENCE,
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write TikTok captions for a video about '{video_topic}'.\n"
            "Hook: {hook}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n\n"
            "Requirements:\n"
            "- Max 150 characters (short, punchy)\n"
            "- Include 3-5 relevant hashtags\n"
            "- Generate 5 variations\n"
            "- Mix of styles: question, statement, challenge, relatable\n\n"
            "Return as JSON with key 'captions' (list of dicts with 'text' and 'hashtags')."
        ),
        "output_format": {"captions": "list[dict]"},
        "char_limits": {"caption": 150},
    },
    {
        "id": "facebook-group-post",
        "name": "Facebook Group Post",
        "category": "social_media",
        "description": "Write engaging Facebook group posts that spark discussion.",
        "fields": [
            _text_field("topic", placeholder="Post topic"),
            _text_field(
                "group_context", required=False, placeholder="Group name or niche"
            ),
            _select_field(
                "post_type",
                ["question", "tip", "story", "poll", "resource_share"],
                default="question",
            ),
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write a Facebook group post about '{topic}' for the {group_context} community.\n"
            "Post type: {post_type}\n"
            "Tone: {tone}\n\n"
            "Requirements:\n"
            "- Open with a relatable statement or question\n"
            "- Provide value (tip, insight, or resource)\n"
            "- End with a question to encourage comments\n"
            "- Keep conversational, not promotional\n"
            "- 100-200 words\n"
            "- Generate 2 variations\n\n"
            "Return as JSON with key 'posts' (list of strings)."
        ),
        "output_format": {"posts": "list[str]"},
        "char_limits": {},
    },
    {
        "id": "social-media-bio",
        "name": "Social Media Bio",
        "category": "social_media",
        "description": "Write compelling social media bios for multiple platforms.",
        "fields": [
            _text_field("name_or_brand", placeholder="Person or brand name"),
            _text_field(
                "role_or_niche", placeholder="e.g. SaaS Founder, Fitness Coach"
            ),
            _KEY_BENEFIT,
            _text_field(
                "unique_trait", required=False, placeholder="What makes you different"
            ),
            _CTA,
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write social media bios for '{name_or_brand}' ({role_or_niche}).\n"
            "Key benefit/value: {key_benefit}\n"
            "Unique trait: {unique_trait}\n"
            "CTA: {call_to_action}\n"
            "Tone: {tone}\n\n"
            "Requirements:\n"
            "Generate platform-specific bios:\n"
            "- Twitter/X: max 160 characters\n"
            "- Instagram: max 150 characters\n"
            "- LinkedIn: max 220 characters (headline)\n"
            "- TikTok: max 80 characters\n\n"
            "Return as JSON with keys 'twitter' (string), 'instagram' (string), "
            "'linkedin' (string), and 'tiktok' (string)."
        ),
        "output_format": {
            "twitter": "str",
            "instagram": "str",
            "linkedin": "str",
            "tiktok": "str",
        },
        "char_limits": {
            "twitter": 160,
            "instagram": 150,
            "linkedin": 220,
            "tiktok": 80,
        },
    },
    {
        "id": "hashtag-generator",
        "name": "Hashtag Generator",
        "category": "social_media",
        "description": "Generate relevant hashtag sets optimized for reach and engagement.",
        "fields": [
            _text_field("topic", placeholder="Content topic"),
            _text_field("niche", required=False, placeholder="Your niche or industry"),
            _select_field(
                "platform",
                ["instagram", "tiktok", "twitter", "linkedin"],
                default="instagram",
            ),
            _select_field(
                "strategy", ["reach", "engagement", "niche", "mixed"], default="mixed"
            ),
        ],
        "prompt_template": (
            "Generate hashtags for '{topic}' on {platform}.\n"
            "Niche: {niche}\n"
            "Strategy: {strategy}\n\n"
            "Requirements:\n"
            "- Generate 30 hashtags total\n"
            "- Categorize into: high-volume (1M+), medium (100K-1M), niche (<100K)\n"
            "- For 'reach' strategy: more high-volume tags\n"
            "- For 'engagement' strategy: more medium tags\n"
            "- For 'niche' strategy: more niche-specific tags\n"
            "- For 'mixed': balanced distribution\n"
            "- Include relevant branded hashtag suggestions\n\n"
            "Return as JSON with keys 'high_volume' (list), 'medium' (list), "
            "'niche' (list), and 'branded' (list)."
        ),
        "output_format": {
            "high_volume": "list[str]",
            "medium": "list[str]",
            "niche": "list[str]",
            "branded": "list[str]",
        },
        "char_limits": {},
    },
]
