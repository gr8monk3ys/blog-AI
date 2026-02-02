"""
Type definitions for content performance analytics.

This module provides data models for tracking and analyzing content performance
across multiple dimensions including engagement, SEO rankings, and AI-driven
recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


# =============================================================================
# Enums
# =============================================================================


class PerformanceTimeRange(str, Enum):
    """Time range options for performance queries."""

    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"
    ALL_TIME = "all"


class MetricType(str, Enum):
    """Types of performance metrics."""

    VIEW = "view"
    UNIQUE_VIEW = "unique_view"
    TIME_ON_PAGE = "time_on_page"
    SCROLL_DEPTH = "scroll_depth"
    BOUNCE = "bounce"
    SHARE = "share"
    CLICK = "click"
    CONVERSION = "conversion"
    COMMENT = "comment"
    BACKLINK = "backlink"


class ContentFormat(str, Enum):
    """Content format types for recommendations."""

    BLOG = "blog"
    SOCIAL = "social"
    EMAIL = "email"
    VIDEO = "video"
    PODCAST = "podcast"
    INFOGRAPHIC = "infographic"


class TrendDirection(str, Enum):
    """Direction of a performance trend."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class RecommendationType(str, Enum):
    """Types of content recommendations."""

    TOPIC = "topic"
    KEYWORD = "keyword"
    FORMAT = "format"
    TIMING = "timing"
    OPTIMIZATION = "optimization"


# =============================================================================
# Core Performance Models
# =============================================================================


@dataclass
class PerformanceMetric:
    """A single performance metric data point."""

    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ContentPerformance:
    """Performance metrics for a piece of content."""

    content_id: str
    content_type: str
    title: str

    # Core engagement metrics
    views: int = 0
    unique_views: int = 0
    time_on_page_seconds: float = 0.0
    avg_scroll_depth: float = 0.0
    bounce_rate: float = 0.0

    # Social metrics
    shares: int = 0
    shares_by_platform: Dict[str, int] = field(default_factory=dict)
    comments: int = 0
    reactions: int = 0

    # SEO metrics
    backlinks: int = 0
    referring_domains: int = 0
    organic_traffic: int = 0

    # Conversion metrics
    conversions: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0

    # Metadata
    published_at: Optional[datetime] = None
    first_tracked_at: Optional[datetime] = None
    last_tracked_at: Optional[datetime] = None
    url: Optional[str] = None
    platform: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type,
            "title": self.title,
            "views": self.views,
            "unique_views": self.unique_views,
            "time_on_page_seconds": self.time_on_page_seconds,
            "avg_scroll_depth": self.avg_scroll_depth,
            "bounce_rate": self.bounce_rate,
            "shares": self.shares,
            "shares_by_platform": self.shares_by_platform,
            "comments": self.comments,
            "reactions": self.reactions,
            "backlinks": self.backlinks,
            "referring_domains": self.referring_domains,
            "organic_traffic": self.organic_traffic,
            "conversions": self.conversions,
            "conversion_rate": self.conversion_rate,
            "revenue": self.revenue,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "first_tracked_at": self.first_tracked_at.isoformat() if self.first_tracked_at else None,
            "last_tracked_at": self.last_tracked_at.isoformat() if self.last_tracked_at else None,
            "url": self.url,
            "platform": self.platform,
        }

    @property
    def engagement_score(self) -> float:
        """Calculate an overall engagement score (0-100)."""
        if self.views == 0:
            return 0.0

        # Weighted scoring based on engagement actions
        time_score = min(self.time_on_page_seconds / 180, 1) * 25  # 3 min = max
        scroll_score = self.avg_scroll_depth * 25
        bounce_score = (1 - self.bounce_rate) * 20
        share_score = min(self.shares / max(self.views * 0.01, 1), 1) * 15
        conversion_score = min(self.conversion_rate * 10, 1) * 15

        return round(time_score + scroll_score + bounce_score + share_score + conversion_score, 2)


@dataclass
class PerformanceSnapshot:
    """A snapshot of performance metrics at a point in time."""

    content_id: str
    snapshot_date: datetime
    views: int = 0
    unique_views: int = 0
    shares: int = 0
    backlinks: int = 0
    conversions: int = 0
    engagement_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_id": self.content_id,
            "snapshot_date": self.snapshot_date.isoformat(),
            "views": self.views,
            "unique_views": self.unique_views,
            "shares": self.shares,
            "backlinks": self.backlinks,
            "conversions": self.conversions,
            "engagement_score": self.engagement_score,
        }


# =============================================================================
# Trend and Summary Models
# =============================================================================


@dataclass
class PerformanceTrend:
    """Trend analysis for a performance metric."""

    metric_name: str
    current_value: float
    previous_value: float
    change_absolute: float
    change_percent: float
    direction: TrendDirection
    time_range: PerformanceTimeRange
    data_points: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_absolute": self.change_absolute,
            "change_percent": self.change_percent,
            "direction": self.direction.value,
            "time_range": self.time_range.value,
            "data_points": self.data_points,
        }

    @classmethod
    def calculate(
        cls,
        metric_name: str,
        current: float,
        previous: float,
        time_range: PerformanceTimeRange,
        data_points: Optional[List[Dict[str, Any]]] = None,
    ) -> "PerformanceTrend":
        """Calculate a trend from current and previous values."""
        change_absolute = current - previous
        change_percent = (
            (change_absolute / previous * 100) if previous != 0 else (100.0 if current > 0 else 0.0)
        )

        if change_percent > 5:
            direction = TrendDirection.UP
        elif change_percent < -5:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return cls(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            change_absolute=change_absolute,
            change_percent=round(change_percent, 2),
            direction=direction,
            time_range=time_range,
            data_points=data_points or [],
        )


@dataclass
class PerformanceSummary:
    """Summary of performance metrics across multiple content items."""

    time_range: PerformanceTimeRange
    total_content_items: int
    total_views: int
    total_unique_views: int
    total_shares: int
    total_conversions: int
    avg_time_on_page: float
    avg_bounce_rate: float
    avg_engagement_score: float
    top_performing_content: List[str] = field(default_factory=list)
    trends: Dict[str, PerformanceTrend] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "time_range": self.time_range.value,
            "total_content_items": self.total_content_items,
            "total_views": self.total_views,
            "total_unique_views": self.total_unique_views,
            "total_shares": self.total_shares,
            "total_conversions": self.total_conversions,
            "avg_time_on_page": self.avg_time_on_page,
            "avg_bounce_rate": self.avg_bounce_rate,
            "avg_engagement_score": self.avg_engagement_score,
            "top_performing_content": self.top_performing_content,
            "trends": {k: v.to_dict() for k, v in self.trends.items()},
            "generated_at": self.generated_at.isoformat(),
        }


# =============================================================================
# SEO Models
# =============================================================================


@dataclass
class SEORanking:
    """SEO ranking for a keyword."""

    keyword: str
    position: int
    previous_position: Optional[int] = None
    change: int = 0
    search_volume: Optional[int] = None
    difficulty: Optional[float] = None
    url: Optional[str] = None
    content_id: Optional[str] = None
    tracked_at: datetime = field(default_factory=datetime.utcnow)
    search_engine: str = "google"
    location: str = "us"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "keyword": self.keyword,
            "position": self.position,
            "previous_position": self.previous_position,
            "change": self.change,
            "search_volume": self.search_volume,
            "difficulty": self.difficulty,
            "url": self.url,
            "content_id": self.content_id,
            "tracked_at": self.tracked_at.isoformat(),
            "search_engine": self.search_engine,
            "location": self.location,
        }

    @property
    def trend_direction(self) -> TrendDirection:
        """Get the trend direction based on position change."""
        if self.change > 0:
            return TrendDirection.UP  # Improved ranking (lower position number)
        elif self.change < 0:
            return TrendDirection.DOWN
        return TrendDirection.STABLE


@dataclass
class SEOAnalysis:
    """Comprehensive SEO analysis for content."""

    content_id: str
    url: str
    rankings: List[SEORanking] = field(default_factory=list)
    avg_position: Optional[float] = None
    top_keywords: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    competitors: List[Dict[str, Any]] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_id": self.content_id,
            "url": self.url,
            "rankings": [r.to_dict() for r in self.rankings],
            "avg_position": self.avg_position,
            "top_keywords": self.top_keywords,
            "opportunities": self.opportunities,
            "competitors": self.competitors,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


# =============================================================================
# Recommendation Models
# =============================================================================


@dataclass
class ContentRecommendation:
    """AI-generated content recommendation."""

    recommendation_type: RecommendationType
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1 = highest priority
    data: Dict[str, Any] = field(default_factory=dict)
    based_on: List[str] = field(default_factory=list)  # Content IDs this is based on
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_type": self.recommendation_type.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "priority": self.priority,
            "data": self.data,
            "based_on": self.based_on,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class TopicRecommendation(ContentRecommendation):
    """Recommendation for a content topic."""

    topic: str = ""
    related_keywords: List[str] = field(default_factory=list)
    estimated_traffic: Optional[int] = None
    competition_level: Optional[str] = None  # low, medium, high

    def __post_init__(self):
        """Set recommendation type after initialization."""
        self.recommendation_type = RecommendationType.TOPIC

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        base = super().to_dict()
        base.update({
            "topic": self.topic,
            "related_keywords": self.related_keywords,
            "estimated_traffic": self.estimated_traffic,
            "competition_level": self.competition_level,
        })
        return base


@dataclass
class TimingRecommendation(ContentRecommendation):
    """Recommendation for optimal posting time."""

    day_of_week: str = ""  # monday, tuesday, etc.
    hour_utc: int = 0
    timezone: str = "UTC"
    expected_engagement_boost: float = 0.0

    def __post_init__(self):
        """Set recommendation type after initialization."""
        self.recommendation_type = RecommendationType.TIMING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        base = super().to_dict()
        base.update({
            "day_of_week": self.day_of_week,
            "hour_utc": self.hour_utc,
            "timezone": self.timezone,
            "expected_engagement_boost": self.expected_engagement_boost,
        })
        return base


@dataclass
class FormatRecommendation(ContentRecommendation):
    """Recommendation for content format."""

    recommended_format: ContentFormat = ContentFormat.BLOG
    current_format: Optional[ContentFormat] = None
    transformation_suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set recommendation type after initialization."""
        self.recommendation_type = RecommendationType.FORMAT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        base = super().to_dict()
        base.update({
            "recommended_format": self.recommended_format.value,
            "current_format": self.current_format.value if self.current_format else None,
            "transformation_suggestions": self.transformation_suggestions,
        })
        return base


# =============================================================================
# Event Models
# =============================================================================


@dataclass
class PerformanceEvent:
    """A performance tracking event."""

    event_type: MetricType
    content_id: str
    value: float = 1.0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Source information
    source: Optional[str] = None  # tracking_pixel, webhook, api, etc.
    platform: Optional[str] = None  # wordpress, medium, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "content_id": self.content_id,
            "value": self.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "source": self.source,
            "platform": self.platform,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "referrer": self.referrer,
        }


# =============================================================================
# Tracking Configuration
# =============================================================================


@dataclass
class TrackingConfig:
    """Configuration for content tracking."""

    content_id: str
    enabled: bool = True
    track_views: bool = True
    track_time_on_page: bool = True
    track_scroll_depth: bool = True
    track_shares: bool = True
    track_conversions: bool = True
    conversion_goals: List[Dict[str, Any]] = field(default_factory=list)
    custom_dimensions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_id": self.content_id,
            "enabled": self.enabled,
            "track_views": self.track_views,
            "track_time_on_page": self.track_time_on_page,
            "track_scroll_depth": self.track_scroll_depth,
            "track_shares": self.track_shares,
            "track_conversions": self.track_conversions,
            "conversion_goals": self.conversion_goals,
            "custom_dimensions": self.custom_dimensions,
        }
