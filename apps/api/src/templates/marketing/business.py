"""Marketing templates: business category."""

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
        "id": "press-release",
        "name": "Press Release",
        "category": "business",
        "description": "Write professional press releases following AP style guidelines.",
        "fields": [
            _text_field("company_name", placeholder="Company name"),
            _text_field("headline_topic", placeholder="What the announcement is about"),
            _textarea_field(
                "announcement_details",
                required=True,
                placeholder="Full details of the announcement",
            ),
            _text_field(
                "city_state", required=False, placeholder="e.g. San Francisco, CA"
            ),
            _text_field(
                "contact_name", required=False, placeholder="Media contact name"
            ),
            _text_field(
                "contact_email", required=False, placeholder="Media contact email"
            ),
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
    },
    {
        "id": "case-study-outline",
        "name": "Case Study Outline",
        "category": "business",
        "description": "Generate structured case study outlines with key sections and talking points.",
        "fields": [
            _text_field("client_name", placeholder="Client or company name"),
            _text_field("industry", placeholder="Client industry"),
            _PRODUCT_NAME,
            _textarea_field(
                "challenge", required=True, placeholder="Problem the client faced"
            ),
            _textarea_field(
                "solution", required=True, placeholder="How your product solved it"
            ),
            _textarea_field(
                "results", required=True, placeholder="Measurable outcomes"
            ),
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
    },
    {
        "id": "company-boilerplate",
        "name": "Company Boilerplate",
        "category": "business",
        "description": "Create a concise company boilerplate for press releases and about pages.",
        "fields": [
            _text_field("company_name", placeholder="Company name"),
            _text_field("industry", placeholder="Industry or sector"),
            _text_field("founded_year", required=False, placeholder="Year founded"),
            _text_field(
                "headquarters", required=False, placeholder="City, State/Country"
            ),
            _KEY_BENEFIT,
            _text_field(
                "key_stats", required=False, placeholder="e.g. 10K+ customers, Series B"
            ),
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
    },
    {
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
            _text_field(
                "core_values", required=False, placeholder="Comma-separated core values"
            ),
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
    },
    {
        "id": "job-description",
        "name": "Job Description",
        "category": "business",
        "description": "Write compelling job descriptions that attract qualified candidates.",
        "fields": [
            _text_field("job_title", placeholder="e.g. Senior Backend Engineer"),
            _text_field("company_name", placeholder="Company name"),
            _text_field(
                "department", required=False, placeholder="e.g. Engineering, Marketing"
            ),
            _text_field(
                "location",
                required=False,
                placeholder="e.g. Remote, San Francisco, Hybrid",
            ),
            _textarea_field(
                "responsibilities", required=True, placeholder="Key responsibilities"
            ),
            _textarea_field(
                "requirements", required=True, placeholder="Must-have qualifications"
            ),
            _textarea_field(
                "nice_to_haves",
                required=False,
                placeholder="Nice-to-have qualifications",
            ),
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
    },
    {
        "id": "investor-update",
        "name": "Investor Update",
        "category": "business",
        "description": "Write clear investor update emails with key metrics and highlights.",
        "fields": [
            _text_field("company_name", placeholder="Company name"),
            _text_field("period", placeholder="e.g. Q4 2025, January 2026"),
            _textarea_field(
                "highlights", required=True, placeholder="Key wins and milestones"
            ),
            _textarea_field(
                "metrics", required=True, placeholder="Key metrics (MRR, users, growth)"
            ),
            _textarea_field(
                "challenges",
                required=False,
                placeholder="Challenges and how you are addressing them",
            ),
            _textarea_field(
                "asks", required=False, placeholder="Specific asks from investors"
            ),
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
    },
]
