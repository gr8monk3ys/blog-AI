"""
Marketing copy template library.

Contains 52 production-ready templates organized across 7 categories.
Each template defines its input fields, prompt template, expected output
format, and character limits where applicable.
"""

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Shared field definitions (DRY helpers)
# ---------------------------------------------------------------------------

def _text_field(
    name: str,
    *,
    required: bool = True,
    placeholder: str = "",
    description: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "type": "text",
        "required": required,
        "placeholder": placeholder,
        "description": description,
    }


def _textarea_field(
    name: str,
    *,
    required: bool = False,
    placeholder: str = "",
    description: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "type": "textarea",
        "required": required,
        "placeholder": placeholder,
        "description": description,
    }


def _select_field(
    name: str,
    options: List[str],
    *,
    default: str = "",
    required: bool = False,
    description: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "type": "select",
        "options": options,
        "default": default or options[0],
        "required": required,
        "description": description,
    }


_TONE_OPTIONS = ["professional", "casual", "urgent", "friendly", "authoritative", "playful"]
_TONE_FIELD = _select_field("tone", _TONE_OPTIONS, default="professional", description="Voice tone")

_PRODUCT_NAME = _text_field("product_name", placeholder="Your product or service name")
_KEY_BENEFIT = _text_field("key_benefit", placeholder="Main benefit or value proposition")
_TARGET_AUDIENCE = _text_field(
    "target_audience",
    required=False,
    placeholder="e.g. SaaS founders, busy parents, fitness enthusiasts",
)
_CTA = _text_field("call_to_action", required=False, placeholder="e.g. Sign Up Free, Shop Now")
_BRAND_VOICE = _textarea_field(
    "brand_voice",
    placeholder="Describe your brand voice or paste a brand voice summary",
    description="Optional brand voice guidance",
)
_KEYWORDS = _text_field(
    "keywords",
    required=False,
    placeholder="Comma-separated keywords for SEO",
)


# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

TEMPLATE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "advertising": {
        "name": "Advertising",
        "description": "Paid ad copy for search, social, display, and video platforms",
        "icon": "megaphone",
    },
    "product": {
        "name": "Product & E-commerce",
        "description": "Product descriptions, listings, and launch announcements",
        "icon": "shopping-bag",
    },
    "email": {
        "name": "Email Marketing",
        "description": "Transactional, promotional, and lifecycle email copy",
        "icon": "mail",
    },
    "landing_page": {
        "name": "Landing Pages",
        "description": "High-converting landing page sections and copy blocks",
        "icon": "layout",
    },
    "social_media": {
        "name": "Social Media",
        "description": "Organic social posts, threads, bios, and captions",
        "icon": "share-2",
    },
    "business": {
        "name": "Business",
        "description": "Press releases, case studies, mission statements, and corporate copy",
        "icon": "briefcase",
    },
    "other": {
        "name": "Other",
        "description": "SEO metadata, app store copy, event descriptions, and more",
        "icon": "file-text",
    },
}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

MARKETING_TEMPLATES: Dict[str, Dict[str, Any]] = {}


def _register(template: Dict[str, Any]) -> None:
    """Register a template in the global dictionary keyed by its id."""
    MARKETING_TEMPLATES[template["id"]] = template


# ============================= ADVERTISING (10) =============================

_register({
    "id": "google-search-ad",
    "name": "Google Search Ad",
    "category": "advertising",
    "description": "Generate compelling Google Search ad copy with multiple headlines and descriptions that fit character limits.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _text_field("keywords_targeted", required=False, placeholder="Comma-separated target keywords"),
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
})

_register({
    "id": "facebook-ad",
    "name": "Facebook Ad",
    "category": "advertising",
    "description": "Create Facebook ad copy with primary text, headline, and description optimized for engagement.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _select_field("objective", ["awareness", "traffic", "engagement", "leads", "sales"], default="traffic"),
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
    "output_format": {"primary_text": "list[str]", "headline": "list[str]", "description": "list[str]"},
    "char_limits": {"primary_text": 125, "headline": 40, "description": 30},
})

_register({
    "id": "instagram-ad-caption",
    "name": "Instagram Ad Caption",
    "category": "advertising",
    "description": "Write scroll-stopping Instagram ad captions with hashtags and call-to-action.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _select_field("format", ["single_image", "carousel", "reel", "story"], default="single_image"),
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
})

_register({
    "id": "linkedin-sponsored-post",
    "name": "LinkedIn Sponsored Post",
    "category": "advertising",
    "description": "Create professional LinkedIn sponsored content optimized for B2B engagement.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _select_field("format", ["single_image", "carousel", "video", "document"], default="single_image"),
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
})

_register({
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
})

_register({
    "id": "twitter-promoted-post",
    "name": "Twitter/X Promoted Post",
    "category": "advertising",
    "description": "Write promoted posts for Twitter/X optimized for engagement and clicks.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _select_field("objective", ["website_clicks", "engagement", "followers", "app_installs"], default="website_clicks"),
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
})

_register({
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
})

_register({
    "id": "tiktok-ad-script",
    "name": "TikTok Ad Script",
    "category": "advertising",
    "description": "Write native-feeling TikTok ad scripts that blend with organic content.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _select_field("style", ["ugc", "talking_head", "demo", "storytelling"], default="ugc"),
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
    "output_format": {"script": "str", "hook": "str", "on_screen_text": "list[str]", "cta_overlay": "str"},
    "char_limits": {},
})

_register({
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
})

_register({
    "id": "reddit-promoted-post",
    "name": "Reddit Promoted Post",
    "category": "advertising",
    "description": "Write Reddit-native promoted posts that feel like authentic community contributions.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _text_field("subreddit_context", required=False, placeholder="Target subreddit or community topic"),
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
})


# ======================== PRODUCT & E-COMMERCE (8) ==========================

_register({
    "id": "product-description-short",
    "name": "Product Description (Short)",
    "category": "product",
    "description": "Generate concise product descriptions optimized for quick scanning and conversion.",
    "fields": [
        _PRODUCT_NAME,
        _text_field("product_type", placeholder="e.g. wireless earbuds, organic shampoo"),
        _KEY_BENEFIT,
        _text_field("key_features", required=False, placeholder="Comma-separated features"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a short, compelling product description for '{product_name}' "
        "({product_type}).\n"
        "Key benefit: {key_benefit}\n"
        "Key features: {key_features}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- 50-100 words\n"
        "- Lead with the primary benefit\n"
        "- Include 2-3 key features naturally\n"
        "- End with a subtle CTA\n"
        "- Generate 3 variations\n\n"
        "Return as JSON with key 'descriptions' (list of strings)."
    ),
    "output_format": {"descriptions": "list[str]"},
    "char_limits": {},
})

_register({
    "id": "product-description-long",
    "name": "Product Description (Long/Story)",
    "category": "product",
    "description": "Create detailed, story-driven product descriptions that build emotional connection.",
    "fields": [
        _PRODUCT_NAME,
        _text_field("product_type", placeholder="e.g. handcrafted leather bag"),
        _KEY_BENEFIT,
        _textarea_field("features_details", required=True, placeholder="Detailed features and specs"),
        _TARGET_AUDIENCE,
        _textarea_field("brand_story", placeholder="Brief brand story or origin"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a detailed, story-driven product description for '{product_name}' "
        "({product_type}).\n"
        "Key benefit: {key_benefit}\n"
        "Features: {features_details}\n"
        "Target audience: {target_audience}\n"
        "Brand story: {brand_story}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- 200-400 words\n"
        "- Open with an emotional hook or relatable scenario\n"
        "- Weave in the brand story naturally\n"
        "- Detail features as benefits\n"
        "- Use sensory language\n"
        "- Close with a compelling CTA\n\n"
        "Return as JSON with key 'description' (string)."
    ),
    "output_format": {"description": "str"},
    "char_limits": {},
})

_register({
    "id": "product-feature-bullets",
    "name": "Product Feature Bullets",
    "category": "product",
    "description": "Generate benefit-driven feature bullet points for product pages.",
    "fields": [
        _PRODUCT_NAME,
        _textarea_field("features_list", required=True, placeholder="List your product features, one per line"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Convert the following raw features of '{product_name}' into compelling, "
        "benefit-driven bullet points.\n"
        "Raw features:\n{features_list}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Lead each bullet with the benefit, then the feature\n"
        "- Keep each bullet under 150 characters\n"
        "- Use consistent structure across bullets\n"
        "- Generate 5-8 bullets\n\n"
        "Return as JSON with key 'bullets' (list of strings)."
    ),
    "output_format": {"bullets": "list[str]"},
    "char_limits": {"bullet": 150},
})

_register({
    "id": "product-comparison",
    "name": "Product Comparison",
    "category": "product",
    "description": "Generate product comparison copy positioning your product against competitors.",
    "fields": [
        _PRODUCT_NAME,
        _text_field("competitor_name", placeholder="Main competitor"),
        _textarea_field("your_advantages", required=True, placeholder="Key advantages over competitor"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a product comparison between '{product_name}' and '{competitor_name}'.\n"
        "Key advantages of {product_name}: {your_advantages}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Fair but persuasive framing\n"
        "- Highlight 3-5 comparison points\n"
        "- Provide a summary paragraph recommending your product\n"
        "- Do not trash the competitor; focus on your strengths\n\n"
        "Return as JSON with keys 'comparison_points' (list of dicts with "
        "'feature', 'your_product', 'competitor') and 'summary' (string)."
    ),
    "output_format": {"comparison_points": "list[dict]", "summary": "str"},
    "char_limits": {},
})

_register({
    "id": "product-review-response",
    "name": "Product Review Response",
    "category": "product",
    "description": "Draft professional responses to product reviews (positive and negative).",
    "fields": [
        _PRODUCT_NAME,
        _textarea_field("review_text", required=True, placeholder="Paste the customer review"),
        _select_field("review_sentiment", ["positive", "negative", "mixed"], default="positive"),
        _text_field("company_name", placeholder="Your company name"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a professional response to this {review_sentiment} review of "
        "'{product_name}' on behalf of {company_name}.\n\n"
        "Customer review:\n\"{review_text}\"\n\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Thank the customer\n"
        "- Address specific points from their review\n"
        "- If negative: acknowledge concern, offer solution, invite offline resolution\n"
        "- If positive: express gratitude, reinforce their positive experience\n"
        "- Keep under 150 words\n"
        "- Professional and empathetic\n\n"
        "Return as JSON with key 'response' (string)."
    ),
    "output_format": {"response": "str"},
    "char_limits": {},
})

_register({
    "id": "amazon-product-listing",
    "name": "Amazon Product Listing",
    "category": "product",
    "description": "Create optimized Amazon product listing with title, bullets, and description.",
    "fields": [
        _PRODUCT_NAME,
        _text_field("product_type", placeholder="Product category"),
        _textarea_field("features_details", required=True, placeholder="All features and specs"),
        _KEYWORDS,
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "You are an Amazon listing optimization expert. Create a product listing "
        "for '{product_name}' ({product_type}).\n"
        "Features: {features_details}\n"
        "Keywords: {keywords}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Title: max 200 characters, keyword-rich, brand + key features\n"
        "- 5 bullet points: benefit-first, max 500 characters each\n"
        "- Product description: 300-500 words, use HTML where appropriate\n"
        "- Backend search terms: 5 keyword phrases\n\n"
        "Return as JSON with keys 'title' (string), 'bullets' (list of strings), "
        "'description' (string), and 'search_terms' (list of strings)."
    ),
    "output_format": {
        "title": "str",
        "bullets": "list[str]",
        "description": "str",
        "search_terms": "list[str]",
    },
    "char_limits": {"title": 200, "bullet": 500},
})

_register({
    "id": "shopify-product-page",
    "name": "Shopify Product Page",
    "category": "product",
    "description": "Write complete Shopify product page copy including title, description, and SEO.",
    "fields": [
        _PRODUCT_NAME,
        _text_field("product_type", placeholder="Product type/category"),
        _text_field("price", required=False, placeholder="e.g. $49.99"),
        _textarea_field("features_details", required=True, placeholder="Features and specifications"),
        _TARGET_AUDIENCE,
        _KEYWORDS,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write complete Shopify product page copy for '{product_name}' ({product_type}).\n"
        "Price: {price}\n"
        "Features: {features_details}\n"
        "Target audience: {target_audience}\n"
        "Keywords: {keywords}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- SEO title: max 70 characters\n"
        "- Meta description: max 160 characters\n"
        "- Product description: 150-300 words, scannable with headers\n"
        "- Feature highlights section\n"
        "- Social proof / trust signals suggestion\n\n"
        "Return as JSON with keys 'seo_title' (string), 'meta_description' (string), "
        "'product_description' (string), 'feature_highlights' (list of strings), "
        "and 'trust_signals' (list of strings)."
    ),
    "output_format": {
        "seo_title": "str",
        "meta_description": "str",
        "product_description": "str",
        "feature_highlights": "list[str]",
        "trust_signals": "list[str]",
    },
    "char_limits": {"seo_title": 70, "meta_description": 160},
})

_register({
    "id": "product-launch-announcement",
    "name": "Product Launch Announcement",
    "category": "product",
    "description": "Generate product launch announcement copy for multiple channels.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _textarea_field("launch_details", required=True, placeholder="Launch date, availability, pricing"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a product launch announcement for '{product_name}'.\n"
        "Key benefit: {key_benefit}\n"
        "Launch details: {launch_details}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Generate versions for:\n"
        "1. Email announcement (subject line + body, 200 words)\n"
        "2. Social media post (280 chars for Twitter, 300 chars for LinkedIn)\n"
        "3. Blog intro paragraph (100 words)\n\n"
        "Return as JSON with keys 'email_subject' (string), 'email_body' (string), "
        "'twitter_post' (string), 'linkedin_post' (string), and 'blog_intro' (string)."
    ),
    "output_format": {
        "email_subject": "str",
        "email_body": "str",
        "twitter_post": "str",
        "linkedin_post": "str",
        "blog_intro": "str",
    },
    "char_limits": {"twitter_post": 280, "linkedin_post": 300},
})


# ============================ EMAIL MARKETING (8) ===========================

_register({
    "id": "welcome-email",
    "name": "Welcome Email",
    "category": "email",
    "description": "Write an engaging welcome email for new subscribers or customers.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _text_field("offer", required=False, placeholder="e.g. 10% off first order"),
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a welcome email for new subscribers to {company_name}.\n"
        "Product: {product_name}\n"
        "Key benefit: {key_benefit}\n"
        "Special offer: {offer}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Subject line: max 50 characters, 3 variations\n"
        "- Preview text: max 90 characters\n"
        "- Body: warm, sets expectations, delivers value immediately\n"
        "- Include the offer if provided\n"
        "- Clear single CTA\n"
        "- 150-200 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "newsletter-email",
    "name": "Newsletter",
    "category": "email",
    "description": "Create newsletter email copy with engaging sections and curated content.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _text_field("newsletter_topic", placeholder="Main topic or theme"),
        _textarea_field("key_points", required=True, placeholder="Key points or stories to cover"),
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a newsletter email for {company_name} about '{newsletter_topic}'.\n"
        "Key points to cover:\n{key_points}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars)\n"
        "- Preview text: max 90 characters\n"
        "- Opening hook: personal, relatable\n"
        "- 2-3 content sections with headers\n"
        "- Brief, scannable paragraphs\n"
        "- Closing with CTA\n"
        "- 300-500 words total\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "promotional-email",
    "name": "Promotional Email",
    "category": "email",
    "description": "Write compelling promotional emails for sales, launches, and special offers.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _text_field("promotion_details", placeholder="e.g. 30% off, buy one get one free"),
        _text_field("deadline", required=False, placeholder="e.g. Ends Friday, Limited to 100"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a promotional email for {company_name} about '{product_name}'.\n"
        "Promotion: {promotion_details}\n"
        "Deadline/Urgency: {deadline}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations with urgency (max 50 chars)\n"
        "- Preview text with offer highlight\n"
        "- Body: lead with the offer, explain the value, create urgency\n"
        "- Single, prominent CTA\n"
        "- 100-200 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "cart-abandonment-email",
    "name": "Cart Abandonment Email",
    "category": "email",
    "description": "Recover lost sales with persuasive cart abandonment email sequences.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _text_field("incentive", required=False, placeholder="e.g. 10% discount, free shipping"),
        _select_field("sequence_position", ["first_reminder", "second_reminder", "final_reminder"], default="first_reminder"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a cart abandonment email ({sequence_position}) for {company_name}.\n"
        "Product left in cart: {product_name}\n"
        "Incentive: {incentive}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars)\n"
        "- For first_reminder: gentle, helpful reminder\n"
        "- For second_reminder: add social proof, create mild urgency\n"
        "- For final_reminder: strongest urgency, offer incentive if available\n"
        "- Include a 'return to cart' CTA\n"
        "- 80-150 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "re-engagement-email",
    "name": "Re-engagement Email",
    "category": "email",
    "description": "Win back inactive subscribers with compelling re-engagement campaigns.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _KEY_BENEFIT,
        _text_field("incentive", required=False, placeholder="Special offer to re-engage"),
        _text_field("inactivity_period", required=False, placeholder="e.g. 3 months, 6 months"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a re-engagement email for {company_name} targeting subscribers "
        "inactive for {inactivity_period}.\n"
        "Key benefit reminder: {key_benefit}\n"
        "Re-engagement incentive: {incentive}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (personal, curiosity-driven, max 50 chars)\n"
        "- Acknowledge absence without guilt-tripping\n"
        "- Remind them of the value they are missing\n"
        "- Offer incentive if available\n"
        "- Include easy opt-out option (mention 'unsubscribe if no longer interested')\n"
        "- 100-150 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "product-update-email",
    "name": "Product Update Email",
    "category": "email",
    "description": "Announce new features and product updates to keep users engaged.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _textarea_field("update_details", required=True, placeholder="New features, improvements, changes"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a product update email for {company_name} about '{product_name}'.\n"
        "Updates:\n{update_details}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars)\n"
        "- Lead with the most impactful change\n"
        "- Use bullet points for feature list\n"
        "- Explain the 'why' behind each update\n"
        "- Close with a CTA to try the new features\n"
        "- 150-250 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "event-invitation-email",
    "name": "Event Invitation Email",
    "category": "email",
    "description": "Create event invitation emails that drive RSVPs and attendance.",
    "fields": [
        _text_field("event_name", placeholder="Name of the event"),
        _text_field("event_date", placeholder="Date and time"),
        _text_field("event_location", required=False, placeholder="Venue or 'Virtual'"),
        _textarea_field("event_description", required=True, placeholder="What the event is about"),
        _text_field("speakers", required=False, placeholder="Featured speakers or guests"),
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write an event invitation email for '{event_name}'.\n"
        "Date: {event_date}\n"
        "Location: {event_location}\n"
        "Description: {event_description}\n"
        "Speakers: {speakers}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars)\n"
        "- Highlight what attendees will learn or gain\n"
        "- Include logistics (date, time, location) clearly\n"
        "- Mention speakers if provided\n"
        "- Strong RSVP CTA\n"
        "- 150-200 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'preview_text' (string), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "preview_text": "str", "body": "str"},
    "char_limits": {"subject_line": 50, "preview_text": 90},
})

_register({
    "id": "cold-outreach-email",
    "name": "Cold Outreach Email",
    "category": "email",
    "description": "Write effective cold outreach emails for sales and partnership development.",
    "fields": [
        _text_field("sender_name", placeholder="Your name"),
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _text_field("recipient_role", placeholder="e.g. VP of Marketing, CTO"),
        _text_field("recipient_company", required=False, placeholder="Their company name"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a cold outreach email from {sender_name} at {company_name} to a "
        "{recipient_role} at {recipient_company}.\n"
        "Product: {product_name}\n"
        "Key benefit: {key_benefit}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars, personalized)\n"
        "- Open with a personalized observation or compliment\n"
        "- Identify a relevant pain point\n"
        "- Position your product as the solution (2-3 sentences max)\n"
        "- Low-friction CTA (e.g., 'Would a 15-min call make sense?')\n"
        "- Under 100 words total\n"
        "- No attachments mentioned\n\n"
        "Return as JSON with keys 'subject_lines' (list), and 'body' (string)."
    ),
    "output_format": {"subject_lines": "list[str]", "body": "str"},
    "char_limits": {"subject_line": 50},
})


# ============================== LANDING PAGES (6) ===========================

_register({
    "id": "landing-hero-section",
    "name": "Hero Section",
    "category": "landing_page",
    "description": "Write a high-converting hero section with headline, subheadline, and CTA.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
        _BRAND_VOICE,
    ],
    "prompt_template": (
        "Write hero section copy for a landing page promoting '{product_name}'.\n"
        "Key benefit: {key_benefit}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n"
        "Brand voice: {brand_voice}\n\n"
        "Requirements:\n"
        "- Headline: max 10 words, benefit-driven, emotionally compelling\n"
        "- Subheadline: 15-25 words, elaborates on the headline\n"
        "- CTA button text: 2-5 words\n"
        "- Supporting text: 1-2 sentences for context\n"
        "- Generate 3 variations of each\n\n"
        "Return as JSON with keys 'headlines' (list), 'subheadlines' (list), "
        "'cta_buttons' (list), and 'supporting_text' (list)."
    ),
    "output_format": {
        "headlines": "list[str]",
        "subheadlines": "list[str]",
        "cta_buttons": "list[str]",
        "supporting_text": "list[str]",
    },
    "char_limits": {},
})

_register({
    "id": "landing-features-section",
    "name": "Features Section",
    "category": "landing_page",
    "description": "Create a features section with benefit-driven headlines and descriptions.",
    "fields": [
        _PRODUCT_NAME,
        _textarea_field("features_list", required=True, placeholder="List features, one per line"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write features section copy for '{product_name}' landing page.\n"
        "Features:\n{features_list}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Section headline: benefit-driven\n"
        "- For each feature:\n"
        "  - Feature title (5-8 words, benefit-first)\n"
        "  - Feature description (25-40 words)\n"
        "  - Suggested icon name\n\n"
        "Return as JSON with keys 'section_headline' (string) and "
        "'features' (list of dicts with 'title', 'description', 'icon')."
    ),
    "output_format": {"section_headline": "str", "features": "list[dict]"},
    "char_limits": {},
})

_register({
    "id": "landing-testimonial-request",
    "name": "Testimonial Request",
    "category": "landing_page",
    "description": "Write testimonial request emails and generate structured testimonial outlines.",
    "fields": [
        _text_field("company_name", placeholder="Your company name"),
        _PRODUCT_NAME,
        _text_field("customer_name", required=False, placeholder="Customer name"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a testimonial request email for {company_name} asking a customer "
        "to share their experience with '{product_name}'.\n"
        "Customer name: {customer_name}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Subject line: 3 variations (max 50 chars)\n"
        "- Personalized and respectful request\n"
        "- Include 3-5 guiding questions to help structure their response\n"
        "- Mention how the testimonial will be used\n"
        "- Keep under 150 words\n\n"
        "Return as JSON with keys 'subject_lines' (list), 'email_body' (string), "
        "and 'guiding_questions' (list of strings)."
    ),
    "output_format": {"subject_lines": "list[str]", "email_body": "str", "guiding_questions": "list[str]"},
    "char_limits": {"subject_line": 50},
})

_register({
    "id": "landing-cta-section",
    "name": "CTA Section",
    "category": "landing_page",
    "description": "Create compelling call-to-action sections for landing pages.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _select_field("cta_type", ["signup", "purchase", "demo", "download", "contact"], default="signup"),
        _text_field("offer", required=False, placeholder="e.g. Start free trial, 30-day guarantee"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a CTA section for a '{product_name}' landing page.\n"
        "Key benefit: {key_benefit}\n"
        "CTA type: {cta_type}\n"
        "Offer: {offer}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Section headline: create urgency or excitement\n"
        "- Supporting paragraph: 2-3 sentences reinforcing value\n"
        "- Primary CTA button text: action-oriented, 2-5 words\n"
        "- Secondary CTA text: lower commitment alternative\n"
        "- Trust signal: one-liner (e.g., 'No credit card required')\n"
        "- Generate 3 variations\n\n"
        "Return as JSON with keys 'variations' (list of dicts with "
        "'headline', 'supporting_text', 'primary_cta', 'secondary_cta', 'trust_signal')."
    ),
    "output_format": {"variations": "list[dict]"},
    "char_limits": {},
})

_register({
    "id": "landing-faq-section",
    "name": "FAQ Section",
    "category": "landing_page",
    "description": "Generate FAQ copy for landing pages addressing common objections.",
    "fields": [
        _PRODUCT_NAME,
        _KEY_BENEFIT,
        _textarea_field("common_questions", required=False, placeholder="Common questions from customers"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write an FAQ section for the '{product_name}' landing page.\n"
        "Key benefit: {key_benefit}\n"
        "Known questions: {common_questions}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Generate 8-10 FAQ pairs\n"
        "- Address common objections (price, complexity, trust, competition)\n"
        "- Include known questions if provided\n"
        "- Answers should be concise (2-4 sentences)\n"
        "- Naturally reinforce value proposition\n\n"
        "Return as JSON with key 'faqs' (list of dicts with 'question' and 'answer')."
    ),
    "output_format": {"faqs": "list[dict]"},
    "char_limits": {},
})

_register({
    "id": "landing-pricing-copy",
    "name": "Pricing Page Copy",
    "category": "landing_page",
    "description": "Write persuasive pricing page copy with plan descriptions and feature lists.",
    "fields": [
        _PRODUCT_NAME,
        _textarea_field("plans", required=True, placeholder="List plans with prices and features"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write pricing page copy for '{product_name}'.\n"
        "Plans:\n{plans}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Page headline: value-focused, not just 'Pricing'\n"
        "- Page subheadline: address price sensitivity\n"
        "- For each plan:\n"
        "  - Catchy plan name if not provided\n"
        "  - One-line plan description (who it is for)\n"
        "  - Feature highlights as benefit statements\n"
        "  - CTA button text\n"
        "- Highlight the recommended plan\n"
        "- Add a money-back guarantee statement\n\n"
        "Return as JSON with keys 'page_headline' (string), 'page_subheadline' (string), "
        "'plans' (list of dicts with 'name', 'description', 'features', 'cta'), "
        "and 'guarantee' (string)."
    ),
    "output_format": {
        "page_headline": "str",
        "page_subheadline": "str",
        "plans": "list[dict]",
        "guarantee": "str",
    },
    "char_limits": {},
})


# ============================== SOCIAL MEDIA (8) ============================

_register({
    "id": "twitter-thread",
    "name": "Twitter/X Thread",
    "category": "social_media",
    "description": "Create engaging Twitter/X threads that educate, entertain, or promote.",
    "fields": [
        _text_field("topic", placeholder="Thread topic"),
        _textarea_field("key_points", required=True, placeholder="Key points to cover"),
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
})

_register({
    "id": "linkedin-article-intro",
    "name": "LinkedIn Article Intro",
    "category": "social_media",
    "description": "Write compelling LinkedIn article introductions that hook professional readers.",
    "fields": [
        _text_field("article_topic", placeholder="Article topic"),
        _textarea_field("key_insight", required=True, placeholder="Main insight or argument"),
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
})

_register({
    "id": "instagram-carousel-script",
    "name": "Instagram Carousel Script",
    "category": "social_media",
    "description": "Write text content for Instagram carousel posts (slide-by-slide).",
    "fields": [
        _text_field("topic", placeholder="Carousel topic"),
        _textarea_field("key_points", required=True, placeholder="Key points to cover"),
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
})

_register({
    "id": "youtube-video-description",
    "name": "YouTube Video Description",
    "category": "social_media",
    "description": "Write SEO-optimized YouTube video descriptions with timestamps and links.",
    "fields": [
        _text_field("video_title", placeholder="Video title"),
        _textarea_field("video_summary", required=True, placeholder="Brief summary of the video content"),
        _KEYWORDS,
        _text_field("channel_name", required=False, placeholder="Your channel name"),
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
    "output_format": {"description": "str", "timestamps": "list[dict]", "hashtags": "list[str]"},
    "char_limits": {},
})

_register({
    "id": "tiktok-caption",
    "name": "TikTok Caption",
    "category": "social_media",
    "description": "Write TikTok captions optimized for discoverability and engagement.",
    "fields": [
        _text_field("video_topic", placeholder="What the video is about"),
        _text_field("hook", required=False, placeholder="Opening hook or text overlay"),
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
})

_register({
    "id": "facebook-group-post",
    "name": "Facebook Group Post",
    "category": "social_media",
    "description": "Write engaging Facebook group posts that spark discussion.",
    "fields": [
        _text_field("topic", placeholder="Post topic"),
        _text_field("group_context", required=False, placeholder="Group name or niche"),
        _select_field("post_type", ["question", "tip", "story", "poll", "resource_share"], default="question"),
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
})

_register({
    "id": "social-media-bio",
    "name": "Social Media Bio",
    "category": "social_media",
    "description": "Write compelling social media bios for multiple platforms.",
    "fields": [
        _text_field("name_or_brand", placeholder="Person or brand name"),
        _text_field("role_or_niche", placeholder="e.g. SaaS Founder, Fitness Coach"),
        _KEY_BENEFIT,
        _text_field("unique_trait", required=False, placeholder="What makes you different"),
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
    "output_format": {"twitter": "str", "instagram": "str", "linkedin": "str", "tiktok": "str"},
    "char_limits": {"twitter": 160, "instagram": 150, "linkedin": 220, "tiktok": 80},
})

_register({
    "id": "hashtag-generator",
    "name": "Hashtag Generator",
    "category": "social_media",
    "description": "Generate relevant hashtag sets optimized for reach and engagement.",
    "fields": [
        _text_field("topic", placeholder="Content topic"),
        _text_field("niche", required=False, placeholder="Your niche or industry"),
        _select_field("platform", ["instagram", "tiktok", "twitter", "linkedin"], default="instagram"),
        _select_field("strategy", ["reach", "engagement", "niche", "mixed"], default="mixed"),
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
})


# ================================ BUSINESS (6) ==============================

_register({
    "id": "press-release",
    "name": "Press Release",
    "category": "business",
    "description": "Write professional press releases following AP style guidelines.",
    "fields": [
        _text_field("company_name", placeholder="Company name"),
        _text_field("headline_topic", placeholder="What the announcement is about"),
        _textarea_field("announcement_details", required=True, placeholder="Full details of the announcement"),
        _text_field("city_state", required=False, placeholder="e.g. San Francisco, CA"),
        _text_field("contact_name", required=False, placeholder="Media contact name"),
        _text_field("contact_email", required=False, placeholder="Media contact email"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a press release for {company_name} about: {headline_topic}.\n"
        "Details: {announcement_details}\n"
        "Location: {city_state}\n"
        "Contact: {contact_name} ({contact_email})\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Follow AP style\n"
        "- Headline: concise, newsworthy\n"
        "- Subheadline: additional context\n"
        "- Dateline: City, State, Date\n"
        "- Lead paragraph: who, what, when, where, why\n"
        "- Body: 3-5 paragraphs with quotes\n"
        "- Boilerplate section\n"
        "- Media contact info\n"
        "- 300-500 words\n\n"
        "Return as JSON with keys 'headline' (string), 'subheadline' (string), "
        "'body' (string), 'boilerplate' (string), and 'contact_info' (string)."
    ),
    "output_format": {
        "headline": "str",
        "subheadline": "str",
        "body": "str",
        "boilerplate": "str",
        "contact_info": "str",
    },
    "char_limits": {},
})

_register({
    "id": "case-study-outline",
    "name": "Case Study Outline",
    "category": "business",
    "description": "Generate structured case study outlines with key sections and talking points.",
    "fields": [
        _text_field("client_name", placeholder="Client or company name"),
        _text_field("industry", placeholder="Client industry"),
        _PRODUCT_NAME,
        _textarea_field("challenge", required=True, placeholder="Problem the client faced"),
        _textarea_field("solution", required=True, placeholder="How your product solved it"),
        _textarea_field("results", required=True, placeholder="Measurable outcomes"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a case study outline for {client_name} ({industry}) using "
        "'{product_name}'.\n"
        "Challenge: {challenge}\n"
        "Solution: {solution}\n"
        "Results: {results}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Title: compelling, results-driven\n"
        "- Executive summary: 2-3 sentences\n"
        "- Challenge section: context + pain points\n"
        "- Solution section: implementation details\n"
        "- Results section: metrics and outcomes\n"
        "- Quote placeholders for client testimonials\n"
        "- Key takeaways\n"
        "- CTA for prospects\n\n"
        "Return as JSON with keys 'title' (string), 'executive_summary' (string), "
        "'sections' (list of dicts with 'heading' and 'talking_points'), "
        "'quote_placeholders' (list of strings), and 'cta' (string)."
    ),
    "output_format": {
        "title": "str",
        "executive_summary": "str",
        "sections": "list[dict]",
        "quote_placeholders": "list[str]",
        "cta": "str",
    },
    "char_limits": {},
})

_register({
    "id": "company-boilerplate",
    "name": "Company Boilerplate",
    "category": "business",
    "description": "Create a concise company boilerplate for press releases and about pages.",
    "fields": [
        _text_field("company_name", placeholder="Company name"),
        _text_field("industry", placeholder="Industry or sector"),
        _text_field("founded_year", required=False, placeholder="Year founded"),
        _text_field("headquarters", required=False, placeholder="City, State/Country"),
        _KEY_BENEFIT,
        _text_field("key_stats", required=False, placeholder="e.g. 10K+ customers, Series B"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a company boilerplate for {company_name}.\n"
        "Industry: {industry}\n"
        "Founded: {founded_year}\n"
        "Headquarters: {headquarters}\n"
        "Value proposition: {key_benefit}\n"
        "Key stats: {key_stats}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Generate 3 lengths:\n"
        "  - Short: 1-2 sentences (50 words)\n"
        "  - Medium: 1 paragraph (100 words)\n"
        "  - Long: 2 paragraphs (150 words)\n"
        "- Factual, professional, no superlatives without backing\n"
        "- Include key differentiators\n\n"
        "Return as JSON with keys 'short' (string), 'medium' (string), "
        "and 'long' (string)."
    ),
    "output_format": {"short": "str", "medium": "str", "long": "str"},
    "char_limits": {},
})

_register({
    "id": "mission-statement",
    "name": "Mission Statement",
    "category": "business",
    "description": "Craft a clear, inspiring mission statement for your organization.",
    "fields": [
        _text_field("company_name", placeholder="Company name"),
        _text_field("industry", placeholder="Industry or sector"),
        _text_field("who_you_serve", placeholder="Who you serve"),
        _text_field("what_you_do", placeholder="What you do"),
        _text_field("why_it_matters", placeholder="Why it matters"),
        _text_field("core_values", required=False, placeholder="Comma-separated core values"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Craft a mission statement for {company_name} ({industry}).\n"
        "Who we serve: {who_you_serve}\n"
        "What we do: {what_you_do}\n"
        "Why it matters: {why_it_matters}\n"
        "Core values: {core_values}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Generate 5 variations\n"
        "- Each should be 1-2 sentences\n"
        "- Clear, memorable, actionable\n"
        "- Avoid jargon and cliches\n"
        "- Range from concise (10 words) to detailed (30 words)\n\n"
        "Return as JSON with key 'statements' (list of strings)."
    ),
    "output_format": {"statements": "list[str]"},
    "char_limits": {},
})

_register({
    "id": "job-description",
    "name": "Job Description",
    "category": "business",
    "description": "Write compelling job descriptions that attract qualified candidates.",
    "fields": [
        _text_field("job_title", placeholder="e.g. Senior Backend Engineer"),
        _text_field("company_name", placeholder="Company name"),
        _text_field("department", required=False, placeholder="e.g. Engineering, Marketing"),
        _text_field("location", required=False, placeholder="e.g. Remote, San Francisco, Hybrid"),
        _textarea_field("responsibilities", required=True, placeholder="Key responsibilities"),
        _textarea_field("requirements", required=True, placeholder="Must-have qualifications"),
        _textarea_field("nice_to_haves", required=False, placeholder="Nice-to-have qualifications"),
        _text_field("salary_range", required=False, placeholder="e.g. $120K-$160K"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a job description for {job_title} at {company_name}.\n"
        "Department: {department}\n"
        "Location: {location}\n"
        "Responsibilities: {responsibilities}\n"
        "Requirements: {requirements}\n"
        "Nice to haves: {nice_to_haves}\n"
        "Salary range: {salary_range}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Opening: 2-3 sentences about the role and impact\n"
        "- Responsibilities: 5-8 bullet points\n"
        "- Must-have qualifications: 4-6 bullet points\n"
        "- Nice-to-have: 3-4 bullet points\n"
        "- Benefits/perks section placeholder\n"
        "- Inclusive language throughout\n"
        "- Avoid gendered language\n\n"
        "Return as JSON with keys 'opening' (string), 'responsibilities' (list), "
        "'requirements' (list), 'nice_to_haves' (list), 'benefits_placeholder' (string), "
        "and 'closing' (string)."
    ),
    "output_format": {
        "opening": "str",
        "responsibilities": "list[str]",
        "requirements": "list[str]",
        "nice_to_haves": "list[str]",
        "benefits_placeholder": "str",
        "closing": "str",
    },
    "char_limits": {},
})

_register({
    "id": "investor-update",
    "name": "Investor Update",
    "category": "business",
    "description": "Write clear investor update emails with key metrics and highlights.",
    "fields": [
        _text_field("company_name", placeholder="Company name"),
        _text_field("period", placeholder="e.g. Q4 2025, January 2026"),
        _textarea_field("highlights", required=True, placeholder="Key wins and milestones"),
        _textarea_field("metrics", required=True, placeholder="Key metrics (MRR, users, growth)"),
        _textarea_field("challenges", required=False, placeholder="Challenges and how you are addressing them"),
        _textarea_field("asks", required=False, placeholder="Specific asks from investors"),
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write an investor update email for {company_name} ({period}).\n"
        "Highlights: {highlights}\n"
        "Key metrics: {metrics}\n"
        "Challenges: {challenges}\n"
        "Asks: {asks}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Subject line: clear, metric-driven\n"
        "- TL;DR: 2-3 bullet summary at top\n"
        "- Highlights section with context\n"
        "- Metrics presented clearly (ideally with period-over-period comparison)\n"
        "- Challenges: honest, with mitigation plans\n"
        "- Asks: specific and actionable\n"
        "- Next period outlook\n"
        "- 400-600 words\n\n"
        "Return as JSON with keys 'subject_line' (string), 'tldr' (list of strings), "
        "and 'body' (string)."
    ),
    "output_format": {"subject_line": "str", "tldr": "list[str]", "body": "str"},
    "char_limits": {},
})


# ================================= OTHER (6) ================================

_register({
    "id": "seo-meta-description",
    "name": "SEO Meta Description",
    "category": "other",
    "description": "Generate SEO-optimized meta descriptions for web pages.",
    "fields": [
        _text_field("page_title", placeholder="Page title"),
        _textarea_field("page_content_summary", required=True, placeholder="Brief summary of the page content"),
        _KEYWORDS,
        _CTA,
    ],
    "prompt_template": (
        "Write SEO meta descriptions for a page titled '{page_title}'.\n"
        "Content summary: {page_content_summary}\n"
        "Target keywords: {keywords}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Max 160 characters each\n"
        "- Include primary keyword in the first 100 characters\n"
        "- Action-oriented language\n"
        "- Generate 5 variations\n"
        "- Each should be unique in approach\n\n"
        "Return as JSON with key 'descriptions' (list of strings)."
    ),
    "output_format": {"descriptions": "list[str]"},
    "char_limits": {"description": 160},
})

_register({
    "id": "app-store-description",
    "name": "App Store Description",
    "category": "other",
    "description": "Write App Store and Google Play descriptions optimized for downloads.",
    "fields": [
        _text_field("app_name", placeholder="App name"),
        _text_field("app_category", placeholder="e.g. Productivity, Health, Finance"),
        _KEY_BENEFIT,
        _textarea_field("features", required=True, placeholder="Key features"),
        _TARGET_AUDIENCE,
        _select_field("platform", ["ios", "android", "both"], default="both"),
    ],
    "prompt_template": (
        "Write app store description for '{app_name}' ({app_category}).\n"
        "Key benefit: {key_benefit}\n"
        "Features: {features}\n"
        "Target audience: {target_audience}\n"
        "Platform: {platform}\n\n"
        "Requirements:\n"
        "- Subtitle/short description: max 30 characters\n"
        "- First paragraph: hook + primary value (visible without expanding)\n"
        "- Feature list: bullet points with benefit-first wording\n"
        "- Social proof placeholder\n"
        "- Promotional text: max 170 characters\n"
        "- Keywords suggestion: 100 characters for App Store keyword field\n"
        "- 200-300 words total\n\n"
        "Return as JSON with keys 'subtitle' (string), 'description' (string), "
        "'promotional_text' (string), and 'keywords' (string)."
    ),
    "output_format": {
        "subtitle": "str",
        "description": "str",
        "promotional_text": "str",
        "keywords": "str",
    },
    "char_limits": {"subtitle": 30, "promotional_text": 170, "keywords": 100},
})

_register({
    "id": "podcast-show-notes",
    "name": "Podcast Show Notes",
    "category": "other",
    "description": "Generate structured podcast show notes with timestamps and resources.",
    "fields": [
        _text_field("episode_title", placeholder="Episode title"),
        _text_field("podcast_name", required=False, placeholder="Podcast name"),
        _textarea_field("episode_summary", required=True, placeholder="Brief summary of what was discussed"),
        _text_field("guest_name", required=False, placeholder="Guest name and title"),
        _KEYWORDS,
    ],
    "prompt_template": (
        "Write podcast show notes for '{episode_title}' on {podcast_name}.\n"
        "Summary: {episode_summary}\n"
        "Guest: {guest_name}\n"
        "Keywords: {keywords}\n\n"
        "Requirements:\n"
        "- Episode description: 2-3 sentences for podcast directories\n"
        "- Key takeaways: 3-5 bullet points\n"
        "- Suggested timestamps: 5-8 entries\n"
        "- Resources mentioned section\n"
        "- Guest bio placeholder\n"
        "- SEO-friendly\n\n"
        "Return as JSON with keys 'description' (string), 'takeaways' (list), "
        "'timestamps' (list of dicts with 'time' and 'topic'), "
        "'resources' (list of strings), and 'guest_bio_placeholder' (string)."
    ),
    "output_format": {
        "description": "str",
        "takeaways": "list[str]",
        "timestamps": "list[dict]",
        "resources": "list[str]",
        "guest_bio_placeholder": "str",
    },
    "char_limits": {},
})

_register({
    "id": "webinar-description",
    "name": "Webinar Description",
    "category": "other",
    "description": "Write webinar landing page descriptions that drive registrations.",
    "fields": [
        _text_field("webinar_title", placeholder="Webinar title"),
        _textarea_field("webinar_topics", required=True, placeholder="Topics to be covered"),
        _text_field("presenter", required=False, placeholder="Presenter name and title"),
        _text_field("date_time", required=False, placeholder="Date and time"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write a webinar description for '{webinar_title}'.\n"
        "Topics: {webinar_topics}\n"
        "Presenter: {presenter}\n"
        "Date/time: {date_time}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Headline: benefit-driven, not just the title\n"
        "- Subheadline: who it is for\n"
        "- What you will learn: 3-5 bullet points\n"
        "- Speaker bio placeholder\n"
        "- Registration CTA copy\n"
        "- 150-250 words\n\n"
        "Return as JSON with keys 'headline' (string), 'subheadline' (string), "
        "'description' (string), 'learning_outcomes' (list), "
        "'speaker_placeholder' (string), and 'cta_text' (string)."
    ),
    "output_format": {
        "headline": "str",
        "subheadline": "str",
        "description": "str",
        "learning_outcomes": "list[str]",
        "speaker_placeholder": "str",
        "cta_text": "str",
    },
    "char_limits": {},
})

_register({
    "id": "course-description",
    "name": "Course Description",
    "category": "other",
    "description": "Write course descriptions for online learning platforms.",
    "fields": [
        _text_field("course_title", placeholder="Course title"),
        _textarea_field("course_topics", required=True, placeholder="Topics and modules covered"),
        _text_field("instructor", required=False, placeholder="Instructor name and credentials"),
        _select_field("level", ["beginner", "intermediate", "advanced", "all_levels"], default="all_levels"),
        _text_field("duration", required=False, placeholder="e.g. 8 hours, 6 weeks"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
    ],
    "prompt_template": (
        "Write a course description for '{course_title}'.\n"
        "Topics: {course_topics}\n"
        "Instructor: {instructor}\n"
        "Level: {level}\n"
        "Duration: {duration}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n\n"
        "Requirements:\n"
        "- Headline: transformation-focused\n"
        "- Overview: 2-3 sentences on what students will achieve\n"
        "- What you will learn: 5-7 outcomes\n"
        "- Who this course is for: 3-4 personas\n"
        "- Prerequisites if applicable\n"
        "- 200-300 words\n\n"
        "Return as JSON with keys 'headline' (string), 'overview' (string), "
        "'outcomes' (list), 'target_personas' (list), "
        "'prerequisites' (list), and 'instructor_placeholder' (string)."
    ),
    "output_format": {
        "headline": "str",
        "overview": "str",
        "outcomes": "list[str]",
        "target_personas": "list[str]",
        "prerequisites": "list[str]",
        "instructor_placeholder": "str",
    },
    "char_limits": {},
})

_register({
    "id": "event-description",
    "name": "Event Description",
    "category": "other",
    "description": "Write event descriptions for conferences, meetups, and workshops.",
    "fields": [
        _text_field("event_name", placeholder="Event name"),
        _select_field("event_type", ["conference", "meetup", "workshop", "hackathon", "networking"], default="conference"),
        _textarea_field("event_details", required=True, placeholder="What the event is about"),
        _text_field("date_location", required=False, placeholder="Date and location"),
        _text_field("speakers_or_hosts", required=False, placeholder="Featured speakers or hosts"),
        _TARGET_AUDIENCE,
        _TONE_FIELD,
        _CTA,
    ],
    "prompt_template": (
        "Write an event description for '{event_name}' ({event_type}).\n"
        "Details: {event_details}\n"
        "Date/Location: {date_location}\n"
        "Speakers/Hosts: {speakers_or_hosts}\n"
        "Target audience: {target_audience}\n"
        "Tone: {tone}\n"
        "CTA: {call_to_action}\n\n"
        "Requirements:\n"
        "- Headline: exciting, benefit-driven\n"
        "- Short description: 2-3 sentences for listing pages\n"
        "- Full description: 200-300 words\n"
        "- What to expect: 4-6 bullet points\n"
        "- Logistics summary (date, time, location)\n"
        "- Registration CTA\n\n"
        "Return as JSON with keys 'headline' (string), "
        "'short_description' (string), 'full_description' (string), "
        "'what_to_expect' (list), 'logistics' (string), and 'cta_text' (string)."
    ),
    "output_format": {
        "headline": "str",
        "short_description": "str",
        "full_description": "str",
        "what_to_expect": "list[str]",
        "logistics": "str",
        "cta_text": "str",
    },
    "char_limits": {},
})
