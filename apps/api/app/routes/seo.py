"""
SEO content optimization API endpoints.

Provides endpoints for:
- SERP analysis: Fetch and analyze top Google results for a keyword
- Content optimization: Score content against SERP competitive data
- Content brief generation: Create a full writing brief from SERP analysis
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.seo.content_optimizer import (
    ContentOptimizerError,
    generate_content_brief,
    optimize_content,
)
from src.seo.serp_analyzer import SERPAnalyzerError, analyze_serp
from src.text_generation.core import (
    TextGenerationError,
    create_provider_from_env,
)
from src.types.providers import ProviderType
from src.types.seo import (
    ContentBrief,
    ContentOptimization,
    SERPAnalysis,
)

from ..middleware import require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seo", tags=["seo"])


# =============================================================================
# Request / Response Models
# =============================================================================


class AnalyzeSERPRequest(BaseModel):
    """Request model for SERP analysis."""

    keyword: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Target keyword to analyze in Google SERPs",
    )
    num_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of SERP results to analyze (1-20)",
    )
    location: str = Field(
        default="us",
        max_length=50,
        description="Geographic location for the search (e.g., 'us', 'uk')",
    )
    language: str = Field(
        default="en",
        max_length=10,
        description="Language code for the search (e.g., 'en', 'es')",
    )
    provider_type: Optional[str] = Field(
        default=None,
        description="LLM provider to use for analysis (openai, anthropic, gemini)",
    )


class AnalyzeSERPResponse(BaseModel):
    """Response model for SERP analysis."""

    success: bool = Field(..., description="Whether the analysis completed successfully")
    data: Optional[SERPAnalysis] = Field(None, description="SERP analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")


class OptimizeContentRequest(BaseModel):
    """Request model for content optimization."""

    content: str = Field(
        ...,
        min_length=50,
        max_length=200000,
        description="Draft content to optimize (50-200,000 characters)",
    )
    keyword: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Target keyword for the content",
    )
    serp_analysis: Optional[SERPAnalysis] = Field(
        None,
        description=(
            "Pre-computed SERP analysis data. If not provided, "
            "a fresh SERP analysis will be performed."
        ),
    )
    num_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of SERP results to analyze if serp_analysis is not provided",
    )
    provider_type: Optional[str] = Field(
        default=None,
        description="LLM provider to use for SERP analysis (openai, anthropic, gemini)",
    )


class OptimizeContentResponse(BaseModel):
    """Response model for content optimization."""

    success: bool = Field(
        ...,
        description="Whether the optimization completed successfully",
    )
    data: Optional[ContentOptimization] = Field(
        None,
        description="Content optimization results",
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class ContentBriefRequest(BaseModel):
    """Request model for content brief generation."""

    keyword: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Target keyword for the content brief",
    )
    serp_analysis: Optional[SERPAnalysis] = Field(
        None,
        description=(
            "Pre-computed SERP analysis data. If not provided, "
            "a fresh SERP analysis will be performed."
        ),
    )
    num_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of SERP results to analyze if serp_analysis is not provided",
    )
    location: str = Field(
        default="us",
        max_length=50,
        description="Geographic location for the search",
    )
    language: str = Field(
        default="en",
        max_length=10,
        description="Language code for the search",
    )
    provider_type: Optional[str] = Field(
        default=None,
        description="LLM provider to use (openai, anthropic, gemini)",
    )


class ContentBriefResponse(BaseModel):
    """Response model for content brief generation."""

    success: bool = Field(
        ...,
        description="Whether the brief generation completed successfully",
    )
    data: Optional[ContentBrief] = Field(
        None,
        description="Generated content brief",
    )
    error: Optional[str] = Field(None, description="Error message if failed")


# =============================================================================
# Helper Functions
# =============================================================================


def _resolve_provider(provider_type: Optional[str]):
    """
    Resolve the LLM provider from a provider_type string.

    Args:
        provider_type: Provider type string (openai, anthropic, gemini) or None.

    Returns:
        LLMProvider instance.

    Raises:
        HTTPException: If the provider cannot be created.
    """
    effective_type: ProviderType = provider_type or "openai"
    if effective_type not in ("openai", "anthropic", "gemini"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid provider_type '{effective_type}'. "
                "Must be one of: openai, anthropic, gemini"
            ),
        )
    try:
        return create_provider_from_env(effective_type)
    except TextGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider '{effective_type}' is not configured: {str(e)}",
        )


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/analyze-serp",
    response_model=AnalyzeSERPResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze SERPs for a keyword",
    description="""
Fetch and analyze the top Google search results for a target keyword.

Returns competitive intelligence including:
- Top-ranking page titles, URLs, and snippets
- Common topics and entities covered by competitors
- Suggested headings for a competitive article
- Questions the content should answer (including People Also Ask)
- Recommended word count based on competitor content
- Semantically related NLP terms for topical authority

**Requires:** SERP_API_KEY environment variable and at least one LLM provider.

**Cost:** 1 SERP API credit + 1 LLM call.
    """,
    responses={
        200: {"description": "SERP analysis completed successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
        502: {"description": "SERP API or LLM provider error"},
        503: {"description": "SERP API or LLM provider not configured"},
    },
)
async def analyze_serp_endpoint(
    request: AnalyzeSERPRequest,
    user_id: str = Depends(require_quota),
) -> AnalyzeSERPResponse:
    """
    Analyze SERPs for a keyword and return competitive intelligence.
    """
    logger.info(
        "SERP analysis requested by user: %s, keyword: %s",
        user_id,
        request.keyword,
    )

    try:
        provider = _resolve_provider(request.provider_type)

        result = analyze_serp(
            keyword=request.keyword,
            num_results=request.num_results,
            location=request.location,
            language=request.language,
            provider=provider,
        )

        logger.info(
            "SERP analysis completed: keyword='%s', results=%d, topics=%d, terms=%d",
            request.keyword,
            len(result.results),
            len(result.common_topics),
            len(result.nlp_terms),
        )

        return AnalyzeSERPResponse(success=True, data=result)

    except SERPAnalyzerError as e:
        logger.error("SERP analysis failed: %s", e)
        if "SERP_API_KEY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SERP API is not configured. Set SERP_API_KEY in environment.",
            )
        if "timed out" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="SERP API request timed out. Please try again.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SERP analysis failed: {str(e)}",
        )

    except TextGenerationError as e:
        logger.error("LLM analysis failed during SERP analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM analysis failed: {str(e)}",
        )

    except (ValueError, KeyError, TypeError) as e:
        logger.error("Unexpected error in SERP analysis: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.post(
    "/optimize-content",
    response_model=OptimizeContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Score and optimize content against SERP data",
    description="""
Score draft content against SERP competitive data and get actionable
optimization suggestions.

Returns a Surfer-SEO-style content score (0-100) broken down by:
- **Topic coverage**: How well the content covers competitor topics
- **Term usage**: How well NLP/semantic terms are utilized
- **Structure score**: How well headings align with competitor patterns
- **Word count score**: How well length matches competitive average
- **Readability score**: Content readability alignment

Also returns:
- Missing topics that competitors cover
- Missing NLP terms for topical authority
- Prioritized optimization suggestions

**Note:** You can pass a pre-computed `serp_analysis` to avoid redundant
SERP API calls, or omit it to have a fresh analysis performed automatically.

**Cost:** 0 SERP API credits if serp_analysis is provided, otherwise 1 credit + 1 LLM call.
    """,
    responses={
        200: {"description": "Content optimization completed"},
        400: {"description": "Invalid request (content too short, invalid provider)"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
        502: {"description": "SERP API or LLM provider error"},
    },
)
async def optimize_content_endpoint(
    request: OptimizeContentRequest,
    user_id: str = Depends(require_quota),
) -> OptimizeContentResponse:
    """
    Score content against SERP data and return optimization suggestions.
    """
    logger.info(
        "Content optimization requested by user: %s, keyword: %s, content_length: %d",
        user_id,
        request.keyword,
        len(request.content),
    )

    try:
        # Get or compute SERP analysis
        serp_analysis = request.serp_analysis
        if serp_analysis is None:
            provider = _resolve_provider(request.provider_type)
            serp_analysis = analyze_serp(
                keyword=request.keyword,
                num_results=request.num_results,
                provider=provider,
            )

        result = optimize_content(
            content=request.content,
            keyword=request.keyword,
            serp_analysis=serp_analysis,
        )

        logger.info(
            "Content optimization completed: keyword='%s', score=%.1f, "
            "missing_topics=%d, missing_terms=%d, suggestions=%d",
            request.keyword,
            result.score.overall_score,
            len(result.missing_topics),
            len(result.missing_terms),
            len(result.suggestions),
        )

        return OptimizeContentResponse(success=True, data=result)

    except SERPAnalyzerError as e:
        logger.error("SERP analysis failed during optimization: %s", e)
        if "SERP_API_KEY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SERP API is not configured. Set SERP_API_KEY in environment.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SERP analysis failed: {str(e)}",
        )

    except ContentOptimizerError as e:
        logger.error("Content optimization failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content optimization failed: {str(e)}",
        )

    except TextGenerationError as e:
        logger.error("LLM error during content optimization: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM analysis failed: {str(e)}",
        )

    except (ValueError, KeyError, TypeError) as e:
        logger.error("Unexpected error in content optimization: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.post(
    "/content-brief",
    response_model=ContentBriefResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a content brief from SERP analysis",
    description="""
Generate a comprehensive, writer-friendly content brief based on SERP
competitive analysis.

The brief includes:
- **Recommended title**: SEO-optimized title suggestion
- **Recommended outline**: Complete heading structure (8-15 sections)
- **Word count target**: Based on competitor content lengths
- **Terms to include**: Priority NLP terms for topical authority
- **Questions to answer**: Key questions the content should address
- **Competitor insights**: Summary of competitor strategies and content gaps
- **Tone guidance**: Recommended writing tone and style

**Note:** You can pass a pre-computed `serp_analysis` to avoid redundant
SERP API calls, or omit it to have a fresh analysis performed automatically.

**Cost:** 1 LLM call (+ 1 SERP API credit if serp_analysis is not provided).
    """,
    responses={
        200: {"description": "Content brief generated successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
        502: {"description": "SERP API or LLM provider error"},
        503: {"description": "Required service not configured"},
    },
)
async def content_brief_endpoint(
    request: ContentBriefRequest,
    user_id: str = Depends(require_quota),
) -> ContentBriefResponse:
    """
    Generate a content brief from SERP analysis for a target keyword.
    """
    logger.info(
        "Content brief requested by user: %s, keyword: %s",
        user_id,
        request.keyword,
    )

    try:
        provider = _resolve_provider(request.provider_type)

        # Get or compute SERP analysis
        serp_analysis = request.serp_analysis
        if serp_analysis is None:
            serp_analysis = analyze_serp(
                keyword=request.keyword,
                num_results=request.num_results,
                location=request.location,
                language=request.language,
                provider=provider,
            )

        result = generate_content_brief(
            keyword=request.keyword,
            serp_analysis=serp_analysis,
            provider=provider,
        )

        logger.info(
            "Content brief generated: keyword='%s', outline_sections=%d, terms=%d",
            request.keyword,
            len(result.recommended_outline),
            len(result.terms_to_include),
        )

        return ContentBriefResponse(success=True, data=result)

    except SERPAnalyzerError as e:
        logger.error("SERP analysis failed during brief generation: %s", e)
        if "SERP_API_KEY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SERP API is not configured. Set SERP_API_KEY in environment.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SERP analysis failed: {str(e)}",
        )

    except ContentOptimizerError as e:
        logger.error("Content brief generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content brief generation failed: {str(e)}",
        )

    except TextGenerationError as e:
        logger.error("LLM error during brief generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM analysis failed: {str(e)}",
        )

    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            "Unexpected error in content brief generation: %s", e, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
