"""Marketing templates: landing_page category."""

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
    },
    {
        "id": "landing-features-section",
        "name": "Features Section",
        "category": "landing_page",
        "description": "Create a features section with benefit-driven headlines and descriptions.",
        "fields": [
            _PRODUCT_NAME,
            _textarea_field(
                "features_list",
                required=True,
                placeholder="List features, one per line",
            ),
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
    },
    {
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
        "output_format": {
            "subject_lines": "list[str]",
            "email_body": "str",
            "guiding_questions": "list[str]",
        },
        "char_limits": {"subject_line": 50},
    },
    {
        "id": "landing-cta-section",
        "name": "CTA Section",
        "category": "landing_page",
        "description": "Create compelling call-to-action sections for landing pages.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _select_field(
                "cta_type",
                ["signup", "purchase", "demo", "download", "contact"],
                default="signup",
            ),
            _text_field(
                "offer",
                required=False,
                placeholder="e.g. Start free trial, 30-day guarantee",
            ),
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
    },
    {
        "id": "landing-faq-section",
        "name": "FAQ Section",
        "category": "landing_page",
        "description": "Generate FAQ copy for landing pages addressing common objections.",
        "fields": [
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _textarea_field(
                "common_questions",
                required=False,
                placeholder="Common questions from customers",
            ),
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
    },
    {
        "id": "landing-pricing-copy",
        "name": "Pricing Page Copy",
        "category": "landing_page",
        "description": "Write persuasive pricing page copy with plan descriptions and feature lists.",
        "fields": [
            _PRODUCT_NAME,
            _textarea_field(
                "plans",
                required=True,
                placeholder="List plans with prices and features",
            ),
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
    },
]
