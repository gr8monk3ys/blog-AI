"""
Deep research -- multi-provider research with quality scoring and depth levels.
"""

import logging
from typing import Optional

from src.research.source_quality import score_source_quality
from src.research.web_researcher import (
    conduct_web_research,
    extract_research_sources,
)
from src.types.research import (
    DeepResearchResult,
    QualityRatedSource,
    ResearchDepth,
    SearchOptions,
)

logger = logging.getLogger(__name__)

# Source limits per depth level
_DEPTH_CONFIG = {
    ResearchDepth.BASIC: {"max_sources": 5, "num_results": 5},
    ResearchDepth.DEEP: {"max_sources": 15, "num_results": 10},
    ResearchDepth.COMPREHENSIVE: {"max_sources": 25, "num_results": 15},
}


def conduct_deep_research(
    query: str,
    keywords: Optional[list[str]] = None,
    depth: ResearchDepth = ResearchDepth.BASIC,
    min_quality_score: float = 0.0,
) -> DeepResearchResult:
    """
    Conduct research at the specified depth level with quality scoring.

    Args:
        query: The research query.
        keywords: Optional keywords for relevance scoring.
        depth: Research depth level.
        min_quality_score: Minimum quality score to include a source.

    Returns:
        DeepResearchResult with quality-rated sources.
    """
    config = _DEPTH_CONFIG[depth]
    all_keywords = [query] + (keywords or [])

    options = SearchOptions(
        num_results=config["num_results"],
    )

    # Conduct research using existing multi-provider engine
    research_results = conduct_web_research(all_keywords, options)

    # Extract and de-duplicate sources
    raw_sources = extract_research_sources(
        research_results,
        max_sources=config["max_sources"] * 2,  # Over-fetch for quality filtering
    )

    total_found = len(raw_sources)

    # Score each source for quality
    rated_sources: list[QualityRatedSource] = []
    for src in raw_sources:
        quality = score_source_quality(
            url=src.get("url", ""),
            title=src.get("title", ""),
            snippet=src.get("snippet", ""),
            keywords=all_keywords,
        )

        if quality.overall < min_quality_score:
            continue

        rated_sources.append(
            QualityRatedSource(
                title=src.get("title", ""),
                url=src.get("url", ""),
                snippet=src.get("snippet", ""),
                provider=src.get("provider", ""),
                quality=quality,
            )
        )

    # Sort by quality score and trim to max
    rated_sources.sort(key=lambda s: s.quality.overall, reverse=True)
    rated_sources = rated_sources[:config["max_sources"]]

    # Build summary from top sources
    summary_parts = []
    for s in rated_sources[:3]:
        if s.snippet:
            summary_parts.append(f"- {s.title}: {s.snippet[:150]}")
    summary = "\n".join(summary_parts)

    logger.info(
        "Deep research complete: depth=%s, found=%d, after_filter=%d",
        depth.value,
        total_found,
        len(rated_sources),
    )

    return DeepResearchResult(
        query=query,
        depth=depth,
        sources=rated_sources,
        summary=summary,
        total_sources_found=total_found,
        sources_after_quality_filter=len(rated_sources),
    )
