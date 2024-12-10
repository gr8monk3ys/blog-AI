"""Marketing templates: product category."""

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
        "id": "product-description-short",
        "name": "Product Description (Short)",
        "category": "product",
        "description": "Generate concise product descriptions optimized for quick scanning and conversion.",
        "fields": [
            _PRODUCT_NAME,
            _text_field(
                "product_type", placeholder="e.g. wireless earbuds, organic shampoo"
            ),
            _KEY_BENEFIT,
            _text_field(
                "key_features", required=False, placeholder="Comma-separated features"
            ),
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
    },
    {
        "id": "product-description-long",
        "name": "Product Description (Long/Story)",
        "category": "product",
        "description": "Create detailed, story-driven product descriptions that build emotional connection.",
        "fields": [
            _PRODUCT_NAME,
            _text_field("product_type", placeholder="e.g. handcrafted leather bag"),
            _KEY_BENEFIT,
            _textarea_field(
                "features_details",
                required=True,
                placeholder="Detailed features and specs",
            ),
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
    },
    {
        "id": "product-feature-bullets",
        "name": "Product Feature Bullets",
        "category": "product",
        "description": "Generate benefit-driven feature bullet points for product pages.",
        "fields": [
            _PRODUCT_NAME,
            _textarea_field(
                "features_list",
                required=True,
                placeholder="List your product features, one per line",
            ),
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
    },
    {
        "id": "product-comparison",
        "name": "Product Comparison",
        "category": "product",
        "description": "Generate product comparison copy positioning your product against competitors.",
        "fields": [
            _PRODUCT_NAME,
            _text_field("competitor_name", placeholder="Main competitor"),
            _textarea_field(
                "your_advantages",
                required=True,
                placeholder="Key advantages over competitor",
            ),
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
    },
    {
        "id": "product-review-response",
        "name": "Product Review Response",
        "category": "product",
        "description": "Draft professional responses to product reviews (positive and negative).",
        "fields": [
            _PRODUCT_NAME,
            _textarea_field(
                "review_text", required=True, placeholder="Paste the customer review"
            ),
            _select_field(
                "review_sentiment",
                ["positive", "negative", "mixed"],
                default="positive",
            ),
            _text_field("company_name", placeholder="Your company name"),
            _TONE_FIELD,
        ],
        "prompt_template": (
            "Write a professional response to this {review_sentiment} review of "
            "'{product_name}' on behalf of {company_name}.\n\n"
            'Customer review:\n"{review_text}"\n\n'
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
    },
    {
        "id": "amazon-product-listing",
        "name": "Amazon Product Listing",
        "category": "product",
        "description": "Create optimized Amazon product listing with title, bullets, and description.",
        "fields": [
            _PRODUCT_NAME,
            _text_field("product_type", placeholder="Product category"),
            _textarea_field(
                "features_details", required=True, placeholder="All features and specs"
            ),
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
    },
    {
        "id": "shopify-product-page",
        "name": "Shopify Product Page",
        "category": "product",
        "description": "Write complete Shopify product page copy including title, description, and SEO.",
        "fields": [
            _PRODUCT_NAME,
            _text_field("product_type", placeholder="Product type/category"),
            _text_field("price", required=False, placeholder="e.g. $49.99"),
            _textarea_field(
                "features_details",
                required=True,
                placeholder="Features and specifications",
            ),
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
    },
    {
        "id": "product-launch-announcement",
        "name": "Product Launch Announcement",
        "category": "product",
        "description": "Generate product launch announcement copy for multiple channels.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _textarea_field(
                "launch_details",
                required=True,
                placeholder="Launch date, availability, pricing",
            ),
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
    },
]
