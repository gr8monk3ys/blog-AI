"""
Fact-checking API endpoints.
"""

import asyncio
import logging
from functools import partial
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.fact_checking.fact_checker import check_facts
from src.organizations import AuthorizationContext
from src.text_generation.core import GenerationOptions

from ..dependencies import require_content_creation
from ..middleware import require_pro_tier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fact-check", tags=["fact-check"])


class FactCheckRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=50000)
    sources: Optional[list[dict]] = Field(
        default=None,
        description="Optional sources to check against (title, url, snippet dicts)",
    )


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Check facts in content",
)
async def fact_check_content(
    request: FactCheckRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """
    Extract and verify factual claims in the provided content.

    If no sources are provided, the system will attempt web research
    to find relevant sources for verification.
    """
    await require_pro_tier(auth_ctx.user_id)

    result = await asyncio.to_thread(
        partial(
            check_facts,
            content=request.content,
            sources=request.sources,
        )
    )

    return {
        "success": True,
        "data": {
            "overall_confidence": result.overall_confidence,
            "verified_count": result.verified_count,
            "unverified_count": result.unverified_count,
            "contradicted_count": result.contradicted_count,
            "summary": result.summary,
            "claims": [
                {
                    "text": v.claim.text,
                    "claim_type": v.claim.claim_type.value,
                    "status": v.status.value,
                    "confidence": v.confidence,
                    "explanation": v.explanation,
                    "supporting_sources": v.supporting_sources,
                }
                for v in result.claims
            ],
        },
    }
