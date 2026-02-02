"""
Analytics endpoints for Blog-AI dashboard.

Provides aggregated statistics about content generation,
tool usage, and activity timelines.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..auth import verify_api_key

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


# =============================================================================
# Supabase Client
# =============================================================================

_supabase_client = None


def get_supabase():
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Supabase not configured, using mock data")
        return None

    try:
        from supabase import create_client

        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except ImportError:
        logger.warning("Supabase Python client not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


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
    user_id: str = Depends(verify_api_key),
):
    """
    Get overview statistics.

    Returns aggregated statistics including total generations,
    tools used, active today, and popular tool.
    """
    logger.info(f"Analytics overview requested by user: {user_id}, range: {range}")

    supabase = get_supabase()
    if not supabase:
        return get_mock_overview()

    try:
        start, end = get_time_range_dates(range)
        start_iso = start.isoformat()
        end_iso = end.isoformat()
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Get total generations in range
        gen_result = (
            supabase.table("generated_content")
            .select("*", count="exact")
            .gte("created_at", start_iso)
            .lte("created_at", end_iso)
            .execute()
        )
        total_generations = gen_result.count or 0

        # Get unique tools used
        tools_result = supabase.table("tool_usage").select("tool_id").execute()
        total_tools_used = len(tools_result.data) if tools_result.data else 0

        # Get today's activity
        today_result = (
            supabase.table("generated_content")
            .select("*", count="exact")
            .gte("created_at", today)
            .execute()
        )
        active_today = today_result.count or 0

        # Get average execution time
        exec_result = (
            supabase.table("generated_content")
            .select("execution_time_ms")
            .gte("created_at", start_iso)
            .lte("created_at", end_iso)
            .execute()
        )
        exec_times = [r["execution_time_ms"] for r in (exec_result.data or [])]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0

        # Get most popular tool
        popular_result = (
            supabase.table("tool_usage")
            .select("tool_id, count")
            .order("count", desc=True)
            .limit(1)
            .execute()
        )
        popular_tool = (
            popular_result.data[0]["tool_id"]
            if popular_result.data
            else None
        )

        # Calculate change from previous period
        period_days = (end - start).days
        prev_start = start - timedelta(days=period_days)
        prev_end = start

        prev_result = (
            supabase.table("generated_content")
            .select("*", count="exact")
            .gte("created_at", prev_start.isoformat())
            .lte("created_at", prev_end.isoformat())
            .execute()
        )
        prev_generations = prev_result.count or 0

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
    user_id: str = Depends(verify_api_key),
):
    """
    Get tool usage statistics.

    Returns usage counts for each tool, sorted by popularity.
    """
    logger.info(f"Tool usage requested by user: {user_id}, range: {range}")

    supabase = get_supabase()
    if not supabase:
        return get_mock_tool_usage()[:limit]

    try:
        result = (
            supabase.table("tool_usage")
            .select("*")
            .order("count", desc=True)
            .limit(limit)
            .execute()
        )

        if not result.data:
            return get_mock_tool_usage()[:limit]

        total_count = sum(r["count"] for r in result.data)

        return [
            ToolUsageResponse(
                tool_id=r["tool_id"],
                tool_name=format_tool_name(r["tool_id"]),
                category=extract_category(r["tool_id"]),
                count=r["count"],
                last_used_at=r["last_used_at"],
                percentage=(r["count"] / total_count) * 100 if total_count > 0 else 0,
            )
            for r in result.data
        ]

    except Exception as e:
        logger.error(f"Error fetching tool usage: {e}")
        return get_mock_tool_usage()[:limit]


@router.get("/timeline", response_model=list[TimelineDataPoint])
async def get_timeline(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    user_id: str = Depends(verify_api_key),
):
    """
    Get generation timeline data.

    Returns daily generation counts over the specified time range.
    """
    logger.info(f"Timeline data requested by user: {user_id}, range: {range}")

    supabase = get_supabase()
    if not supabase:
        return get_mock_timeline(range)

    try:
        start, end = get_time_range_dates(range)

        result = (
            supabase.table("generated_content")
            .select("created_at")
            .gte("created_at", start.isoformat())
            .lte("created_at", end.isoformat())
            .order("created_at")
            .execute()
        )

        if not result.data:
            return get_mock_timeline(range)

        # Group by date
        grouped: dict[str, int] = {}
        for item in result.data:
            date = item["created_at"][:10]  # Extract YYYY-MM-DD
            grouped[date] = grouped.get(date, 0) + 1

        return [
            TimelineDataPoint(date=date, count=count)
            for date, count in sorted(grouped.items())
        ]

    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        return get_mock_timeline(range)


@router.get("/categories", response_model=list[CategoryBreakdown])
async def get_category_breakdown(
    range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    user_id: str = Depends(verify_api_key),
):
    """
    Get category breakdown statistics.

    Returns generation counts grouped by tool category.
    """
    logger.info(f"Category breakdown requested by user: {user_id}, range: {range}")

    supabase = get_supabase()
    if not supabase:
        return get_mock_categories()

    try:
        start, end = get_time_range_dates(range)

        result = (
            supabase.table("generated_content")
            .select("tool_id")
            .gte("created_at", start.isoformat())
            .lte("created_at", end.isoformat())
            .execute()
        )

        if not result.data:
            return get_mock_categories()

        # Group by category
        grouped: dict[str, int] = {}
        for item in result.data:
            category = extract_category(item["tool_id"])
            grouped[category] = grouped.get(category, 0) + 1

        total = sum(grouped.values())

        return [
            CategoryBreakdown(
                category=category,
                count=count,
                percentage=(count / total) * 100 if total > 0 else 0,
            )
            for category, count in sorted(
                grouped.items(), key=lambda x: x[1], reverse=True
            )
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
