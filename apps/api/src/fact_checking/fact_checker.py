"""
Fact-checker facade — orchestrates claim extraction, validation, and confidence scoring.
"""

import logging
from typing import Optional

from src.text_generation.core import GenerationOptions
from src.types.fact_check import FactCheckResult, VerificationStatus

from .claim_extractor import extract_claims
from .claim_validator import validate_claims

logger = logging.getLogger(__name__)


def check_facts(
    content: str,
    sources: Optional[list[dict[str, str]]] = None,
    provider_type: str = "openai",
    options: Optional[GenerationOptions] = None,
) -> FactCheckResult:
    """
    Check facts in content against available sources.

    Orchestrates:
    1. Extract factual claims from content
    2. Validate each claim against sources
    3. Compute aggregate confidence

    Args:
        content: The text content to fact-check.
        sources: Optional list of source dicts with 'title', 'url', 'snippet'.
                 If None, falls back to web research.
        provider_type: LLM provider for extraction and validation.
        options: LLM generation options.

    Returns:
        FactCheckResult with per-claim verifications and aggregate stats.
    """
    # Step 1: Extract claims
    claims = extract_claims(content, provider_type, options)

    if not claims:
        logger.info("No factual claims extracted from content")
        return FactCheckResult(
            claims=[],
            overall_confidence=1.0,
            summary="No verifiable factual claims found in the content.",
        )

    # Step 2: If no sources provided, attempt web research
    if not sources:
        try:
            from src.research.web_researcher import conduct_web_research, extract_research_sources
            from src.types.research import SearchOptions

            # Use claim texts as search queries
            search_keywords = [c.text[:100] for c in claims[:5]]
            research = conduct_web_research(search_keywords, SearchOptions(num_results=5))
            raw_sources = extract_research_sources(research, max_sources=10)
            sources = [
                {"title": s.get("title", ""), "url": s.get("url", ""), "snippet": s.get("snippet", "")}
                for s in raw_sources
            ]
        except Exception as e:
            logger.warning("Web research for fact-checking failed: %s", e)
            sources = []

    # Step 3: Validate claims
    verifications = validate_claims(claims, sources or [], provider_type, options)

    # Step 4: Compute aggregate stats
    verified = sum(1 for v in verifications if v.status == VerificationStatus.VERIFIED)
    unverified = sum(1 for v in verifications if v.status == VerificationStatus.UNVERIFIED)
    contradicted = sum(1 for v in verifications if v.status == VerificationStatus.CONTRADICTED)

    if verifications:
        overall_confidence = sum(v.confidence for v in verifications) / len(verifications)
    else:
        overall_confidence = 0.0

    total = len(verifications)
    summary = (
        f"Checked {total} claim{'s' if total != 1 else ''}: "
        f"{verified} verified, {unverified} unverified, {contradicted} contradicted. "
        f"Overall confidence: {overall_confidence:.0%}."
    )

    logger.info(
        "Fact-check complete: %d claims, %d verified, %d contradicted, confidence=%.2f",
        total, verified, contradicted, overall_confidence,
    )

    return FactCheckResult(
        claims=verifications,
        overall_confidence=round(overall_confidence, 3),
        verified_count=verified,
        unverified_count=unverified,
        contradicted_count=contradicted,
        summary=summary,
    )
