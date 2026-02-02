"""
Performance analytics API endpoints.

Provides endpoints for:
- Tracking performance events (views, engagement, shares, conversions)
- Retrieving content performance metrics
- Getting performance summaries and trends
- SEO ranking data
- Content recommendations
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TrackEventRequest(BaseModel):
    """Request to track a performance event."""

    content_id: str = Field(..., description="Unique identifier for the content")
    event_type: Literal[
        "view", "unique_view", "time_on_page", "scroll_depth",
        "bounce", "share", "click", "conversion", "comment"
    ] = Field(..., description="Type of event to track")
    value: float = Field(default=1.0, description="Event value")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    platform: Optional[str] = Field(default=None, description="Platform (for shares)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TrackViewRequest(BaseModel):
    """Request to track a content view."""

    content_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    is_unique: bool = False
    referrer: Optional[str] = None
    user_agent: Optional[str] = None


class TrackEngagementRequest(BaseModel):
    """Request to track engagement metrics."""

    content_id: str
    time_on_page: Optional[float] = Field(default=None, ge=0, description="Time in seconds")
    scroll_depth: Optional[float] = Field(default=None, ge=0, le=1, description="Scroll depth 0-1")
    is_bounce: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TrackShareRequest(BaseModel):
    """Request to track a content share."""

    content_id: str
    platform: str = Field(..., description="Platform shared to (twitter, facebook, linkedin, etc.)")
    user_id: Optional[str] = None


class TrackConversionRequest(BaseModel):
    """Request to track a conversion."""

    content_id: str
    conversion_type: str = Field(..., description="Type of conversion (signup, purchase, download)")
    value: float = Field(default=1.0, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentPerformanceResponse(BaseModel):
    """Response containing content performance data."""

    content_id: str
    content_type: str
    title: str
    views: int
    unique_views: int
    time_on_page_seconds: float
    avg_scroll_depth: float
    bounce_rate: float
    shares: int
    shares_by_platform: Dict[str, int]
    comments: int
    backlinks: int
    conversions: int
    conversion_rate: float
    revenue: float
    engagement_score: float
    published_at: Optional[str]
    last_tracked_at: Optional[str]
    url: Optional[str]


class PerformanceSummaryResponse(BaseModel):
    """Response containing performance summary."""

    time_range: str
    total_content_items: int
    total_views: int
    total_unique_views: int
    total_shares: int
    total_conversions: int
    avg_time_on_page: float
    avg_bounce_rate: float
    avg_engagement_score: float
    top_performing_content: List[str]
    trends: Dict[str, Any]
    generated_at: str


class PerformanceTrendResponse(BaseModel):
    """Response containing trend data."""

    metric_name: str
    current_value: float
    previous_value: float
    change_absolute: float
    change_percent: float
    direction: str
    time_range: str
    data_points: List[Dict[str, Any]]


class SEORankingResponse(BaseModel):
    """Response containing SEO ranking data."""

    keyword: str
    position: int
    previous_position: Optional[int]
    change: int
    search_volume: Optional[int]
    url: Optional[str]
    tracked_at: str
    trend_direction: str


class SEOAnalysisResponse(BaseModel):
    """Response containing SEO analysis."""

    content_id: str
    url: str
    rankings: List[SEORankingResponse]
    avg_position: Optional[float]
    top_keywords: List[str]
    opportunities: List[str]
    analyzed_at: str


class RecommendationResponse(BaseModel):
    """Response containing a recommendation."""

    recommendation_type: str
    title: str
    description: str
    confidence: float
    priority: int
    data: Dict[str, Any]
    created_at: str


# =============================================================================
# Service Initialization
# =============================================================================


def get_performance_service():
    """Get the performance service instance."""
    from src.analytics.performance_service import PerformanceService

    return PerformanceService()


def get_seo_tracker():
    """Get the SEO tracker instance."""
    from src.analytics.seo_tracker import SEOTracker

    return SEOTracker()


def get_recommendation_engine():
    """Get the recommendation engine instance."""
    from src.analytics.recommendation_engine import RecommendationEngine

    return RecommendationEngine()


# =============================================================================
# Tracking Endpoints
# =============================================================================


@router.post("/track", status_code=status.HTTP_202_ACCEPTED)
async def track_event(
    request: TrackEventRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Track a performance event.

    This endpoint accepts various event types and records them for analytics.
    Events are processed asynchronously.

    Event types:
    - view: Page view
    - unique_view: Unique page view (deduplicated)
    - time_on_page: Time spent on page (value = seconds)
    - scroll_depth: Scroll depth (value = 0-1)
    - bounce: Bounce event
    - share: Content share (requires platform)
    - click: Link/button click
    - conversion: Conversion event (requires conversion_type in metadata)
    - comment: Comment on content
    """
    try:
        from src.types.performance import MetricType, PerformanceEvent

        service = get_performance_service()

        # Map string event type to enum
        event_type_map = {
            "view": MetricType.VIEW,
            "unique_view": MetricType.UNIQUE_VIEW,
            "time_on_page": MetricType.TIME_ON_PAGE,
            "scroll_depth": MetricType.SCROLL_DEPTH,
            "bounce": MetricType.BOUNCE,
            "share": MetricType.SHARE,
            "click": MetricType.CLICK,
            "conversion": MetricType.CONVERSION,
            "comment": MetricType.COMMENT,
        }

        event = PerformanceEvent(
            event_type=event_type_map[request.event_type],
            content_id=request.content_id,
            value=request.value,
            user_id=request.user_id,
            session_id=request.session_id,
            platform=request.platform,
            metadata=request.metadata,
            source="api",
        )

        success = await service.track_event(event)

        return {
            "success": success,
            "message": "Event tracked" if success else "Event tracking failed",
            "event_type": request.event_type,
            "content_id": request.content_id,
        }

    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track event: {str(e)}",
        )


@router.post("/track/view", status_code=status.HTTP_202_ACCEPTED)
async def track_view(
    request: TrackViewRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Track a content view.

    Simplified endpoint specifically for tracking page views.
    """
    try:
        service = get_performance_service()

        success = await service.track_view(
            content_id=request.content_id,
            user_id=request.user_id,
            session_id=request.session_id,
            is_unique=request.is_unique,
            metadata={
                "referrer": request.referrer,
                "user_agent": request.user_agent,
            },
        )

        return {
            "success": success,
            "message": "View tracked" if success else "View tracking failed",
        }

    except Exception as e:
        logger.error(f"Failed to track view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/track/engagement", status_code=status.HTTP_202_ACCEPTED)
async def track_engagement(
    request: TrackEngagementRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Track engagement metrics.

    Records time on page, scroll depth, and bounce events.
    """
    try:
        service = get_performance_service()

        success = await service.track_engagement(
            content_id=request.content_id,
            time_on_page=request.time_on_page,
            scroll_depth=request.scroll_depth,
            is_bounce=request.is_bounce,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        return {
            "success": success,
            "message": "Engagement tracked" if success else "Engagement tracking failed",
        }

    except Exception as e:
        logger.error(f"Failed to track engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/track/share", status_code=status.HTTP_202_ACCEPTED)
async def track_share(
    request: TrackShareRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Track a content share.

    Records when content is shared to social platforms.
    """
    try:
        service = get_performance_service()

        success = await service.track_share(
            content_id=request.content_id,
            platform=request.platform,
            user_id=request.user_id,
        )

        return {
            "success": success,
            "message": "Share tracked" if success else "Share tracking failed",
            "platform": request.platform,
        }

    except Exception as e:
        logger.error(f"Failed to track share: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/track/conversion", status_code=status.HTTP_202_ACCEPTED)
async def track_conversion(
    request: TrackConversionRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Track a conversion event.

    Records conversions like signups, purchases, or downloads.
    """
    try:
        service = get_performance_service()

        success = await service.track_conversion(
            content_id=request.content_id,
            conversion_type=request.conversion_type,
            value=request.value,
            user_id=request.user_id,
            revenue=request.revenue,
            metadata=request.metadata,
        )

        return {
            "success": success,
            "message": "Conversion tracked" if success else "Conversion tracking failed",
            "conversion_type": request.conversion_type,
        }

    except Exception as e:
        logger.error(f"Failed to track conversion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Performance Data Endpoints
# =============================================================================


@router.get("/content/{content_id}", response_model=ContentPerformanceResponse)
async def get_content_performance(
    content_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get performance metrics for a specific content item.

    Returns all tracked metrics including views, engagement, shares, and conversions.
    """
    try:
        service = get_performance_service()

        performance = await service.get_content_performance(content_id)

        if not performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No performance data found for content: {content_id}",
            )

        return ContentPerformanceResponse(
            content_id=performance.content_id,
            content_type=performance.content_type,
            title=performance.title,
            views=performance.views,
            unique_views=performance.unique_views,
            time_on_page_seconds=performance.time_on_page_seconds,
            avg_scroll_depth=performance.avg_scroll_depth,
            bounce_rate=performance.bounce_rate,
            shares=performance.shares,
            shares_by_platform=performance.shares_by_platform,
            comments=performance.comments,
            backlinks=performance.backlinks,
            conversions=performance.conversions,
            conversion_rate=performance.conversion_rate,
            revenue=performance.revenue,
            engagement_score=performance.engagement_score,
            published_at=performance.published_at.isoformat() if performance.published_at else None,
            last_tracked_at=performance.last_tracked_at.isoformat() if performance.last_tracked_at else None,
            url=performance.url,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    time_range: str = Query(default="30d", pattern="^(1h|24h|7d|30d|90d|365d|all)$"),
    organization_id: Optional[str] = Query(default=None),
    user_id: str = Depends(verify_api_key),
):
    """
    Get aggregated performance summary.

    Returns total metrics across all content for the specified time range.
    """
    try:
        from src.types.performance import PerformanceTimeRange

        service = get_performance_service()

        # Map string to enum
        range_map = {
            "1h": PerformanceTimeRange.HOUR,
            "24h": PerformanceTimeRange.DAY,
            "7d": PerformanceTimeRange.WEEK,
            "30d": PerformanceTimeRange.MONTH,
            "90d": PerformanceTimeRange.QUARTER,
            "365d": PerformanceTimeRange.YEAR,
            "all": PerformanceTimeRange.ALL_TIME,
        }

        summary = await service.get_performance_summary(
            time_range=range_map[time_range],
            organization_id=organization_id,
            user_id=user_id,
        )

        return PerformanceSummaryResponse(
            time_range=summary.time_range.value,
            total_content_items=summary.total_content_items,
            total_views=summary.total_views,
            total_unique_views=summary.total_unique_views,
            total_shares=summary.total_shares,
            total_conversions=summary.total_conversions,
            avg_time_on_page=summary.avg_time_on_page,
            avg_bounce_rate=summary.avg_bounce_rate,
            avg_engagement_score=summary.avg_engagement_score,
            top_performing_content=summary.top_performing_content,
            trends={k: v.to_dict() for k, v in summary.trends.items()},
            generated_at=summary.generated_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/top", response_model=List[ContentPerformanceResponse])
async def get_top_performing_content(
    limit: int = Query(default=10, ge=1, le=100),
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d|365d|all)$"),
    sort_by: str = Query(default="views", pattern="^(views|shares|conversions|engagement_score)$"),
    organization_id: Optional[str] = Query(default=None),
    user_id: str = Depends(verify_api_key),
):
    """
    Get top performing content.

    Returns content sorted by the specified metric.
    """
    try:
        from src.types.performance import PerformanceTimeRange

        service = get_performance_service()

        range_map = {
            "7d": PerformanceTimeRange.WEEK,
            "30d": PerformanceTimeRange.MONTH,
            "90d": PerformanceTimeRange.QUARTER,
            "365d": PerformanceTimeRange.YEAR,
            "all": PerformanceTimeRange.ALL_TIME,
        }

        content_list = await service.get_top_performing_content(
            limit=limit,
            time_range=range_map[time_range],
            sort_by=sort_by,
            organization_id=organization_id,
        )

        return [
            ContentPerformanceResponse(
                content_id=p.content_id,
                content_type=p.content_type,
                title=p.title,
                views=p.views,
                unique_views=p.unique_views,
                time_on_page_seconds=p.time_on_page_seconds,
                avg_scroll_depth=p.avg_scroll_depth,
                bounce_rate=p.bounce_rate,
                shares=p.shares,
                shares_by_platform=p.shares_by_platform,
                comments=p.comments,
                backlinks=p.backlinks,
                conversions=p.conversions,
                conversion_rate=p.conversion_rate,
                revenue=p.revenue,
                engagement_score=p.engagement_score,
                published_at=None,
                last_tracked_at=None,
                url=p.url,
            )
            for p in content_list
        ]

    except Exception as e:
        logger.error(f"Failed to get top performing content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/trends/{content_id}", response_model=PerformanceTrendResponse)
async def get_performance_trends(
    content_id: str,
    metric: str = Query(default="views", pattern="^(views|shares|conversions|engagement_score)$"),
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    user_id: str = Depends(verify_api_key),
):
    """
    Get performance trends for a content item.

    Returns historical data points for trend visualization.
    """
    try:
        from src.types.performance import PerformanceTimeRange

        service = get_performance_service()

        range_map = {
            "7d": PerformanceTimeRange.WEEK,
            "30d": PerformanceTimeRange.MONTH,
            "90d": PerformanceTimeRange.QUARTER,
        }

        trend = await service.get_performance_trends(
            content_id=content_id,
            metric=metric,
            time_range=range_map[time_range],
        )

        return PerformanceTrendResponse(
            metric_name=trend.metric_name,
            current_value=trend.current_value,
            previous_value=trend.previous_value,
            change_absolute=trend.change_absolute,
            change_percent=trend.change_percent,
            direction=trend.direction.value,
            time_range=trend.time_range.value,
            data_points=trend.data_points,
        )

    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# SEO Endpoints
# =============================================================================


@router.get("/seo/{content_id}", response_model=SEOAnalysisResponse)
async def get_seo_rankings(
    content_id: str,
    url: str = Query(..., description="Content URL to analyze"),
    keywords: Optional[str] = Query(default=None, description="Comma-separated keywords to track"),
    user_id: str = Depends(verify_api_key),
):
    """
    Get SEO rankings for a content item.

    Returns keyword rankings, position changes, and opportunities.
    """
    try:
        tracker = get_seo_tracker()

        if not tracker.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SEO tracking not configured. Set SERP_API_KEY environment variable.",
            )

        keyword_list = keywords.split(",") if keywords else None
        analysis = tracker.analyze_content_seo(
            content_id=content_id,
            url=url,
            keywords=keyword_list,
        )

        return SEOAnalysisResponse(
            content_id=analysis.content_id,
            url=analysis.url,
            rankings=[
                SEORankingResponse(
                    keyword=r.keyword,
                    position=r.position,
                    previous_position=r.previous_position,
                    change=r.change,
                    search_volume=r.search_volume,
                    url=r.url,
                    tracked_at=r.tracked_at.isoformat(),
                    trend_direction=r.trend_direction.value,
                )
                for r in analysis.rankings
            ],
            avg_position=analysis.avg_position,
            top_keywords=analysis.top_keywords,
            opportunities=analysis.opportunities,
            analyzed_at=analysis.analyzed_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SEO rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/seo/keyword/{keyword}/history")
async def get_keyword_ranking_history(
    keyword: str,
    url: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    user_id: str = Depends(verify_api_key),
):
    """
    Get ranking history for a keyword.

    Returns historical position data for trend analysis.
    """
    try:
        tracker = get_seo_tracker()

        history = tracker.get_ranking_history(
            keyword=keyword,
            target_url=url,
            days=days,
        )

        return {
            "keyword": keyword,
            "history": [
                {
                    "position": r.position,
                    "previous_position": r.previous_position,
                    "change": r.change,
                    "tracked_at": r.tracked_at.isoformat(),
                }
                for r in history
            ],
            "data_points": len(history),
        }

    except Exception as e:
        logger.error(f"Failed to get keyword history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Recommendations Endpoints
# =============================================================================


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    organization_id: Optional[str] = Query(default=None),
    limit_per_type: int = Query(default=3, ge=1, le=10),
    user_id: str = Depends(verify_api_key),
):
    """
    Get AI-powered content recommendations.

    Returns topic suggestions, optimal posting times, and format recommendations
    based on historical performance data.
    """
    try:
        engine = get_recommendation_engine()

        recommendations = await engine.get_all_recommendations(
            organization_id=organization_id,
            user_id=user_id,
            limit_per_type=limit_per_type,
        )

        return [
            RecommendationResponse(
                recommendation_type=r.recommendation_type.value,
                title=r.title,
                description=r.description,
                confidence=r.confidence,
                priority=r.priority,
                data=r.data,
                created_at=r.created_at.isoformat(),
            )
            for r in recommendations
        ]

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/recommendations/topics", response_model=List[RecommendationResponse])
async def get_topic_recommendations(
    organization_id: Optional[str] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
    user_id: str = Depends(verify_api_key),
):
    """
    Get topic recommendations.

    Returns suggested content topics based on historical performance.
    """
    try:
        engine = get_recommendation_engine()

        recommendations = await engine.get_topic_recommendations(
            organization_id=organization_id,
            user_id=user_id,
            limit=limit,
        )

        return [
            RecommendationResponse(
                recommendation_type=r.recommendation_type.value,
                title=r.title,
                description=r.description,
                confidence=r.confidence,
                priority=r.priority,
                data=r.to_dict().get("data", {}),
                created_at=r.created_at.isoformat(),
            )
            for r in recommendations
        ]

    except Exception as e:
        logger.error(f"Failed to get topic recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/recommendations/timing", response_model=List[RecommendationResponse])
async def get_timing_recommendations(
    organization_id: Optional[str] = Query(default=None),
    content_type: Optional[str] = Query(default=None),
    user_id: str = Depends(verify_api_key),
):
    """
    Get optimal posting time recommendations.

    Returns suggested days and times for publishing content.
    """
    try:
        engine = get_recommendation_engine()

        recommendations = await engine.get_timing_recommendations(
            organization_id=organization_id,
            user_id=user_id,
            content_type=content_type,
        )

        return [
            RecommendationResponse(
                recommendation_type=r.recommendation_type.value,
                title=r.title,
                description=r.description,
                confidence=r.confidence,
                priority=r.priority,
                data={
                    "day_of_week": r.day_of_week,
                    "hour_utc": r.hour_utc,
                    "expected_boost": r.expected_engagement_boost,
                },
                created_at=r.created_at.isoformat(),
            )
            for r in recommendations
        ]

    except Exception as e:
        logger.error(f"Failed to get timing recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
