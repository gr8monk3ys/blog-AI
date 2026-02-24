"""
Claim validation — checks individual claims against source material using LLM.
"""

import json
import logging
from typing import Optional

from src.text_generation.core import GenerationOptions, create_provider_from_env, generate_text
from src.types.fact_check import Claim, ClaimVerification, VerificationStatus

logger = logging.getLogger(__name__)

_VALIDATION_PROMPT = """\
You are a fact-checker. Determine whether the following claim is supported by the provided sources.

CLAIM: {claim}

SOURCES:
{sources}

Respond with ONLY a JSON object:
{{
  "status": "verified" | "unverified" | "contradicted",
  "confidence": 0.0 to 1.0,
  "supporting_sources": ["source title or URL that supports/contradicts"],
  "explanation": "Brief explanation (1-2 sentences)"
}}

Rules:
- "verified": The claim is directly supported by at least one source.
- "contradicted": A source directly contradicts the claim.
- "unverified": No source confirms or denies the claim.
- Confidence should reflect how strongly the sources support the verdict."""


def validate_claim(
    claim: Claim,
    source_snippets: list[dict[str, str]],
    provider_type: str = "openai",
    options: Optional[GenerationOptions] = None,
) -> ClaimVerification:
    """
    Validate a single claim against source snippets.

    Args:
        claim: The claim to validate.
        source_snippets: List of dicts with 'title', 'url', 'snippet' keys.
        provider_type: LLM provider.
        options: Generation options.

    Returns:
        ClaimVerification result.
    """
    sources_text = "\n".join(
        f"[{i+1}] {s.get('title', 'Unknown')}: {s.get('snippet', '')[:300]}"
        for i, s in enumerate(source_snippets[:10])
    )

    if not sources_text.strip():
        return ClaimVerification(
            claim=claim,
            confidence=0.0,
            status=VerificationStatus.UNVERIFIED,
            explanation="No sources available for verification.",
        )

    prompt = _VALIDATION_PROMPT.format(claim=claim.text, sources=sources_text)
    provider = create_provider_from_env(provider_type)
    response = generate_text(prompt, provider, options)

    try:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)

        status_str = data.get("status", "unverified")
        try:
            ver_status = VerificationStatus(status_str)
        except ValueError:
            ver_status = VerificationStatus.UNVERIFIED

        return ClaimVerification(
            claim=claim,
            confidence=min(1.0, max(0.0, float(data.get("confidence", 0.5)))),
            status=ver_status,
            supporting_sources=data.get("supporting_sources", []),
            explanation=str(data.get("explanation", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Failed to parse validation result: %s", e)
        return ClaimVerification(
            claim=claim,
            confidence=0.0,
            status=VerificationStatus.UNVERIFIED,
            explanation="Failed to parse verification result.",
        )


def validate_claims(
    claims: list[Claim],
    source_snippets: list[dict[str, str]],
    provider_type: str = "openai",
    options: Optional[GenerationOptions] = None,
) -> list[ClaimVerification]:
    """Validate a batch of claims against source material."""
    return [
        validate_claim(claim, source_snippets, provider_type, options)
        for claim in claims
    ]
