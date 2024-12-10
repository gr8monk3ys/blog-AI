"""
Source quality scoring -- heuristic quality assessment for research sources.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from src.types.research import CredibilityTier, SourceQuality

logger = logging.getLogger(__name__)

# High-authority domains
_HIGH_AUTHORITY_DOMAINS = {
    ".edu", ".gov", ".mil",
}
_HIGH_AUTHORITY_EXACT = {
    "nature.com", "science.org", "thelancet.com", "bmj.com",
    "nytimes.com", "washingtonpost.com", "bbc.com", "bbc.co.uk",
    "reuters.com", "apnews.com", "economist.com",
    "hbr.org", "mckinsey.com", "forbes.com",
    "github.com", "stackoverflow.com", "arxiv.org",
    "wikipedia.org", "who.int", "cdc.gov",
}
_MEDIUM_AUTHORITY_EXACT = {
    "medium.com", "substack.com", "dev.to", "hackernoon.com",
    "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com",
    "zdnet.com", "cnet.com", "engadget.com",
    "investopedia.com", "healthline.com", "webmd.com",
    "hubspot.com", "moz.com", "semrush.com",
}


def _extract_domain(url: str) -> str:
    """Extract the registrable domain from a URL."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        # Strip www prefix
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname.lower()
    except Exception:
        return ""


def _score_domain_authority(url: str) -> tuple[float, CredibilityTier]:
    """Score domain authority using heuristic rules."""
    domain = _extract_domain(url)
    if not domain:
        return 20.0, CredibilityTier.UNKNOWN

    # Check TLD-based authority
    for tld in _HIGH_AUTHORITY_DOMAINS:
        if domain.endswith(tld):
            return 90.0, CredibilityTier.HIGH

    # Check exact domain matches
    if domain in _HIGH_AUTHORITY_EXACT:
        return 85.0, CredibilityTier.HIGH

    if domain in _MEDIUM_AUTHORITY_EXACT:
        return 60.0, CredibilityTier.MEDIUM

    # Default heuristic: unknown domains get a low score
    return 35.0, CredibilityTier.LOW


def _score_recency(snippet: str, url: str) -> float:
    """Score source recency based on date patterns in snippet/URL."""
    text = f"{snippet} {url}"
    current_year = datetime.now(timezone.utc).year

    # Look for year patterns
    year_pattern = re.compile(r'\b(20[0-9]{2})\b')
    years = [int(y) for y in year_pattern.findall(text)]

    if not years:
        return 50.0  # No date info, neutral score

    most_recent = max(years)
    age = current_year - most_recent

    if age <= 0:
        return 100.0
    if age == 1:
        return 85.0
    if age == 2:
        return 70.0
    if age <= 5:
        return 50.0
    return max(20.0, 50.0 - (age - 5) * 5)


def _score_relevance(snippet: str, title: str, keywords: list[str]) -> float:
    """Score relevance by keyword overlap."""
    if not keywords:
        return 50.0

    text = f"{title} {snippet}".lower()
    matched = sum(1 for kw in keywords if kw.lower() in text)
    ratio = matched / len(keywords)

    return min(100.0, ratio * 100.0)


def score_source_quality(
    url: str,
    title: str,
    snippet: str,
    keywords: Optional[list[str]] = None,
) -> SourceQuality:
    """
    Compute a composite quality score for a research source.

    Weights: authority 40%, recency 30%, relevance 30%.
    """
    authority, tier = _score_domain_authority(url)
    recency = _score_recency(snippet, url)
    relevance = _score_relevance(snippet, title, keywords or [])

    overall = authority * 0.4 + recency * 0.3 + relevance * 0.3

    return SourceQuality(
        domain_authority=authority,
        recency=recency,
        relevance=relevance,
        credibility_tier=tier,
        overall=overall,
    )
