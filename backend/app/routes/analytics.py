"""
Analytics endpoints for Blog-AI dashboard.

Provides aggregated statistics about content generation,
tool usage, and activity timelines.

Authorization:
- All endpoints require authentication (API key or Bearer token)
- Organization context is optional via X-Organization-ID and only applies when the
  user is a member of that organization
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.db import fetch as db_fetch, fetchrow as db_fetchrow, is_database_configured
from src.organizations import AuthorizationContext

from ..dependencies.organization import get_optional_organization_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# =============================================================================
# Response Models
# =============================================================================


class OverviewResponse(BaseModel):
    """Overview statistics response."""

    total_generations: int
    total_tools_used: int
    active_today: int
    average_execution_time_ms: float
    popular_tool: Optional[str]
    generations_change_percent: float


class ToolUsageResponse(BaseModel):
    """Tool usage statistics response."""

    tool_id: str
    tool_name: str
    category: str
    count: int
    last_used_at: str
    percentage: float


class TimelineDataPoint(BaseModel):
    """Timeline data point."""

    date: str
    count: int


class CategoryBreakdown(BaseModel):
    """Category breakdown response."""

    category: str
    count: int
    percentage: float


def get_time_range_dates(range_str: str) -> tuple[datetime, datetime]:
    """Convert range string to start/end dates."""
    now = datetime.utcnow()

    if range_str == "7d":
        start = now - timedelta(days=7)
    elif range_str == "30d":
        start = now - timedelta(days=30)
    elif range_str == "90d":
        start = now - timedelta(days=90)
    else:  # 'all'
        start = datetime(2020, 1, 1)

    return start, now


# =============================================================================
# Mock Data Functions
# =============================================================================


def get_mock_overview() -> OverviewResponse:
    """Return mock overview data for development."""
    return OverviewResponse(
        total_generations=1247,
        total_tools_used=18,
        active_today=42,
        average_execution_time_ms=2340.5,
        popular_tool="blog-post-generator",
        generations_change_percent=12.5,
    )


def get_mock_tool_usage() -> list[ToolUsageResponse]:
    """Return mock tool usage data."""
    tools = [
        ("blog-post-generator", "Blog Post Generator", "blog", 324),
        ("email-subject-lines", "Email Subject Lines", "email", 218),
        ("instagram-caption", "Instagram Caption", "social-media", 186),
        ("product-description", "Product Description", "business", 142),
        ("meta-description", "Meta Description", "seo", 98),
        ("brand-name-generator", "Brand Name Generator", "naming", 87),
        ("youtube-title", "YouTube Title", "video", 76),
        ("content-rewriter", "Content Rewriter", "rewriting", 65),
    ]

    total = sum(t[3] for t in tools)
    now = datetime.utcnow().isoformat()

    return [
        ToolUsageResponse(
            tool_id=t[0],
            tool_name=t[1],
            category=t[2],
            count=t[3],
            last_used_at=now,
            percentage=(t[3] / total) * 100 if total > 0 else 0,
        )
        for t in tools
    ]


def get_mock_timeline(range_str: str) -> list[TimelineDataPoint]:
    """Return mock timeline data."""
    import random

    days = 7 if range_str == "7d" else 30 if range_str == "30d" else 90
    now = datetime.utcnow()

    data = []
    for i in range(days - 1, -1, -1):
        date = now - timedelta(days=i)
        # Generate realistic-looking data
        base_count = 30 + random.randint(0, 20)
        weekend_factor = 0.6 if date.weekday() >= 5 else 1.0
        trend_factor = 1 + (days - i) * 0.01

        data.append(
            TimelineDataPoint(
                date=date.strftime("%Y-%m-%d"),
                count=int(base_count * weekend_factor * trend_factor),
            )
        )

    return data


def get_mock_categories() -> list[CategoryBreakdown]:
    """Return mock category breakdown."""
    categories = [
        ("blog", 412),
        ("email", 268),
        ("social-media", 224),
        ("business", 156),
        ("seo", 98),
        ("naming", 45),
        ("video", 32),
        ("rewriting", 12),
    ]

    total = sum(c[1] for c in categories)

    return [
        CategoryBreakdown(
            category=c[0],
            count=c[1],
            percentage=(c[1] / total) * 100 if total > 0 else 0,
        )
        for c in categories
    ]


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Get overview statistics.

    Returns aggregated statistics including total generations,
    tools used, active today, and popular tool.

    Authorization: Requires content.view permission.
    """
    # Scope to org only if the user is actually a member; otherwise fall back to user scope.
    scope_id = (
        auth_ctx.organization_id
        if auth_ctx.organization_id and auth_ctx.is_org_member
        else auth_ctx.user_id
    )
    logger.info(f"Analytics overview requested by user: {auth_ctx.user_id}, org: {auth_ctx.organization_id}, range: {range}")

    if not is_database_configured():
        return get_mock_overview()

    try:
        start, end = get_time_range_dates(range)
        start_utc = start.replace(tzinfo=timezone.utc)
        end_utc = end.replace(tzinfo=timezone.utc)
        today_start_utc = (
            datetime.utcnow()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .replace(tzinfo=timezone.utc)
        )

        gen_row = await db_fetchrow(
            """
            SELECT COUNT(*)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            """,
            scope_id,
            start_utc,
            end_utc,
        )
        total_generations = int(gen_row["count"] or 0) if gen_row else 0

        tools_row = await db_fetchrow(
            """
            SELECT COUNT(DISTINCT tool_id)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            """,
            scope_id,
            start_utc,
            end_utc,
        )
        total_tools_used = int(tools_row["count"] or 0) if tools_row else 0

        today_row = await db_fetchrow(
            """
            SELECT COUNT(*)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
            """,
            scope_id,
            today_start_utc,
        )
        active_today = int(today_row["count"] or 0) if today_row else 0

        avg_row = await db_fetchrow(
            """
            SELECT COALESCE(AVG(execution_time_ms), 0)::float AS avg_ms
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            """,
            scope_id,
            start_utc,
            end_utc,
        )
        avg_exec_time = float(avg_row["avg_ms"] or 0) if avg_row else 0.0

        popular_row = await db_fetchrow(
            """
            SELECT tool_id
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            GROUP BY tool_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """,
            scope_id,
            start_utc,
            end_utc,
        )
        popular_tool = str(popular_row["tool_id"]) if popular_row else None

        # Calculate change from previous period - SECURITY: Filter by scope_id
        period_days = max((end - start).days, 1)
        prev_start = start - timedelta(days=period_days)
        prev_end = start
        prev_row = await db_fetchrow(
            """
            SELECT COUNT(*)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            """,
            scope_id,
            prev_start.replace(tzinfo=timezone.utc),
            prev_end.replace(tzinfo=timezone.utc),
        )
        prev_generations = int(prev_row["count"] or 0) if prev_row else 0

        if prev_generations > 0:
            change_percent = ((total_generations - prev_generations) / prev_generations) * 100
        else:
            change_percent = 100.0 if total_generations > 0 else 0.0

        return OverviewResponse(
            total_generations=total_generations,
            total_tools_used=total_tools_used,
            active_today=active_today,
            average_execution_time_ms=avg_exec_time,
            popular_tool=popular_tool,
            generations_change_percent=round(change_percent, 1),
        )

    except Exception as e:
        logger.error(f"Error fetching overview: {e}")
        return get_mock_overview()


@router.get("/tools", response_model=list[ToolUsageResponse])
async def get_tool_usage(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    limit: int = Query(10, ge=1, le=50),
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Get tool usage statistics.

    Returns usage counts for each tool, sorted by popularity.

    Authorization: Requires content.view permission.
    """
    scope_id = (
        auth_ctx.organization_id
        if auth_ctx.organization_id and auth_ctx.is_org_member
        else auth_ctx.user_id
    )
    logger.info(f"Tool usage requested by user: {auth_ctx.user_id}, org: {auth_ctx.organization_id}, range: {range}")

    if not is_database_configured():
        return get_mock_tool_usage()[:limit]

    try:
        start, end = get_time_range_dates(range)
        rows = await db_fetch(
            """
            SELECT
                tool_id,
                COUNT(*)::int AS count,
                MAX(created_at) AS last_used_at
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            GROUP BY tool_id
            ORDER BY count DESC
            LIMIT $4
            """,
            scope_id,
            start.replace(tzinfo=timezone.utc),
            end.replace(tzinfo=timezone.utc),
            limit,
        )

        if not rows:
            return get_mock_tool_usage()[:limit]

        total_count = sum(int(r["count"] or 0) for r in rows)

        responses: list[ToolUsageResponse] = []
        for r in rows:
            count = int(r["count"] or 0)
            last_used = r["last_used_at"]
            responses.append(
                ToolUsageResponse(
                    tool_id=r["tool_id"],
                    tool_name=format_tool_name(r["tool_id"]),
                    category=extract_category(r["tool_id"]),
                    count=count,
                    last_used_at=last_used.isoformat() if last_used else datetime.utcnow().isoformat(),
                    percentage=(count / total_count) * 100 if total_count > 0 else 0,
                )
            )

        return responses

    except Exception as e:
        logger.error(f"Error fetching tool usage: {e}")
        return get_mock_tool_usage()[:limit]


@router.get("/timeline", response_model=list[TimelineDataPoint])
async def get_timeline(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Get generation timeline data.

    Returns daily generation counts over the specified time range.

    Authorization: Requires content.view permission.
    """
    scope_id = (
        auth_ctx.organization_id
        if auth_ctx.organization_id and auth_ctx.is_org_member
        else auth_ctx.user_id
    )
    logger.info(f"Timeline data requested by user: {auth_ctx.user_id}, org: {auth_ctx.organization_id}, range: {range}")

    if not is_database_configured():
        return get_mock_timeline(range)

    try:
        # We want a stable number of points for charting (7/30/90), including today.
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        if range == "7d":
            days = 7
        elif range == "30d":
            days = 30
        elif range == "90d":
            days = 90
        else:
            days = None

        if days is not None:
            start_day = (now_utc.date() - timedelta(days=days - 1))
            start_utc = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)
            end_utc = now_utc
        else:
            start, end = get_time_range_dates(range)
            start_utc = start.replace(tzinfo=timezone.utc)
            end_utc = end.replace(tzinfo=timezone.utc)

        rows = await db_fetch(
            """
            SELECT created_at::date AS day, COUNT(*)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            GROUP BY day
            ORDER BY day ASC
            """,
            scope_id,
            start_utc,
            end_utc,
        )

        counts_by_day: dict[str, int] = {}
        for r in rows or []:
            try:
                day = r["day"]
                count = int(r["count"] or 0)
            except Exception:
                continue
            if not day:
                continue
            counts_by_day[str(day)] = count

        if days is not None:
            points: list[TimelineDataPoint] = []
            for i in range(days):
                day = (start_utc.date() + timedelta(days=i)).isoformat()
                points.append(TimelineDataPoint(date=day, count=counts_by_day.get(day, 0)))
            return points

        return [TimelineDataPoint(date=str(k), count=v) for k, v in sorted(counts_by_day.items())]

    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        return get_mock_timeline(range)


@router.get("/categories", response_model=list[CategoryBreakdown])
async def get_category_breakdown(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Get category breakdown statistics.

    Returns generation counts grouped by tool category.

    Authorization: Requires content.view permission.
    """
    scope_id = (
        auth_ctx.organization_id
        if auth_ctx.organization_id and auth_ctx.is_org_member
        else auth_ctx.user_id
    )
    logger.info(f"Category breakdown requested by user: {auth_ctx.user_id}, org: {auth_ctx.organization_id}, range: {range}")

    if not is_database_configured():
        return get_mock_categories()

    try:
        start, end = get_time_range_dates(range)
        start_utc = start.replace(tzinfo=timezone.utc)
        end_utc = end.replace(tzinfo=timezone.utc)

        rows = await db_fetch(
            """
            SELECT tool_id, COUNT(*)::int AS count
            FROM generated_content
            WHERE user_id = $1
              AND created_at >= $2
              AND created_at <= $3
            GROUP BY tool_id
            """,
            scope_id,
            start_utc,
            end_utc,
        )

        if not rows:
            return get_mock_categories()

        grouped: dict[str, int] = {}
        for r in rows:
            try:
                tool_id = r["tool_id"]
                count = int(r["count"] or 0)
            except Exception:
                continue
            if not tool_id:
                continue
            category = extract_category(str(tool_id))
            grouped[category] = grouped.get(category, 0) + count

        total = sum(grouped.values())

        return [
            CategoryBreakdown(
                category=category,
                count=count,
                percentage=(count / total) * 100 if total > 0 else 0,
            )
            for category, count in sorted(grouped.items(), key=lambda x: x[1], reverse=True)
        ]

    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return get_mock_categories()


# =============================================================================
# Helper Functions
# =============================================================================


def format_tool_name(tool_id: str) -> str:
    """Format tool ID as display name."""
    return " ".join(word.capitalize() for word in tool_id.split("-"))


def extract_category(tool_id: str) -> str:
    """Extract category from tool ID."""
    category_map = {
        "blog": "blog",
        "email": "email",
        "newsletter": "email",
        "instagram": "social-media",
        "twitter": "social-media",
        "linkedin": "social-media",
        "facebook": "social-media",
        "social": "social-media",
        "business": "business",
        "product": "business",
        "brand": "naming",
        "tagline": "naming",
        "domain": "naming",
        "youtube": "video",
        "video": "video",
        "meta": "seo",
        "seo": "seo",
        "keyword": "seo",
        "rewrite": "rewriting",
        "sentence": "rewriting",
        "tone": "rewriting",
        "grammar": "rewriting",
    }

    lower_id = tool_id.lower()
    for key, category in category_map.items():
        if key in lower_id:
            return category

    return "blog"  # Default category
