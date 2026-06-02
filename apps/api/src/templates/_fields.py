"""Shared field-definition helpers and constants for marketing templates."""

from typing import Any, Dict, List  # noqa: F401


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


_TONE_OPTIONS = [
    "professional",
    "casual",
    "urgent",
    "friendly",
    "authoritative",
    "playful",
]
_TONE_FIELD = _select_field(
    "tone", _TONE_OPTIONS, default="professional", description="Voice tone"
)

_PRODUCT_NAME = _text_field("product_name", placeholder="Your product or service name")
_KEY_BENEFIT = _text_field(
    "key_benefit", placeholder="Main benefit or value proposition"
)
_TARGET_AUDIENCE = _text_field(
    "target_audience",
    required=False,
    placeholder="e.g. SaaS founders, busy parents, fitness enthusiasts",
)
_CTA = _text_field(
    "call_to_action", required=False, placeholder="e.g. Sign Up Free, Shop Now"
)
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
