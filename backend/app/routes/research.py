"""
Deep research API endpoints.
"""

import asyncio
import json
import logging
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.organizations import AuthorizationContext
from src.research.deep_researcher import conduct_deep_research
from src.research.research_store import (
    get_cached_research,
    list_research_history,
    save_research,
)
from src.types.research import ResearchDepth

from ..dependencies import require_content_creation
from ..middleware import require_pro_tier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    keywords: list[str] = Field(default_factory=list)
    depth: str = Field(default="basic", description="basic, deep, or comprehensive")
    max_sources: int = Field(default=10, ge=1, le=50)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Conduct deep research on a topic",
)
async def research_topic(
    request: ResearchRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """Conduct deep research with quality-scored sources."""
    user_id = auth_ctx.user_id

    # Map depth string to enum
    try:
        depth = ResearchDepth(request.depth)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid depth: {request.depth}. Must be basic, deep, or comprehensive.",
        )

    # Deep/comprehensive require Pro tier
    if depth in (ResearchDepth.DEEP, ResearchDepth.COMPREHENSIVE):
        await require_pro_tier(user_id)

    # Check cache first
    cached = await get_cached_research(request.query, depth.value)
    if cached:
        return {"success": True, "cached": True, "data": cached}

    # Run deep research in thread pool (synchronous web_researcher under the hood)
    result = await asyncio.to_thread(
        partial(
            conduct_deep_research,
            query=request.query,
            keywords=request.keywords,
            depth=depth,
        )
    )

    # Persist results
    sources_data = [
        {
            "title": s.title,
            "url": s.url,
            "snippet": s.snippet,
            "provider": s.provider,
            "quality": s.quality.model_dump(),
        }
        for s in result.sources
    ]
    query_id = await save_research(
        user_id=user_id,
        query=request.query,
        keywords=request.keywords,
        depth=depth.value,
        sources=sources_data,
        summary=result.summary,
    )

    return {
        "success": True,
        "cached": False,
        "data": {
            "id": query_id,
            "query": result.query,
            "depth": result.depth.value,
            "sources": sources_data,
            "summary": result.summary,
            "total_sources_found": result.total_sources_found,
            "sources_after_quality_filter": result.sources_after_quality_filter,
        },
    }


@router.get(
    "/history",
    summary="List past research queries",
)
async def research_history(
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List the user's past research queries."""
    results = await list_research_history(auth_ctx.user_id, limit=limit, offset=offset)
    return {"success": True, "data": results}


@router.get(
    "/{query_id}",
    summary="Get specific research results",
)
async def get_research(
    query_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """Get the results for a specific research query."""
    from src.research.research_store import _queries

    # Check in-memory first
    record = _queries.get(query_id)
    if record:
        if record["user_id"] != auth_ctx.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research not found")
        return {"success": True, "data": record}

    # Try DB
    from src.db import fetchrow as db_fetchrow, is_database_configured

    if is_database_configured():
        try:
            row = await db_fetchrow(
                "SELECT * FROM research_queries WHERE id = $1 AND user_id = $2",
                query_id, auth_ctx.user_id,
            )
            if row:
                results = row["results_json"]
                if isinstance(results, str):
                    results = json.loads(results)
                return {
                    "success": True,
                    "data": {
                        "id": row["id"],
                        "query": row["query"],
                        "depth": row["depth"],
                        "sources": results or [],
                        "summary": row["summary"] or "",
                        "total_sources": row["total_sources"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    },
                }
        except Exception as e:
            logger.warning("Failed to fetch research from DB: %s", e)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research not found")
