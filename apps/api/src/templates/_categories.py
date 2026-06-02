"""Category metadata for the marketing template library."""

from typing import Any, Dict

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
