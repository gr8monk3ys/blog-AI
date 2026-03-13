"""
Dashboard service for analytics data aggregation.

This module provides:
- Real-time stats aggregation
- Comparison periods (this week vs last week)
- Dashboard data formatting
- Export functionality (CSV, JSON)
"""

import csv
import io
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

from ..types.performance import (
    ContentPerformance,
    PerformanceSummary,
    PerformanceTimeRange,
    PerformanceTrend,
    TrendDirection,
)

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetric:
    """A single dashboard metric card."""

    name: str
    value: float
    formatted_value: str
    change_value: float
    change_percent: float
    change_direction: TrendDirection
    comparison_period: str
    icon: Optional[str] = None
    color: Optional[str] = None


@dataclass
class DashboardChart:
    """Chart data for dashboard visualization."""

    chart_type: Literal["line", "bar", "pie", "area"]
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardData:
    """Complete dashboard data package."""

    metrics: List[DashboardMetric]
    charts: List[DashboardChart]
    top_content: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "formatted_value": m.formatted_value,
                    "change_value": m.change_value,
                    "change_percent": m.change_percent,
                    "change_direction": m.change_direction.value,
                    "comparison_period": m.comparison_period,
                    "icon": m.icon,
                    "color": m.color,
                }
                for m in self.metrics
            ],
            "charts": [
                {
                    "chart_type": c.chart_type,
                    "title": c.title,
                    "labels": c.labels,
                    "datasets": c.datasets,
                    "options": c.options,
                }
                for c in self.charts
            ],
            "top_content": self.top_content,
            "recent_activity": self.recent_activity,
            "generated_at": self.generated_at.isoformat(),
        }


class DashboardService:
    """
    Service for generating dashboard analytics data.

    This service aggregates performance data into dashboard-ready
    formats with charts, metrics, and comparisons.
    """

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None,
        cache_ttl: int = 60,  # 1 minute cache for real-time feel
    ):
        """
        Initialize the dashboard service.

        Args:
            supabase_client: Optional Supabase client.
            redis_client: Optional Redis client for caching.
            cache_ttl: Cache TTL in seconds.
        """
        self._supabase = supabase_client
        self._redis = redis_client
        self._cache_ttl = cache_ttl

    def _get_supabase(self) -> Optional[Any]:
        """Get or create Supabase client."""
        if self._supabase is not None:
            return self._supabase

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_key:
            return None

        try:
            from supabase import create_client

            self._supabase = create_client(supabase_url, supabase_key)
            return self._supabase
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            return None

    # =========================================================================
    # Dashboard Data Generation
    # =========================================================================

    async def get_dashboard_data(
        self,
        time_range: PerformanceTimeRange = PerformanceTimeRange.MONTH,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> DashboardData:
        """
        Get complete dashboard data.

        Args:
            time_range: Time range for the dashboard.
            organization_id: Optional organization filter.
            user_id: Optional user filter.

        Returns:
            DashboardData object with metrics, charts, and lists.
        """
        # Get current and previous period data
        current_data = await self._get_period_data(time_range, organization_id, user_id)
        previous_data = await self._get_previous_period_data(time_range, organization_id, user_id)

        # Build metrics cards
        metrics = self._build_metrics(current_data, previous_data, time_range)

        # Build charts
        charts = await self._build_charts(time_range, organization_id, user_id)

        # Get top content
        top_content = await self._get_top_content_list(organization_id, user_id, limit=5)

        # Get recent activity
        recent_activity = await self._get_recent_activity(organization_id, user_id, limit=10)

        return DashboardData(
            metrics=metrics,
            charts=charts,
            top_content=top_content,
            recent_activity=recent_activity,
        )

    async def _get_period_data(
        self,
        time_range: PerformanceTimeRange,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> Dict[str, Any]:
        """Get aggregated data for a time period."""
        supabase = self._get_supabase()
        if not supabase:
            return self._get_empty_period_data()

        try:
            start_date, end_date = self._get_date_range(time_range)

            query = supabase.table("content_performance").select(
                "views, unique_views, shares, conversions, time_on_page_seconds, bounce_rate"
            ).gte("last_tracked_at", start_date.isoformat())

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data:
                return self._get_empty_period_data()

            return {
                "views": sum(r.get("views", 0) for r in result.data),
                "unique_views": sum(r.get("unique_views", 0) for r in result.data),
                "shares": sum(r.get("shares", 0) for r in result.data),
                "conversions": sum(r.get("conversions", 0) for r in result.data),
                "avg_time_on_page": self._safe_average(
                    [r.get("time_on_page_seconds", 0) for r in result.data]
                ),
                "avg_bounce_rate": self._safe_average(
                    [r.get("bounce_rate", 0) for r in result.data]
                ),
                "content_count": len(result.data),
            }

        except Exception as e:
            logger.error(f"Failed to get period data: {e}")
            return self._get_empty_period_data()

    async def _get_previous_period_data(
        self,
        time_range: PerformanceTimeRange,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> Dict[str, Any]:
        """Get aggregated data for the previous period."""
        supabase = self._get_supabase()
        if not supabase:
            return self._get_empty_period_data()

        try:
            current_start, current_end = self._get_date_range(time_range)
            period_days = (current_end - current_start).days
            previous_start = current_start - timedelta(days=period_days)
            previous_end = current_start

            query = supabase.table("content_performance").select(
                "views, unique_views, shares, conversions, time_on_page_seconds, bounce_rate"
            ).gte("last_tracked_at", previous_start.isoformat()).lt(
                "last_tracked_at", previous_end.isoformat()
            )

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data:
                return self._get_empty_period_data()

            return {
                "views": sum(r.get("views", 0) for r in result.data),
                "unique_views": sum(r.get("unique_views", 0) for r in result.data),
                "shares": sum(r.get("shares", 0) for r in result.data),
                "conversions": sum(r.get("conversions", 0) for r in result.data),
                "avg_time_on_page": self._safe_average(
                    [r.get("time_on_page_seconds", 0) for r in result.data]
                ),
                "avg_bounce_rate": self._safe_average(
                    [r.get("bounce_rate", 0) for r in result.data]
                ),
                "content_count": len(result.data),
            }

        except Exception as e:
            logger.error(f"Failed to get previous period data: {e}")
            return self._get_empty_period_data()

    def _get_empty_period_data(self) -> Dict[str, Any]:
        """Return empty period data structure."""
        return {
            "views": 0,
            "unique_views": 0,
            "shares": 0,
            "conversions": 0,
            "avg_time_on_page": 0.0,
            "avg_bounce_rate": 0.0,
            "content_count": 0,
        }

    def _build_metrics(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any],
        time_range: PerformanceTimeRange,
    ) -> List[DashboardMetric]:
        """Build dashboard metric cards."""
        comparison = self._get_comparison_label(time_range)

        metrics = []

        # Total Views
        metrics.append(
            self._create_metric(
                name="Total Views",
                current_value=current["views"],
                previous_value=previous["views"],
                comparison_period=comparison,
                formatter=self._format_number,
                icon="eye",
                color="blue",
            )
        )

        # Unique Visitors
        metrics.append(
            self._create_metric(
                name="Unique Visitors",
                current_value=current["unique_views"],
                previous_value=previous["unique_views"],
                comparison_period=comparison,
                formatter=self._format_number,
                icon="users",
                color="green",
            )
        )

        # Social Shares
        metrics.append(
            self._create_metric(
                name="Social Shares",
                current_value=current["shares"],
                previous_value=previous["shares"],
                comparison_period=comparison,
                formatter=self._format_number,
                icon="share",
                color="purple",
            )
        )

        # Conversions
        metrics.append(
            self._create_metric(
                name="Conversions",
                current_value=current["conversions"],
                previous_value=previous["conversions"],
                comparison_period=comparison,
                formatter=self._format_number,
                icon="target",
                color="orange",
            )
        )

        # Avg Time on Page
        metrics.append(
            self._create_metric(
                name="Avg. Time on Page",
                current_value=current["avg_time_on_page"],
                previous_value=previous["avg_time_on_page"],
                comparison_period=comparison,
                formatter=self._format_duration,
                icon="clock",
                color="teal",
            )
        )

        # Bounce Rate (inverted - lower is better)
        bounce_metric = self._create_metric(
            name="Bounce Rate",
            current_value=current["avg_bounce_rate"] * 100,
            previous_value=previous["avg_bounce_rate"] * 100,
            comparison_period=comparison,
            formatter=self._format_percent,
            icon="arrow-left",
            color="red",
        )
        # Invert direction for bounce rate (lower is better)
        if bounce_metric.change_direction == TrendDirection.UP:
            bounce_metric.change_direction = TrendDirection.DOWN
        elif bounce_metric.change_direction == TrendDirection.DOWN:
            bounce_metric.change_direction = TrendDirection.UP
        metrics.append(bounce_metric)

        return metrics

    def _create_metric(
        self,
        name: str,
        current_value: float,
        previous_value: float,
        comparison_period: str,
        formatter: callable,
        icon: Optional[str] = None,
        color: Optional[str] = None,
    ) -> DashboardMetric:
        """Create a dashboard metric."""
        change_value = current_value - previous_value
        change_percent = (
            (change_value / previous_value * 100)
            if previous_value != 0
            else (100.0 if current_value > 0 else 0.0)
        )

        if change_percent > 5:
            direction = TrendDirection.UP
        elif change_percent < -5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return DashboardMetric(
            name=name,
            value=current_value,
            formatted_value=formatter(current_value),
            change_value=change_value,
            change_percent=round(change_percent, 1),
            change_direction=direction,
            comparison_period=comparison_period,
            icon=icon,
            color=color,
        )

    async def _build_charts(
        self,
        time_range: PerformanceTimeRange,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> List[DashboardChart]:
        """Build dashboard charts."""
        charts = []

        # Views over time chart
        views_chart = await self._build_views_chart(time_range, organization_id, user_id)
        if views_chart:
            charts.append(views_chart)

        # Content type breakdown
        type_chart = await self._build_content_type_chart(organization_id, user_id)
        if type_chart:
            charts.append(type_chart)

        # Platform shares breakdown
        shares_chart = await self._build_shares_chart(organization_id, user_id)
        if shares_chart:
            charts.append(shares_chart)

        return charts

    async def _build_views_chart(
        self,
        time_range: PerformanceTimeRange,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> Optional[DashboardChart]:
        """Build views over time line chart."""
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            start_date, end_date = self._get_date_range(time_range)

            query = supabase.table("performance_snapshots").select(
                "snapshot_date, views, unique_views"
            ).gte("snapshot_date", start_date.date().isoformat()).order("snapshot_date")

            if organization_id:
                query = query.eq("organization_id", organization_id)

            result = query.execute()

            if not result.data:
                return None

            # Aggregate by date
            daily_data: Dict[str, Dict[str, int]] = {}
            for row in result.data:
                date = row["snapshot_date"]
                if date not in daily_data:
                    daily_data[date] = {"views": 0, "unique_views": 0}
                daily_data[date]["views"] += row.get("views", 0)
                daily_data[date]["unique_views"] += row.get("unique_views", 0)

            sorted_dates = sorted(daily_data.keys())

            return DashboardChart(
                chart_type="line",
                title="Views Over Time",
                labels=sorted_dates,
                datasets=[
                    {
                        "label": "Total Views",
                        "data": [daily_data[d]["views"] for d in sorted_dates],
                        "borderColor": "#3b82f6",
                        "fill": False,
                    },
                    {
                        "label": "Unique Views",
                        "data": [daily_data[d]["unique_views"] for d in sorted_dates],
                        "borderColor": "#10b981",
                        "fill": False,
                    },
                ],
                options={
                    "responsive": True,
                    "maintainAspectRatio": False,
                },
            )

        except Exception as e:
            logger.error(f"Failed to build views chart: {e}")
            return None

    async def _build_content_type_chart(
        self,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> Optional[DashboardChart]:
        """Build content type pie chart."""
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            query = supabase.table("content_performance").select("content_type, views")

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data:
                return None

            # Aggregate by content type
            type_views: Dict[str, int] = {}
            for row in result.data:
                content_type = row.get("content_type", "other")
                type_views[content_type] = type_views.get(content_type, 0) + row.get("views", 0)

            labels = list(type_views.keys())
            values = list(type_views.values())

            colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

            return DashboardChart(
                chart_type="pie",
                title="Views by Content Type",
                labels=labels,
                datasets=[
                    {
                        "data": values,
                        "backgroundColor": colors[: len(labels)],
                    }
                ],
            )

        except Exception as e:
            logger.error(f"Failed to build content type chart: {e}")
            return None

    async def _build_shares_chart(
        self,
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> Optional[DashboardChart]:
        """Build shares by platform chart."""
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            query = supabase.table("content_performance").select("shares_by_platform")

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data:
                return None

            # Aggregate platform shares
            platform_shares: Dict[str, int] = {}
            for row in result.data:
                shares = row.get("shares_by_platform", {})
                for platform, count in shares.items():
                    platform_shares[platform] = platform_shares.get(platform, 0) + count

            if not platform_shares:
                return None

            labels = list(platform_shares.keys())
            values = list(platform_shares.values())

            return DashboardChart(
                chart_type="bar",
                title="Shares by Platform",
                labels=labels,
                datasets=[
                    {
                        "label": "Shares",
                        "data": values,
                        "backgroundColor": "#8b5cf6",
                    }
                ],
            )

        except Exception as e:
            logger.error(f"Failed to build shares chart: {e}")
            return None

    async def _get_top_content_list(
        self,
        organization_id: Optional[str],
        user_id: Optional[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get list of top performing content."""
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            query = supabase.table("content_performance").select(
                "content_id, title, content_type, views, shares, conversions"
            ).order("views", desc=True).limit(limit)

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            return [
                {
                    "content_id": row["content_id"],
                    "title": row.get("title", "Untitled"),
                    "content_type": row.get("content_type", "blog"),
                    "views": self._format_number(row.get("views", 0)),
                    "shares": self._format_number(row.get("shares", 0)),
                    "conversions": self._format_number(row.get("conversions", 0)),
                }
                for row in (result.data or [])
            ]

        except Exception as e:
            logger.error(f"Failed to get top content: {e}")
            return []

    async def _get_recent_activity(
        self,
        organization_id: Optional[str],
        user_id: Optional[str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent activity feed."""
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            query = supabase.table("performance_events").select(
                "content_id, event_type, value, platform, timestamp"
            ).order("timestamp", desc=True).limit(limit)

            if organization_id:
                query = query.eq("organization_id", organization_id)

            result = query.execute()

            return [
                {
                    "content_id": row["content_id"],
                    "event_type": row["event_type"],
                    "description": self._format_event_description(row),
                    "timestamp": row["timestamp"],
                    "time_ago": self._format_time_ago(row["timestamp"]),
                }
                for row in (result.data or [])
            ]

        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []

    # =========================================================================
    # Export Functions
    # =========================================================================

    async def export_performance_data(
        self,
        format: Literal["csv", "json"] = "csv",
        time_range: PerformanceTimeRange = PerformanceTimeRange.MONTH,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Export performance data.

        Args:
            format: Export format (csv or json).
            time_range: Time range to export.
            organization_id: Optional organization filter.

        Returns:
            Exported data as string.
        """
        supabase = self._get_supabase()
        if not supabase:
            return "" if format == "csv" else "[]"

        try:
            start_date, _ = self._get_date_range(time_range)

            query = supabase.table("content_performance").select("*").gte(
                "last_tracked_at", start_date.isoformat()
            )

            if organization_id:
                query = query.eq("organization_id", organization_id)

            result = query.execute()

            if format == "json":
                return json.dumps(result.data or [], indent=2, default=str)

            # CSV export
            if not result.data:
                return ""

            output = io.StringIO()
            fieldnames = [
                "content_id", "title", "content_type", "views", "unique_views",
                "shares", "conversions", "bounce_rate", "time_on_page_seconds",
                "published_at", "last_tracked_at",
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for row in result.data:
                writer.writerow(row)

            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return "" if format == "csv" else "[]"

    async def export_seo_data(
        self,
        format: Literal["csv", "json"] = "csv",
        organization_id: Optional[str] = None,
        days: int = 30,
    ) -> str:
        """
        Export SEO ranking data.

        Args:
            format: Export format.
            organization_id: Optional organization filter.
            days: Days of data to export.

        Returns:
            Exported data as string.
        """
        supabase = self._get_supabase()
        if not supabase:
            return "" if format == "csv" else "[]"

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = supabase.table("seo_rankings").select("*").gte(
                "tracked_at", start_date.isoformat()
            ).order("tracked_at", desc=True)

            if organization_id:
                query = query.eq("organization_id", organization_id)

            result = query.execute()

            if format == "json":
                return json.dumps(result.data or [], indent=2, default=str)

            # CSV export
            if not result.data:
                return ""

            output = io.StringIO()
            fieldnames = [
                "keyword", "position", "previous_position", "change",
                "search_volume", "url", "tracked_at",
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for row in result.data:
                writer.writerow(row)

            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to export SEO data: {e}")
            return "" if format == "csv" else "[]"

    # =========================================================================
    # Utility Methods
    # =========================================================================

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
        else:
            start = datetime(2020, 1, 1)

        return start, now

    def _get_comparison_label(self, time_range: PerformanceTimeRange) -> str:
        """Get comparison period label."""
        labels = {
            PerformanceTimeRange.HOUR: "vs previous hour",
            PerformanceTimeRange.DAY: "vs yesterday",
            PerformanceTimeRange.WEEK: "vs last week",
            PerformanceTimeRange.MONTH: "vs last month",
            PerformanceTimeRange.QUARTER: "vs last quarter",
            PerformanceTimeRange.YEAR: "vs last year",
            PerformanceTimeRange.ALL_TIME: "all time",
        }
        return labels.get(time_range, "vs previous period")

    def _safe_average(self, values: List[float]) -> float:
        """Calculate average safely."""
        filtered = [v for v in values if v is not None and v > 0]
        return sum(filtered) / len(filtered) if filtered else 0.0

    def _format_number(self, value: float) -> str:
        """Format number for display."""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(int(value))

    def _format_percent(self, value: float) -> str:
        """Format percentage for display."""
        return f"{value:.1f}%"

    def _format_duration(self, seconds: float) -> str:
        """Format duration for display."""
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def _format_event_description(self, event: Dict[str, Any]) -> str:
        """Format event for activity feed."""
        event_type = event.get("event_type", "")
        platform = event.get("platform", "")

        descriptions = {
            "view": "Page viewed",
            "unique_view": "New visitor",
            "share": f"Shared on {platform}" if platform else "Content shared",
            "conversion": "Conversion recorded",
            "click": "Link clicked",
            "comment": "New comment",
        }

        return descriptions.get(event_type, f"Event: {event_type}")

    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as relative time."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            delta = datetime.utcnow() - dt.replace(tzinfo=None)

            if delta.days > 0:
                return f"{delta.days}d ago"
            elif delta.seconds >= 3600:
                return f"{delta.seconds // 3600}h ago"
            elif delta.seconds >= 60:
                return f"{delta.seconds // 60}m ago"
            else:
                return "just now"
        except (ValueError, AttributeError):
            return ""
