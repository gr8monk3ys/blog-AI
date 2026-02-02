"""
Performance tracking service for content analytics.

This service handles:
- Tracking views, engagement, shares, and conversions
- Aggregating metrics (daily, weekly, monthly)
- Calculating performance trends
- Identifying top performing content
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..types.performance import (
    ContentPerformance,
    MetricType,
    PerformanceEvent,
    PerformanceSnapshot,
    PerformanceSummary,
    PerformanceTimeRange,
    PerformanceTrend,
    TrendDirection,
)

logger = logging.getLogger(__name__)


class PerformanceServiceError(Exception):
    """Exception raised for errors in the performance service."""

    pass


class PerformanceService:
    """
    Service for tracking and analyzing content performance.

    This service provides methods for recording performance events,
    aggregating metrics, and generating insights.
    """

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None,
        cache_ttl: int = 300,  # 5 minutes default cache
    ):
        """
        Initialize the performance service.

        Args:
            supabase_client: Optional Supabase client for database operations.
            redis_client: Optional Redis client for caching.
            cache_ttl: Cache TTL in seconds.
        """
        self._supabase = supabase_client
        self._redis = redis_client
        self._cache_ttl = cache_ttl
        self._initialized = False

    def _get_supabase(self) -> Optional[Any]:
        """Get or create Supabase client."""
        if self._supabase is not None:
            return self._supabase

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not configured for performance tracking")
            return None

        try:
            from supabase import create_client

            self._supabase = create_client(supabase_url, supabase_key)
            return self._supabase
        except ImportError:
            logger.warning("Supabase client not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            return None

    def _get_cache_key(self, prefix: str, *args: Any) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get a cached value if available."""
        if not self._redis:
            return None

        try:
            import json

            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache miss or error: {e}")
        return None

    async def _set_cached(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value."""
        if not self._redis:
            return

        try:
            import json

            await self._redis.setex(
                key,
                ttl or self._cache_ttl,
                json.dumps(value, default=str),
            )
        except Exception as e:
            logger.debug(f"Cache set error: {e}")

    # =========================================================================
    # Event Tracking
    # =========================================================================

    async def track_event(self, event: PerformanceEvent) -> bool:
        """
        Track a performance event.

        Args:
            event: The performance event to track.

        Returns:
            True if the event was tracked successfully.
        """
        supabase = self._get_supabase()
        if not supabase:
            logger.warning("Cannot track event: Supabase not configured")
            return False

        try:
            # Insert the event
            data = {
                "content_id": event.content_id,
                "event_type": event.event_type.value,
                "value": event.value,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata,
                "source": event.source,
                "platform": event.platform,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "referrer": event.referrer,
            }

            supabase.table("performance_events").insert(data).execute()

            # Update content_performance aggregate
            await self._update_content_performance(event)

            logger.debug(f"Tracked {event.event_type.value} event for content {event.content_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False

    async def track_view(
        self,
        content_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        is_unique: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a content view.

        Args:
            content_id: The content identifier.
            user_id: Optional user identifier.
            session_id: Optional session identifier.
            is_unique: Whether this is a unique view.
            metadata: Optional additional metadata.

        Returns:
            True if tracked successfully.
        """
        event_type = MetricType.UNIQUE_VIEW if is_unique else MetricType.VIEW
        event = PerformanceEvent(
            event_type=event_type,
            content_id=content_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            source="api",
        )
        return await self.track_event(event)

    async def track_engagement(
        self,
        content_id: str,
        time_on_page: Optional[float] = None,
        scroll_depth: Optional[float] = None,
        is_bounce: bool = False,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Track engagement metrics.

        Args:
            content_id: The content identifier.
            time_on_page: Time spent on page in seconds.
            scroll_depth: Scroll depth as a percentage (0-1).
            is_bounce: Whether this was a bounce.
            user_id: Optional user identifier.
            session_id: Optional session identifier.

        Returns:
            True if tracked successfully.
        """
        events_tracked = []

        if time_on_page is not None:
            event = PerformanceEvent(
                event_type=MetricType.TIME_ON_PAGE,
                content_id=content_id,
                value=time_on_page,
                user_id=user_id,
                session_id=session_id,
                source="api",
            )
            events_tracked.append(await self.track_event(event))

        if scroll_depth is not None:
            event = PerformanceEvent(
                event_type=MetricType.SCROLL_DEPTH,
                content_id=content_id,
                value=scroll_depth,
                user_id=user_id,
                session_id=session_id,
                source="api",
            )
            events_tracked.append(await self.track_event(event))

        if is_bounce:
            event = PerformanceEvent(
                event_type=MetricType.BOUNCE,
                content_id=content_id,
                value=1.0,
                user_id=user_id,
                session_id=session_id,
                source="api",
            )
            events_tracked.append(await self.track_event(event))

        return all(events_tracked) if events_tracked else False

    async def track_share(
        self,
        content_id: str,
        platform: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a content share.

        Args:
            content_id: The content identifier.
            platform: The platform shared to (twitter, facebook, linkedin, etc.).
            user_id: Optional user identifier.
            metadata: Optional additional metadata.

        Returns:
            True if tracked successfully.
        """
        event = PerformanceEvent(
            event_type=MetricType.SHARE,
            content_id=content_id,
            user_id=user_id,
            platform=platform,
            metadata=metadata or {},
            source="api",
        )
        return await self.track_event(event)

    async def track_conversion(
        self,
        content_id: str,
        conversion_type: str,
        value: float = 1.0,
        user_id: Optional[str] = None,
        revenue: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a conversion event.

        Args:
            content_id: The content identifier.
            conversion_type: Type of conversion (signup, purchase, download, etc.).
            value: Conversion value (default 1.0).
            user_id: Optional user identifier.
            revenue: Optional revenue amount.
            metadata: Optional additional metadata.

        Returns:
            True if tracked successfully.
        """
        event_metadata = metadata or {}
        event_metadata["conversion_type"] = conversion_type
        if revenue is not None:
            event_metadata["revenue"] = revenue

        event = PerformanceEvent(
            event_type=MetricType.CONVERSION,
            content_id=content_id,
            value=value,
            user_id=user_id,
            metadata=event_metadata,
            source="api",
        )
        return await self.track_event(event)

    # =========================================================================
    # Performance Aggregation
    # =========================================================================

    async def _update_content_performance(self, event: PerformanceEvent) -> None:
        """Update the aggregate content performance record."""
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            # Get or create performance record
            result = (
                supabase.table("content_performance")
                .select("*")
                .eq("content_id", event.content_id)
                .execute()
            )

            if result.data:
                # Update existing record
                record = result.data[0]
                updates = {"last_tracked_at": datetime.utcnow().isoformat()}

                if event.event_type == MetricType.VIEW:
                    updates["views"] = record.get("views", 0) + 1
                elif event.event_type == MetricType.UNIQUE_VIEW:
                    updates["unique_views"] = record.get("unique_views", 0) + 1
                elif event.event_type == MetricType.SHARE:
                    updates["shares"] = record.get("shares", 0) + 1
                    # Update platform-specific shares
                    shares_by_platform = record.get("shares_by_platform", {})
                    platform = event.platform or "unknown"
                    shares_by_platform[platform] = shares_by_platform.get(platform, 0) + 1
                    updates["shares_by_platform"] = shares_by_platform
                elif event.event_type == MetricType.CONVERSION:
                    updates["conversions"] = record.get("conversions", 0) + 1
                    if event.metadata.get("revenue"):
                        updates["revenue"] = record.get("revenue", 0) + event.metadata["revenue"]
                elif event.event_type == MetricType.BACKLINK:
                    updates["backlinks"] = record.get("backlinks", 0) + 1

                supabase.table("content_performance").update(updates).eq(
                    "content_id", event.content_id
                ).execute()
            else:
                # Create new record
                new_record = {
                    "content_id": event.content_id,
                    "content_type": event.metadata.get("content_type", "blog"),
                    "title": event.metadata.get("title", "Untitled"),
                    "views": 1 if event.event_type == MetricType.VIEW else 0,
                    "unique_views": 1 if event.event_type == MetricType.UNIQUE_VIEW else 0,
                    "shares": 1 if event.event_type == MetricType.SHARE else 0,
                    "conversions": 1 if event.event_type == MetricType.CONVERSION else 0,
                    "first_tracked_at": datetime.utcnow().isoformat(),
                    "last_tracked_at": datetime.utcnow().isoformat(),
                }
                supabase.table("content_performance").insert(new_record).execute()

        except Exception as e:
            logger.error(f"Failed to update content performance: {e}")

    async def get_content_performance(
        self,
        content_id: str,
        use_cache: bool = True,
    ) -> Optional[ContentPerformance]:
        """
        Get performance metrics for a specific content item.

        Args:
            content_id: The content identifier.
            use_cache: Whether to use cached data.

        Returns:
            ContentPerformance object or None if not found.
        """
        cache_key = self._get_cache_key("perf", content_id)

        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return ContentPerformance(**cached)

        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            result = (
                supabase.table("content_performance")
                .select("*")
                .eq("content_id", content_id)
                .execute()
            )

            if not result.data:
                return None

            record = result.data[0]
            performance = ContentPerformance(
                content_id=record["content_id"],
                content_type=record.get("content_type", "blog"),
                title=record.get("title", ""),
                views=record.get("views", 0),
                unique_views=record.get("unique_views", 0),
                time_on_page_seconds=record.get("time_on_page_seconds", 0.0),
                avg_scroll_depth=record.get("avg_scroll_depth", 0.0),
                bounce_rate=record.get("bounce_rate", 0.0),
                shares=record.get("shares", 0),
                shares_by_platform=record.get("shares_by_platform", {}),
                comments=record.get("comments", 0),
                reactions=record.get("reactions", 0),
                backlinks=record.get("backlinks", 0),
                referring_domains=record.get("referring_domains", 0),
                organic_traffic=record.get("organic_traffic", 0),
                conversions=record.get("conversions", 0),
                conversion_rate=record.get("conversion_rate", 0.0),
                revenue=record.get("revenue", 0.0),
                published_at=(
                    datetime.fromisoformat(record["published_at"])
                    if record.get("published_at")
                    else None
                ),
                first_tracked_at=(
                    datetime.fromisoformat(record["first_tracked_at"])
                    if record.get("first_tracked_at")
                    else None
                ),
                last_tracked_at=(
                    datetime.fromisoformat(record["last_tracked_at"])
                    if record.get("last_tracked_at")
                    else None
                ),
                url=record.get("url"),
                platform=record.get("platform"),
            )

            # Cache the result
            await self._set_cached(cache_key, performance.to_dict())

            return performance

        except Exception as e:
            logger.error(f"Failed to get content performance: {e}")
            return None

    async def create_daily_snapshot(self, content_id: str) -> Optional[PerformanceSnapshot]:
        """
        Create a daily performance snapshot for trending.

        Args:
            content_id: The content identifier.

        Returns:
            PerformanceSnapshot object or None if failed.
        """
        performance = await self.get_content_performance(content_id, use_cache=False)
        if not performance:
            return None

        snapshot = PerformanceSnapshot(
            content_id=content_id,
            snapshot_date=datetime.utcnow(),
            views=performance.views,
            unique_views=performance.unique_views,
            shares=performance.shares,
            backlinks=performance.backlinks,
            conversions=performance.conversions,
            engagement_score=performance.engagement_score,
        )

        supabase = self._get_supabase()
        if supabase:
            try:
                supabase.table("performance_snapshots").insert(snapshot.to_dict()).execute()
            except Exception as e:
                logger.error(f"Failed to save snapshot: {e}")
                return None

        return snapshot

    # =========================================================================
    # Summaries and Trends
    # =========================================================================

    async def get_performance_summary(
        self,
        time_range: PerformanceTimeRange = PerformanceTimeRange.MONTH,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> PerformanceSummary:
        """
        Get a summary of performance metrics.

        Args:
            time_range: The time range for the summary.
            organization_id: Optional organization filter.
            user_id: Optional user filter.
            use_cache: Whether to use cached data.

        Returns:
            PerformanceSummary object.
        """
        cache_key = self._get_cache_key("summary", time_range.value, organization_id, user_id)

        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return PerformanceSummary(**cached)

        supabase = self._get_supabase()
        if not supabase:
            return self._get_empty_summary(time_range)

        try:
            start_date, end_date = self._get_date_range(time_range)

            # Build query
            query = supabase.table("content_performance").select("*")

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            query = query.gte("last_tracked_at", start_date.isoformat())
            result = query.execute()

            if not result.data:
                return self._get_empty_summary(time_range)

            # Calculate aggregates
            total_views = sum(r.get("views", 0) for r in result.data)
            total_unique_views = sum(r.get("unique_views", 0) for r in result.data)
            total_shares = sum(r.get("shares", 0) for r in result.data)
            total_conversions = sum(r.get("conversions", 0) for r in result.data)

            time_on_page_values = [r.get("time_on_page_seconds", 0) for r in result.data if r.get("time_on_page_seconds")]
            bounce_rates = [r.get("bounce_rate", 0) for r in result.data if r.get("bounce_rate") is not None]

            avg_time_on_page = sum(time_on_page_values) / len(time_on_page_values) if time_on_page_values else 0
            avg_bounce_rate = sum(bounce_rates) / len(bounce_rates) if bounce_rates else 0

            # Calculate engagement scores
            engagement_scores = []
            for record in result.data:
                perf = ContentPerformance(
                    content_id=record["content_id"],
                    content_type=record.get("content_type", "blog"),
                    title=record.get("title", ""),
                    views=record.get("views", 0),
                    time_on_page_seconds=record.get("time_on_page_seconds", 0),
                    avg_scroll_depth=record.get("avg_scroll_depth", 0),
                    bounce_rate=record.get("bounce_rate", 0),
                    shares=record.get("shares", 0),
                    conversion_rate=record.get("conversion_rate", 0),
                )
                engagement_scores.append(perf.engagement_score)

            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0

            # Get top performing content
            top_content = sorted(
                result.data,
                key=lambda x: x.get("views", 0),
                reverse=True,
            )[:10]
            top_content_ids = [c["content_id"] for c in top_content]

            # Calculate trends
            trends = await self._calculate_trends(time_range, organization_id, user_id)

            summary = PerformanceSummary(
                time_range=time_range,
                total_content_items=len(result.data),
                total_views=total_views,
                total_unique_views=total_unique_views,
                total_shares=total_shares,
                total_conversions=total_conversions,
                avg_time_on_page=round(avg_time_on_page, 2),
                avg_bounce_rate=round(avg_bounce_rate, 4),
                avg_engagement_score=round(avg_engagement, 2),
                top_performing_content=top_content_ids,
                trends=trends,
            )

            # Cache the result
            await self._set_cached(cache_key, summary.to_dict())

            return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return self._get_empty_summary(time_range)

    def _get_empty_summary(self, time_range: PerformanceTimeRange) -> PerformanceSummary:
        """Return an empty summary."""
        return PerformanceSummary(
            time_range=time_range,
            total_content_items=0,
            total_views=0,
            total_unique_views=0,
            total_shares=0,
            total_conversions=0,
            avg_time_on_page=0.0,
            avg_bounce_rate=0.0,
            avg_engagement_score=0.0,
        )

    def _get_date_range(self, time_range: PerformanceTimeRange) -> Tuple[datetime, datetime]:
        """Convert time range to date range."""
        now = datetime.utcnow()

        if time_range == PerformanceTimeRange.HOUR:
            start = now - timedelta(hours=1)
        elif time_range == PerformanceTimeRange.DAY:
            start = now - timedelta(days=1)
        elif time_range == PerformanceTimeRange.WEEK:
            start = now - timedelta(days=7)
        elif time_range == PerformanceTimeRange.MONTH:
            start = now - timedelta(days=30)
        elif time_range == PerformanceTimeRange.QUARTER:
            start = now - timedelta(days=90)
        elif time_range == PerformanceTimeRange.YEAR:
            start = now - timedelta(days=365)
        else:  # ALL_TIME
            start = datetime(2020, 1, 1)

        return start, now

    async def _calculate_trends(
        self,
        time_range: PerformanceTimeRange,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, PerformanceTrend]:
        """Calculate performance trends."""
        supabase = self._get_supabase()
        if not supabase:
            return {}

        try:
            current_start, current_end = self._get_date_range(time_range)
            period_days = (current_end - current_start).days
            previous_start = current_start - timedelta(days=period_days)
            previous_end = current_start

            # Get current period data
            current_query = supabase.table("content_performance").select(
                "views, unique_views, shares, conversions"
            ).gte("last_tracked_at", current_start.isoformat())

            if organization_id:
                current_query = current_query.eq("organization_id", organization_id)
            if user_id:
                current_query = current_query.eq("user_id", user_id)

            current_result = current_query.execute()

            # Get previous period data
            previous_query = supabase.table("content_performance").select(
                "views, unique_views, shares, conversions"
            ).gte("last_tracked_at", previous_start.isoformat()).lt(
                "last_tracked_at", previous_end.isoformat()
            )

            if organization_id:
                previous_query = previous_query.eq("organization_id", organization_id)
            if user_id:
                previous_query = previous_query.eq("user_id", user_id)

            previous_result = previous_query.execute()

            # Calculate aggregates
            current_data = current_result.data or []
            previous_data = previous_result.data or []

            metrics = ["views", "unique_views", "shares", "conversions"]
            trends = {}

            for metric in metrics:
                current_total = sum(r.get(metric, 0) for r in current_data)
                previous_total = sum(r.get(metric, 0) for r in previous_data)

                trends[metric] = PerformanceTrend.calculate(
                    metric_name=metric,
                    current=current_total,
                    previous=previous_total,
                    time_range=time_range,
                )

            return trends

        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}

    async def get_top_performing_content(
        self,
        limit: int = 10,
        time_range: PerformanceTimeRange = PerformanceTimeRange.MONTH,
        sort_by: str = "views",
        organization_id: Optional[str] = None,
    ) -> List[ContentPerformance]:
        """
        Get top performing content.

        Args:
            limit: Maximum number of items to return.
            time_range: The time range to consider.
            sort_by: Metric to sort by (views, shares, conversions, engagement_score).
            organization_id: Optional organization filter.

        Returns:
            List of ContentPerformance objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            start_date, _ = self._get_date_range(time_range)

            query = supabase.table("content_performance").select("*")

            if organization_id:
                query = query.eq("organization_id", organization_id)

            query = query.gte("last_tracked_at", start_date.isoformat())
            query = query.order(sort_by, desc=True)
            query = query.limit(limit)

            result = query.execute()

            content_list = []
            for record in (result.data or []):
                performance = ContentPerformance(
                    content_id=record["content_id"],
                    content_type=record.get("content_type", "blog"),
                    title=record.get("title", ""),
                    views=record.get("views", 0),
                    unique_views=record.get("unique_views", 0),
                    time_on_page_seconds=record.get("time_on_page_seconds", 0.0),
                    avg_scroll_depth=record.get("avg_scroll_depth", 0.0),
                    bounce_rate=record.get("bounce_rate", 0.0),
                    shares=record.get("shares", 0),
                    shares_by_platform=record.get("shares_by_platform", {}),
                    conversions=record.get("conversions", 0),
                    conversion_rate=record.get("conversion_rate", 0.0),
                    url=record.get("url"),
                )
                content_list.append(performance)

            return content_list

        except Exception as e:
            logger.error(f"Failed to get top performing content: {e}")
            return []

    async def get_performance_trends(
        self,
        content_id: str,
        metric: str = "views",
        time_range: PerformanceTimeRange = PerformanceTimeRange.MONTH,
    ) -> PerformanceTrend:
        """
        Get performance trends for a specific content item.

        Args:
            content_id: The content identifier.
            metric: The metric to analyze.
            time_range: The time range for analysis.

        Returns:
            PerformanceTrend object.
        """
        supabase = self._get_supabase()
        if not supabase:
            return PerformanceTrend(
                metric_name=metric,
                current_value=0,
                previous_value=0,
                change_absolute=0,
                change_percent=0,
                direction=TrendDirection.STABLE,
                time_range=time_range,
            )

        try:
            # Get snapshots for the time range
            start_date, end_date = self._get_date_range(time_range)

            result = (
                supabase.table("performance_snapshots")
                .select("*")
                .eq("content_id", content_id)
                .gte("snapshot_date", start_date.isoformat())
                .lte("snapshot_date", end_date.isoformat())
                .order("snapshot_date")
                .execute()
            )

            if not result.data or len(result.data) < 2:
                return PerformanceTrend(
                    metric_name=metric,
                    current_value=0,
                    previous_value=0,
                    change_absolute=0,
                    change_percent=0,
                    direction=TrendDirection.STABLE,
                    time_range=time_range,
                )

            # Calculate trend from snapshots
            data_points = [
                {
                    "date": r["snapshot_date"],
                    "value": r.get(metric, 0),
                }
                for r in result.data
            ]

            # Get midpoint for comparison
            midpoint = len(data_points) // 2
            first_half = data_points[:midpoint]
            second_half = data_points[midpoint:]

            previous_avg = sum(d["value"] for d in first_half) / len(first_half) if first_half else 0
            current_avg = sum(d["value"] for d in second_half) / len(second_half) if second_half else 0

            return PerformanceTrend.calculate(
                metric_name=metric,
                current=current_avg,
                previous=previous_avg,
                time_range=time_range,
                data_points=data_points,
            )

        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return PerformanceTrend(
                metric_name=metric,
                current_value=0,
                previous_value=0,
                change_absolute=0,
                change_percent=0,
                direction=TrendDirection.STABLE,
                time_range=time_range,
            )
