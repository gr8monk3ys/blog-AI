"""
Marketing copy template library.

Contains 52 production-ready templates organized across 7 categories.
Each template defines its input fields, prompt template, expected output
format, and character limits where applicable.

The template definitions live in per-category modules under
``src/templates/marketing/`` and the shared field helpers in
``src/templates/_fields.py``. This module assembles them into the public
``MARKETING_TEMPLATES`` registry and re-exports ``TEMPLATE_CATEGORIES`` so the
existing import paths keep working.
"""

from typing import Any, Dict

from src.templates._categories import TEMPLATE_CATEGORIES
from src.templates.marketing.advertising import TEMPLATES as _ADVERTISING
from src.templates.marketing.business import TEMPLATES as _BUSINESS
from src.templates.marketing.email import TEMPLATES as _EMAIL
from src.templates.marketing.landing_page import TEMPLATES as _LANDING_PAGE
from src.templates.marketing.other import TEMPLATES as _OTHER
from src.templates.marketing.product import TEMPLATES as _PRODUCT
from src.templates.marketing.social_media import TEMPLATES as _SOCIAL_MEDIA

__all__ = ["MARKETING_TEMPLATES", "TEMPLATE_CATEGORIES"]

# Assembled in the original registration order so template ids resolve
# identically to the previous single-file implementation.
_ALL_TEMPLATES = (
    _ADVERTISING
    + _PRODUCT
    + _EMAIL
    + _LANDING_PAGE
    + _SOCIAL_MEDIA
    + _BUSINESS
    + _OTHER
)

MARKETING_TEMPLATES: Dict[str, Dict[str, Any]] = {
    template["id"]: template for template in _ALL_TEMPLATES
}
