"""
Claim extraction — uses LLM to identify factual claims in content.
"""

import json
import logging
from typing import Optional

from src.text_generation.core import GenerationOptions, create_provider_from_env, generate_text
from src.types.fact_check import Claim, ClaimType

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
You are a fact-checker. Extract all factual claims from the following content.

For each claim, provide:
- "text": The exact factual claim (one sentence)
- "source_section": The section title it appears in (or "" if unknown)
- "claim_type": One of: statistic, quote, historical, scientific, general

Return a JSON array of claims. Only include verifiable factual statements.
Do NOT include opinions, predictions, or subjective statements.

--- CONTENT ---
{content}

--- OUTPUT (JSON array only) ---"""


def extract_claims(
    content: str,
    provider_type: str = "openai",
    options: Optional[GenerationOptions] = None,
) -> list[Claim]:
    """
    Extract factual claims from content using an LLM.

    Args:
        content: The text content to analyze.
        provider_type: LLM provider to use.
        options: Generation options.

    Returns:
        List of extracted claims.
    """
    prompt = _EXTRACTION_PROMPT.format(content=content[:8000])
    provider = create_provider_from_env(provider_type)
    response = generate_text(prompt, provider, options)

    try:
        # Parse JSON from LLM response
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        claims_data = json.loads(text)

        claims = []
        for item in claims_data:
            claim_type = item.get("claim_type", "general")
            try:
                ct = ClaimType(claim_type)
            except ValueError:
                ct = ClaimType.GENERAL

            claims.append(
                Claim(
                    text=str(item.get("text", "")),
                    source_section=str(item.get("source_section", "")),
                    claim_type=ct,
                )
            )
        return claims
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Failed to parse claims from LLM response: %s", e)
        return []
