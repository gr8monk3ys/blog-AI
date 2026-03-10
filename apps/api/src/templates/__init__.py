"""Marketing copy template library for AI-driven content generation."""

from .marketing_templates import MARKETING_TEMPLATES, TEMPLATE_CATEGORIES
from .template_engine import (
    generate_from_template,
    get_all_templates,
    get_categories,
    get_template,
    get_templates_by_category,
)

__all__ = [
    "MARKETING_TEMPLATES",
    "TEMPLATE_CATEGORIES",
    "generate_from_template",
    "get_all_templates",
    "get_categories",
    "get_template",
    "get_templates_by_category",
]
