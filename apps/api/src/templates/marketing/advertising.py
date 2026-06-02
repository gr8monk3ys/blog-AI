"""Marketing templates: advertising category."""

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
        "id": "google-search-ad",
        "name": "Google Search Ad",
        "category": "advertising",
        "description": "Generate compelling Google Search ad copy with multiple headlines and descriptions that fit character limits.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _text_field(
                "keywords_targeted",
                required=False,
                placeholder="Comma-separated target keywords",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are an expert Google Ads copywriter. Generate Google Search ad copy for "
            "'{product_name}' highlighting the benefit: '{key_benefit}'.\n"
            "Target audience: {target_audience}\n"
            "Target keywords: {keywords_targeted}\n"
            "Tone: {tone}\n"
            "Call to action: {call_to_action}\n\n"
            "Requirements:\n"
            "- Provide 5 headlines (max 30 characters each)\n"
            "- Provide 3 descriptions (max 90 characters each)\n"
            "- Include the primary keyword naturally\n"
            "- Use strong action verbs and urgency where appropriate\n\n"
            "Return the result as JSON with keys 'headlines' (list of strings) and "
            "'descriptions' (list of strings)."
        ),
        "output_format": {"headlines": "list[str]", "descriptions": "list[str]"},
        "char_limits": {"headline": 30, "description": 90},
    },
    {
        "id": "facebook-ad",
        "name": "Facebook Ad",
        "category": "advertising",
        "description": "Create Facebook ad copy with primary text, headline, and description optimized for engagement.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field(
                "objective",
                ["awareness", "traffic", "engagement", "leads", "sales"],
                default="traffic",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a Facebook advertising specialist. Write ad copy for '{product_name}' "
            "with the key benefit: '{key_benefit}'.\n"
            "Target audience: {target_audience}\n"
            "Campaign objective: {objective}\n"
            "Tone: {tone}\n"
            "Call to action: {call_to_action}\n\n"
            "Provide:\n"
            "- primary_text: The main ad text (125 characters recommended, 3 variations)\n"
            "- headline: The bold headline below the image (40 characters max, 3 variations)\n"
            "- description: Supporting text (30 characters max, 2 variations)\n\n"
            "Return as JSON with keys 'primary_text', 'headline', 'description' each as lists."
        ),
        "output_format": {
            "primary_text": "list[str]",
            "headline": "list[str]",
            "description": "list[str]",
        },
        "char_limits": {"primary_text": 125, "headline": 40, "description": 30},
    },
    {
        "id": "instagram-ad-caption",
        "name": "Instagram Ad Caption",
        "category": "advertising",
        "description": "Write scroll-stopping Instagram ad captions with hashtags and call-to-action.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field(
                "format",
                ["single_image", "carousel", "reel", "story"],
                default="single_image",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are an Instagram marketing expert. Write an ad caption for '{product_name}' "
            "in {format} format.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Hook in the first line (max 125 characters before 'more')\n"
            "- Body text with value proposition\n"
            "- Clear call-to-action\n"
            "- 5-10 relevant hashtags\n"
            "- Keep under 2200 characters total\n\n"
            "Return as JSON with keys 'caption' (string) and 'hashtags' (list of strings)."
        ),
        "output_format": {"caption": "str", "hashtags": "list[str]"},
        "char_limits": {"caption": 2200},
    },
    {
        "id": "linkedin-sponsored-post",
        "name": "LinkedIn Sponsored Post",
        "category": "advertising",
        "description": "Create professional LinkedIn sponsored content optimized for B2B engagement.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field(
                "format",
                ["single_image", "carousel", "video", "document"],
                default="single_image",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a LinkedIn advertising specialist for B2B companies. Write sponsored "
            "post copy for '{product_name}' in {format} format.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Professional and credibility-focused\n"
            "- Open with a hook or surprising stat\n"
            "- Highlight ROI or measurable outcomes\n"
            "- Include a clear CTA\n"
            "- Introductory text: max 150 characters (before 'see more')\n"
            "- Full text: max 600 characters\n\n"
            "Return as JSON with keys 'intro_text' (string), 'full_text' (string), "
            "and 'headline' (string, max 70 chars)."
        ),
        "output_format": {"intro_text": "str", "full_text": "str", "headline": "str"},
        "char_limits": {"intro_text": 150, "full_text": 600, "headline": 70},
    },
    {
        "id": "youtube-ad-script",
        "name": "YouTube Ad Script",
        "category": "advertising",
        "description": "Write YouTube pre-roll or mid-roll ad scripts in 15-second and 30-second variants.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field("duration", ["15s", "30s", "60s"], default="30s"),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a YouTube advertising scriptwriter. Write a {duration} video ad script "
            "for '{product_name}'.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Hook in the first 5 seconds (unskippable window)\n"
            "- Clear problem/solution narrative\n"
            "- End with a strong CTA\n"
            "- Include visual direction notes in brackets\n"
            "- Word count appropriate for {duration}\n\n"
            "Return as JSON with keys 'script' (string with visual cues in brackets), "
            "'hook' (string, first 5s), and 'cta_text' (string)."
        ),
        "output_format": {"script": "str", "hook": "str", "cta_text": "str"},
        "char_limits": {},
    },
    {
        "id": "twitter-promoted-post",
        "name": "Twitter/X Promoted Post",
        "category": "advertising",
        "description": "Write promoted posts for Twitter/X optimized for engagement and clicks.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field(
                "objective",
                ["website_clicks", "engagement", "followers", "app_installs"],
                default="website_clicks",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a Twitter/X advertising expert. Write promoted post copy for "
            "'{product_name}' with objective: {objective}.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Max 280 characters\n"
            "- Generate 3 variations\n"
            "- Include a hook or question to drive engagement\n"
            "- Leave room for a link (assume 23 chars for URL)\n\n"
            "Return as JSON with key 'posts' (list of strings)."
        ),
        "output_format": {"posts": "list[str]"},
        "char_limits": {"post": 280},
    },
    {
        "id": "google-display-ad",
        "name": "Google Display Ad Copy",
        "category": "advertising",
        "description": "Generate responsive display ad copy for Google Display Network campaigns.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a Google Display Network advertising specialist. Write responsive "
            "display ad copy for '{product_name}'.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Short headlines: 5 options (max 30 characters each)\n"
            "- Long headline: 1 option (max 90 characters)\n"
            "- Descriptions: 3 options (max 90 characters each)\n"
            "- Business name suggestion\n\n"
            "Return as JSON with keys 'short_headlines' (list), 'long_headline' (string), "
            "'descriptions' (list), and 'business_name' (string)."
        ),
        "output_format": {
            "short_headlines": "list[str]",
            "long_headline": "str",
            "descriptions": "list[str]",
            "business_name": "str",
        },
        "char_limits": {"short_headline": 30, "long_headline": 90, "description": 90},
    },
    {
        "id": "tiktok-ad-script",
        "name": "TikTok Ad Script",
        "category": "advertising",
        "description": "Write native-feeling TikTok ad scripts that blend with organic content.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _select_field(
                "style", ["ugc", "talking_head", "demo", "storytelling"], default="ugc"
            ),
            _select_field("duration", ["15s", "30s", "60s"], default="30s"),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a TikTok ad creative strategist. Write a {duration} {style} ad script "
            "for '{product_name}'.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Hook in the first 2 seconds\n"
            "- Native, authentic feel (not overly polished)\n"
            "- Clear value proposition\n"
            "- Include on-screen text suggestions\n"
            "- End with CTA overlay\n\n"
            "Return as JSON with keys 'script' (string), 'hook' (string), "
            "'on_screen_text' (list of strings), and 'cta_overlay' (string)."
        ),
        "output_format": {
            "script": "str",
            "hook": "str",
            "on_screen_text": "list[str]",
            "cta_overlay": "str",
        },
        "char_limits": {},
    },
    {
        "id": "pinterest-pin-description",
        "name": "Pinterest Pin Description",
        "category": "advertising",
        "description": "Write SEO-optimized Pinterest pin descriptions that drive saves and clicks.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _KEYWORDS,
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a Pinterest marketing specialist. Write a pin description for "
            "'{product_name}'.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Keywords: {keywords}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Max 500 characters\n"
            "- Front-load keywords naturally\n"
            "- Include a clear CTA\n"
            "- Inspire action (save, click, try)\n"
            "- Generate 3 variations\n\n"
            "Return as JSON with key 'descriptions' (list of strings)."
        ),
        "output_format": {"descriptions": "list[str]"},
        "char_limits": {"description": 500},
    },
    {
        "id": "reddit-promoted-post",
        "name": "Reddit Promoted Post",
        "category": "advertising",
        "description": "Write Reddit-native promoted posts that feel like authentic community contributions.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _TARGET_AUDIENCE,
            _text_field(
                "subreddit_context",
                required=False,
                placeholder="Target subreddit or community topic",
            ),
            _TONE_FIELD,
            _CTA,
        ],
        "prompt_template": (
            "You are a Reddit advertising specialist. Write a promoted post for "
            "'{product_name}' targeting the {subreddit_context} community.\n"
            "Key benefit: {key_benefit}\n"
            "Target audience: {target_audience}\n"
            "Tone: {tone}\n"
            "CTA: {call_to_action}\n\n"
            "Requirements:\n"
            "- Title: max 300 characters, conversational and non-salesy\n"
            "- Body: informative, value-first approach\n"
            "- Avoid corporate jargon; match Reddit culture\n"
            "- Generate 3 title variations and 1 body\n\n"
            "Return as JSON with keys 'titles' (list of strings) and 'body' (string)."
        ),
        "output_format": {"titles": "list[str]", "body": "str"},
        "char_limits": {"title": 300},
    },
]
