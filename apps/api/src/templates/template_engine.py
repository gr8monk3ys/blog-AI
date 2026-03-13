"""
Template engine for the marketing copy template library.

Provides functions to query templates, validate inputs, fill prompt
templates with user-supplied fields, and generate content through the
LLM abstraction layer.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from ..text_generation.core import (
    TextGenerationError,
    create_provider_from_env,
    generate_text,
)
from ..types.providers import GenerationOptions, ProviderType
from .marketing_templates import MARKETING_TEMPLATES, TEMPLATE_CATEGORIES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public query helpers
# ---------------------------------------------------------------------------


def get_all_templates() -> List[Dict[str, Any]]:
    """Return all marketing templates with metadata (without full prompt text).

    Each entry includes id, name, category, description, fields, output_format,
    and char_limits.
    """
    results: List[Dict[str, Any]] = []
    for template in MARKETING_TEMPLATES.values():
        results.append(_template_summary(template))
    return results


def get_templates_by_category(category: str) -> List[Dict[str, Any]]:
    """Return templates filtered by category slug.

    Args:
        category: A category slug such as 'advertising' or 'email'.

    Returns:
        A list of template summaries in the given category.

    Raises:
        ValueError: If the category does not exist.
    """
    if category not in TEMPLATE_CATEGORIES:
        valid = ", ".join(sorted(TEMPLATE_CATEGORIES.keys()))
        raise ValueError(f"Unknown category '{category}'. Valid categories: {valid}")

    return [
        _template_summary(t)
        for t in MARKETING_TEMPLATES.values()
        if t["category"] == category
    ]


def get_template(template_id: str) -> Dict[str, Any]:
    """Return a single template by id, including the prompt template.

    Args:
        template_id: The unique template identifier (e.g. 'google-search-ad').

    Returns:
        Full template definition.

    Raises:
        KeyError: If no template with the given id exists.
    """
    template = MARKETING_TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(f"Template not found: {template_id}")
    return dict(template)


def get_categories() -> List[Dict[str, Any]]:
    """Return a list of categories with metadata and template counts."""
    counts: Dict[str, int] = {}
    for template in MARKETING_TEMPLATES.values():
        cat = template["category"]
        counts[cat] = counts.get(cat, 0) + 1

    results: List[Dict[str, Any]] = []
    for slug, meta in TEMPLATE_CATEGORIES.items():
        results.append({
            "id": slug,
            "name": meta["name"],
            "description": meta["description"],
            "icon": meta.get("icon", ""),
            "template_count": counts.get(slug, 0),
        })
    return results


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_from_template(
    template_id: str,
    fields: Dict[str, Any],
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> Dict[str, Any]:
    """Fill a prompt template with user fields, call the LLM, and return output.

    Args:
        template_id: The template to use.
        fields: User-supplied field values keyed by field name.
        provider_type: Which LLM provider to use.
        options: Optional generation parameters.

    Returns:
        A dict containing:
            - success (bool)
            - template_id (str)
            - output (dict | str): The generated content, parsed as JSON when
              possible.
            - raw_text (str): The raw LLM response.
            - execution_time_ms (int)
            - error (str | None)
    """
    template = MARKETING_TEMPLATES.get(template_id)
    if template is None:
        return {
            "success": False,
            "template_id": template_id,
            "output": None,
            "raw_text": "",
            "execution_time_ms": 0,
            "error": f"Template not found: {template_id}",
        }

    # ------------------------------------------------------------------
    # Validate required fields
    # ------------------------------------------------------------------
    validation_errors = _validate_fields(template, fields)
    if validation_errors:
        return {
            "success": False,
            "template_id": template_id,
            "output": None,
            "raw_text": "",
            "execution_time_ms": 0,
            "error": f"Validation errors: {'; '.join(validation_errors)}",
        }

    # ------------------------------------------------------------------
    # Build prompt from template
    # ------------------------------------------------------------------
    prompt = _fill_prompt(template["prompt_template"], fields, template["fields"])

    # ------------------------------------------------------------------
    # Call LLM
    # ------------------------------------------------------------------
    start = time.monotonic()
    try:
        provider = create_provider_from_env(provider_type)
        raw_text = generate_text(prompt, provider, options)
    except TextGenerationError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.error("Template generation failed for %s: %s", template_id, exc)
        return {
            "success": False,
            "template_id": template_id,
            "output": None,
            "raw_text": "",
            "execution_time_ms": elapsed_ms,
            "error": str(exc),
        }
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # ------------------------------------------------------------------
    # Parse output
    # ------------------------------------------------------------------
    parsed = _parse_llm_output(raw_text)

    return {
        "success": True,
        "template_id": template_id,
        "output": parsed,
        "raw_text": raw_text,
        "execution_time_ms": elapsed_ms,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _template_summary(template: Dict[str, Any]) -> Dict[str, Any]:
    """Return a template dict without the raw prompt_template string."""
    return {
        "id": template["id"],
        "name": template["name"],
        "category": template["category"],
        "description": template["description"],
        "fields": template["fields"],
        "output_format": template.get("output_format", {}),
        "char_limits": template.get("char_limits", {}),
    }


def _validate_fields(
    template: Dict[str, Any],
    fields: Dict[str, Any],
) -> List[str]:
    """Validate user fields against the template field definitions.

    Returns a list of human-readable error strings (empty if valid).
    """
    errors: List[str] = []
    for field_def in template.get("fields", []):
        name = field_def["name"]
        required = field_def.get("required", False)
        value = fields.get(name)

        if required and (value is None or str(value).strip() == ""):
            errors.append(f"'{name}' is required")
            continue

        # Validate select field values
        if (
            field_def.get("type") == "select"
            and value is not None
            and str(value).strip() != ""
        ):
            allowed = field_def.get("options", [])
            if allowed and str(value) not in allowed:
                errors.append(
                    f"'{name}' must be one of: {', '.join(allowed)}"
                )

    return errors


def _fill_prompt(
    prompt_template: str,
    fields: Dict[str, Any],
    field_defs: List[Dict[str, Any]],
) -> str:
    """Fill placeholders in a prompt template with user-supplied values.

    Missing optional fields are replaced with sensible defaults so the
    prompt reads naturally.
    """
    # Build a mapping of field name -> value (or a default).
    values: Dict[str, str] = {}
    defaults_by_name: Dict[str, str] = {}
    for fd in field_defs:
        name = fd["name"]
        default = fd.get("default", "")
        if not default and fd.get("type") == "select":
            default = fd.get("options", [""])[0] if fd.get("options") else ""
        defaults_by_name[name] = str(default)

    for fd in field_defs:
        name = fd["name"]
        raw = fields.get(name)
        if raw is None or str(raw).strip() == "":
            values[name] = defaults_by_name.get(name, "not specified")
        else:
            values[name] = str(raw).strip()

    # Use a safe format that ignores extra placeholders.
    try:
        return prompt_template.format_map(_SafeDict(values))
    except Exception:
        # Fallback: simple regex replacement
        result = prompt_template
        for key, val in values.items():
            result = result.replace("{" + key + "}", val)
        return result


class _SafeDict(dict):
    """Dict subclass that returns the key wrapped in braces for missing keys."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _parse_llm_output(raw_text: str) -> Any:
    """Attempt to parse the LLM output as JSON.

    Falls back to returning the raw string if parsing fails.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present.
    if text.startswith("```"):
        # Remove opening fence (with optional language tag)
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        # Remove closing fence
        text = re.sub(r"\n?```\s*$", "", text)

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find a JSON object/array embedded in the text.
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, ValueError):
                continue

    # Return raw text as-is.
    return raw_text
