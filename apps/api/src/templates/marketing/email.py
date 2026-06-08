"""Marketing templates: email category."""

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
        "id": "welcome-email",
        "name": "Welcome Email",
        "category": "email",
        "description": "Write an engaging welcome email for new subscribers or customers.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _PRODUCT_NAME,
            _KEY_BENEFIT,
            _text_field(
                "offer", required=False, placeholder="e.g. 10% off first order"
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "newsletter-email",
        "name": "Newsletter",
        "category": "email",
        "description": "Create newsletter email copy with engaging sections and curated content.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _text_field("newsletter_topic", placeholder="Main topic or theme"),
            _textarea_field(
                "key_points",
                required=True,
                placeholder="Key points or stories to cover",
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "promotional-email",
        "name": "Promotional Email",
        "category": "email",
        "description": "Write compelling promotional emails for sales, launches, and special offers.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _PRODUCT_NAME,
            _text_field(
                "promotion_details", placeholder="e.g. 30% off, buy one get one free"
            ),
            _text_field(
                "deadline",
                required=False,
                placeholder="e.g. Ends Friday, Limited to 100",
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "cart-abandonment-email",
        "name": "Cart Abandonment Email",
        "category": "email",
        "description": "Recover lost sales with persuasive cart abandonment email sequences.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _PRODUCT_NAME,
            _text_field(
                "incentive",
                required=False,
                placeholder="e.g. 10% discount, free shipping",
            ),
            _select_field(
                "sequence_position",
                ["first_reminder", "second_reminder", "final_reminder"],
                default="first_reminder",
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "re-engagement-email",
        "name": "Re-engagement Email",
        "category": "email",
        "description": "Win back inactive subscribers with compelling re-engagement campaigns.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _KEY_BENEFIT,
            _text_field(
                "incentive", required=False, placeholder="Special offer to re-engage"
            ),
            _text_field(
                "inactivity_period",
                required=False,
                placeholder="e.g. 3 months, 6 months",
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "product-update-email",
        "name": "Product Update Email",
        "category": "email",
        "description": "Announce new features and product updates to keep users engaged.",
        "fields": [
            _text_field("company_name", placeholder="Your company name"),
            _PRODUCT_NAME,
            _textarea_field(
                "update_details",
                required=True,
                placeholder="New features, improvements, changes",
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
        "id": "event-invitation-email",
        "name": "Event Invitation Email",
        "category": "email",
        "description": "Create event invitation emails that drive RSVPs and attendance.",
        "fields": [
            _text_field("event_name", placeholder="Name of the event"),
            _text_field("event_date", placeholder="Date and time"),
            _text_field(
                "event_location", required=False, placeholder="Venue or 'Virtual'"
            ),
            _textarea_field(
                "event_description",
                required=True,
                placeholder="What the event is about",
            ),
            _text_field(
                "speakers", required=False, placeholder="Featured speakers or guests"
            ),
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
        "output_format": {
            "subject_lines": "list[str]",
            "preview_text": "str",
            "body": "str",
        },
        "char_limits": {"subject_line": 50, "preview_text": 90},
    },
    {
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
            _text_field(
                "recipient_company", required=False, placeholder="Their company name"
            ),
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
    },
]
