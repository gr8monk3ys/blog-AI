"""Marketing templates: other category."""

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
        "id": "seo-meta-description",
        "name": "SEO Meta Description",
        "category": "other",
        "description": "Generate SEO-optimized meta descriptions for web pages.",
        "fields": [
            _text_field("page_title", placeholder="Page title"),
            _textarea_field(
                "page_content_summary",
                required=True,
                placeholder="Brief summary of the page content",
            ),
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
    },
    {
        "id": "app-store-description",
        "name": "App Store Description",
        "category": "other",
        "description": "Write App Store and Google Play descriptions optimized for downloads.",
        "fields": [
            _text_field("app_name", placeholder="App name"),
            _text_field(
                "app_category", placeholder="e.g. Productivity, Health, Finance"
            ),
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
    },
    {
        "id": "podcast-show-notes",
        "name": "Podcast Show Notes",
        "category": "other",
        "description": "Generate structured podcast show notes with timestamps and resources.",
        "fields": [
            _text_field("episode_title", placeholder="Episode title"),
            _text_field("podcast_name", required=False, placeholder="Podcast name"),
            _textarea_field(
                "episode_summary",
                required=True,
                placeholder="Brief summary of what was discussed",
            ),
            _text_field(
                "guest_name", required=False, placeholder="Guest name and title"
            ),
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
    },
    {
        "id": "webinar-description",
        "name": "Webinar Description",
        "category": "other",
        "description": "Write webinar landing page descriptions that drive registrations.",
        "fields": [
            _text_field("webinar_title", placeholder="Webinar title"),
            _textarea_field(
                "webinar_topics", required=True, placeholder="Topics to be covered"
            ),
            _text_field(
                "presenter", required=False, placeholder="Presenter name and title"
            ),
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
    },
    {
        "id": "course-description",
        "name": "Course Description",
        "category": "other",
        "description": "Write course descriptions for online learning platforms.",
        "fields": [
            _text_field("course_title", placeholder="Course title"),
            _textarea_field(
                "course_topics", required=True, placeholder="Topics and modules covered"
            ),
            _text_field(
                "instructor",
                required=False,
                placeholder="Instructor name and credentials",
            ),
            _select_field(
                "level",
                ["beginner", "intermediate", "advanced", "all_levels"],
                default="all_levels",
            ),
            _text_field(
                "duration", required=False, placeholder="e.g. 8 hours, 6 weeks"
            ),
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
    },
    {
        "id": "event-description",
        "name": "Event Description",
        "category": "other",
        "description": "Write event descriptions for conferences, meetups, and workshops.",
        "fields": [
            _text_field("event_name", placeholder="Event name"),
            _select_field(
                "event_type",
                ["conference", "meetup", "workshop", "hackathon", "networking"],
                default="conference",
            ),
            _textarea_field(
                "event_details", required=True, placeholder="What the event is about"
            ),
            _text_field(
                "date_location", required=False, placeholder="Date and location"
            ),
            _text_field(
                "speakers_or_hosts",
                required=False,
                placeholder="Featured speakers or hosts",
            ),
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
    },
]
