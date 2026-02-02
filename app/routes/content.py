"""
Content quality and plagiarism checking endpoints.

Provides API endpoints for:
- Plagiarism detection with multiple provider support
- Content quality scoring
- Provider quota management
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.quality.plagiarism_checker import (
    PlagiarismCheckError,
    get_plagiarism_checker,
)
from src.types.plagiarism import (
    PlagiarismCheckRequest,
    PlagiarismCheckResponse,
    PlagiarismCheckResult,
    PlagiarismProvider,
    PlagiarismQuotaResponse,
    ProviderQuota,
)

from ..middleware import require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


class PlagiarismCheckAPIRequest(BaseModel):
    """API request model for plagiarism checking."""

    content: str = Field(
        ...,
        min_length=50,
        max_length=100000,
        description="Content to check for plagiarism (50-100,000 characters)"
    )
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional title for context"
    )
    exclude_urls: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="URLs to exclude from matching (e.g., your own website)"
    )
    provider: Optional[str] = Field(
        None,
        description="Preferred provider: copyscape, originality, or embedding"
    )
    skip_cache: bool = Field(
        default=False,
        description="Skip cache and force fresh plagiarism check"
    )


class PlagiarismCheckAPIResponse(BaseModel):
    """API response for plagiarism check."""

    success: bool = Field(..., description="Whether the check completed successfully")
    data: Optional[PlagiarismCheckResult] = Field(
        None,
        description="Plagiarism check result"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class QuotaAPIResponse(BaseModel):
    """API response for quota information."""

    success: bool
    data: Optional[PlagiarismQuotaResponse] = None
    error: Optional[str] = None


@router.post(
    "/check-plagiarism",
    response_model=PlagiarismCheckAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Check content for plagiarism",
    description="""
Check content for plagiarism using multiple detection providers.

**Providers supported:**
- **Copyscape** (primary): Industry-standard plagiarism detection
- **Originality.ai** (alternative): Combines plagiarism and AI detection
- **Embedding** (fallback): Local similarity check using embeddings

**Features:**
- Automatic provider fallback on failure
- Result caching to minimize API costs (24-hour TTL)
- Detailed matching source information
- Risk level classification

**Cost Optimization:**
Results are cached by content hash. Repeated checks for identical content
return cached results without consuming API credits.

**Rate Limiting:**
This endpoint is subject to your subscription tier's rate limits.
    """,
    responses={
        200: {
            "description": "Plagiarism check completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "check_id": "cs_abc123def456",
                            "status": "completed",
                            "provider": "copyscape",
                            "overall_score": 12.5,
                            "risk_level": "low",
                            "original_percentage": 87.5,
                            "matching_sources": [
                                {
                                    "url": "https://example.com/article",
                                    "title": "Similar Article",
                                    "similarity_percentage": 12.5,
                                    "matched_words": 45
                                }
                            ],
                            "total_words_checked": 500,
                            "cached": False
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request (content too short, invalid provider)"},
        401: {"description": "Authentication required"},
        402: {"description": "Insufficient API credits"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
        502: {"description": "Plagiarism provider error"},
    }
)
async def check_plagiarism(
    request: PlagiarismCheckAPIRequest,
    user_id: str = Depends(require_quota),
) -> PlagiarismCheckAPIResponse:
    """
    Check content for plagiarism.

    Supports multiple providers with automatic fallback.
    Results are cached to minimize API costs.
    """
    logger.info(
        f"Plagiarism check requested by user: {user_id}, "
        f"content_length: {len(request.content)}"
    )

    try:
        # Parse preferred provider if specified
        preferred_provider: Optional[PlagiarismProvider] = None
        if request.provider:
            try:
                preferred_provider = PlagiarismProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider. Must be one of: {', '.join(p.value for p in PlagiarismProvider)}"
                )

        # Build internal request
        check_request = PlagiarismCheckRequest(
            content=request.content,
            title=request.title,
            exclude_urls=request.exclude_urls,
            preferred_provider=preferred_provider,
            skip_cache=request.skip_cache,
        )

        # Get factory and perform check
        factory = get_plagiarism_checker()
        result = await factory.check_with_fallback(
            check_request,
            skip_cache=request.skip_cache,
        )

        logger.info(
            f"Plagiarism check completed: {result.check_id}, "
            f"score: {result.overall_score:.1f}%, "
            f"risk: {result.risk_level.value}, "
            f"cached: {result.cached}"
        )

        return PlagiarismCheckAPIResponse(
            success=True,
            data=result,
        )

    except PlagiarismCheckError as e:
        logger.error(f"Plagiarism check failed: {e}")

        # Map specific errors to HTTP status codes
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Plagiarism checking service is not configured. Contact support."
            )
        elif "insufficient credits" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient plagiarism API credits. Please contact support."
            )
        elif "too short" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        elif e.is_retryable:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Plagiarism check temporarily unavailable. Please retry."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Plagiarism check failed. Please try again later."
            )

    except Exception as e:
        logger.error(f"Unexpected error in plagiarism check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get(
    "/plagiarism/quota",
    response_model=QuotaAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get plagiarism API quota information",
    description="""
Get current quota and credit information for all configured plagiarism providers.

Returns remaining credits, daily limits, and availability status for each provider.
Useful for monitoring API usage and costs.
    """,
    responses={
        200: {
            "description": "Quota information retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "providers": [
                                {
                                    "provider": "copyscape",
                                    "remaining_credits": 150.0,
                                    "credits_per_check": 0.03,
                                    "is_available": True
                                },
                                {
                                    "provider": "originality",
                                    "remaining_credits": 500.0,
                                    "credits_per_check": 0.01,
                                    "is_available": True
                                }
                            ],
                            "recommended_provider": "originality"
                        }
                    }
                }
            }
        }
    }
)
async def get_plagiarism_quota(
    user_id: str = Depends(require_quota),
) -> QuotaAPIResponse:
    """
    Get quota information for all plagiarism providers.

    Returns credit balance and availability for each configured provider.
    """
    try:
        factory = get_plagiarism_checker()
        quotas = await factory.get_all_quotas()

        # Determine recommended provider (most cost-effective available)
        recommended: Optional[PlagiarismProvider] = None
        available_quotas = [q for q in quotas if q.is_available]

        if available_quotas:
            # Prefer lowest cost per check among available providers
            sorted_quotas = sorted(
                available_quotas,
                key=lambda q: (
                    q.credits_per_check if q.remaining_credits != 0 else float('inf')
                )
            )
            recommended = sorted_quotas[0].provider

        return QuotaAPIResponse(
            success=True,
            data=PlagiarismQuotaResponse(
                providers=quotas,
                recommended_provider=recommended,
            )
        )

    except Exception as e:
        logger.error(f"Failed to get plagiarism quota: {e}", exc_info=True)
        return QuotaAPIResponse(
            success=False,
            error="Failed to retrieve quota information"
        )


@router.get(
    "/plagiarism/providers",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List available plagiarism providers",
    description="Get a list of configured and available plagiarism detection providers."
)
async def list_plagiarism_providers() -> dict:
    """
    List available plagiarism detection providers.

    Returns configured providers and their status.
    """
    factory = get_plagiarism_checker()
    available = factory.get_available_providers()

    providers_info = []
    for provider in PlagiarismProvider:
        is_available = provider in available

        info = {
            "provider": provider.value,
            "is_configured": is_available,
            "description": _get_provider_description(provider),
        }

        if is_available:
            info["cost_estimate"] = _get_provider_cost(provider)

        providers_info.append(info)

    return {
        "success": True,
        "providers": providers_info,
        "configured_count": len(available),
    }


def _get_provider_description(provider: PlagiarismProvider) -> str:
    """Get human-readable description for a provider."""
    descriptions = {
        PlagiarismProvider.COPYSCAPE: (
            "Industry-standard plagiarism detection. Checks content against "
            "billions of web pages."
        ),
        PlagiarismProvider.ORIGINALITY: (
            "Advanced plagiarism and AI content detection. Combines "
            "plagiarism checking with AI-generated content detection."
        ),
        PlagiarismProvider.EMBEDDING: (
            "Fallback similarity checker using AI embeddings. Checks against "
            "locally stored content only, not web sources."
        ),
    }
    return descriptions.get(provider, "Unknown provider")


def _get_provider_cost(provider: PlagiarismProvider) -> str:
    """Get cost estimate for a provider."""
    costs = {
        PlagiarismProvider.COPYSCAPE: "~$0.03 per 100 words",
        PlagiarismProvider.ORIGINALITY: "~$0.01 per 100 words",
        PlagiarismProvider.EMBEDDING: "Minimal (uses OpenAI embedding API)",
    }
    return costs.get(provider, "Unknown")
