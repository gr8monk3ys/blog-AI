"""
Type definitions for social media scheduling and publishing.

Provides models for:
- Social platform configurations and accounts
- Scheduled posts and campaigns
- Post analytics and performance metrics
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator


class SocialPlatform(str, Enum):
    """Supported social media platforms."""

    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    """Status of a scheduled post."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecurrenceType(str, Enum):
    """Types of recurring schedules."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class CampaignStatus(str, Enum):
    """Status of a social media campaign."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# -----------------------------------------------------------------------------
# OAuth and Account Models
# -----------------------------------------------------------------------------


class OAuthState(BaseModel):
    """State for OAuth flow tracking."""

    user_id: str
    platform: SocialPlatform
    redirect_uri: str
    state_token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class OAuthTokens(BaseModel):
    """OAuth tokens for a connected account."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None


class SocialAccount(BaseModel):
    """A connected social media account."""

    id: str
    user_id: str
    platform: SocialPlatform
    platform_user_id: str
    platform_username: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SocialConnection(BaseModel):
    """Response model for a social media connection."""

    id: str
    platform: SocialPlatform
    platform_username: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: bool = True
    connected_at: datetime


# -----------------------------------------------------------------------------
# Post Models
# -----------------------------------------------------------------------------


class MediaAttachment(BaseModel):
    """Media attachment for a social post."""

    id: Optional[str] = None
    type: Literal["image", "video", "gif"] = "image"
    url: str
    alt_text: Optional[str] = None
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[float] = None  # For video


class PostContent(BaseModel):
    """Content for a social media post."""

    text: str = Field(..., min_length=1, max_length=10000)
    media: List[MediaAttachment] = Field(default_factory=list)
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    link_description: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)

    @validator("text")
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Post text cannot be empty or whitespace only")
        return v


class PlatformPostContent(BaseModel):
    """Platform-specific post content with character limits."""

    platform: SocialPlatform
    text: str
    media: List[MediaAttachment] = Field(default_factory=list)
    thread_posts: List[str] = Field(default_factory=list)  # For Twitter threads

    @validator("text")
    def validate_platform_limits(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate text against platform character limits."""
        platform = values.get("platform")
        limits = {
            SocialPlatform.TWITTER: 280,
            SocialPlatform.LINKEDIN: 3000,
            SocialPlatform.FACEBOOK: 63206,
            SocialPlatform.INSTAGRAM: 2200,
        }
        if platform and len(v) > limits.get(platform, 10000):
            raise ValueError(
                f"Text exceeds {platform.value} character limit of {limits[platform]}"
            )
        return v


class ScheduledPost(BaseModel):
    """A post scheduled for future publishing."""

    id: str
    user_id: str
    account_id: str
    platform: SocialPlatform
    content: PostContent
    platform_content: Optional[PlatformPostContent] = None
    scheduled_at: datetime
    published_at: Optional[datetime] = None
    status: PostStatus = PostStatus.SCHEDULED
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    campaign_id: Optional[str] = None
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    source_content_id: Optional[str] = None  # Reference to blog/content that generated this
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# -----------------------------------------------------------------------------
# Campaign Models
# -----------------------------------------------------------------------------


class CampaignPlatformConfig(BaseModel):
    """Configuration for a platform within a campaign."""

    platform: SocialPlatform
    account_id: str
    enabled: bool = True
    post_offset_minutes: int = 0  # Stagger posts across platforms
    custom_content: Optional[PostContent] = None  # Override campaign content


class SocialCampaign(BaseModel):
    """A multi-platform social media campaign."""

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    content: PostContent
    platforms: List[CampaignPlatformConfig]
    scheduled_at: datetime
    status: CampaignStatus = CampaignStatus.DRAFT
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    post_ids: List[str] = Field(default_factory=list)  # Generated scheduled posts
    tags: List[str] = Field(default_factory=list)
    source_content_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# -----------------------------------------------------------------------------
# Analytics Models
# -----------------------------------------------------------------------------


class PostAnalytics(BaseModel):
    """Analytics for a published post."""

    id: str
    post_id: str
    platform: SocialPlatform
    platform_post_id: str
    impressions: int = 0
    reach: int = 0
    engagements: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    retweets: int = 0  # Twitter specific
    reposts: int = 0  # LinkedIn specific
    saves: int = 0  # Instagram specific
    clicks: int = 0
    link_clicks: int = 0
    profile_visits: int = 0
    video_views: int = 0
    video_watch_time_seconds: int = 0
    engagement_rate: float = 0.0
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class CampaignAnalytics(BaseModel):
    """Aggregated analytics for a campaign."""

    campaign_id: str
    total_posts: int = 0
    published_posts: int = 0
    failed_posts: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    total_engagements: int = 0
    total_clicks: int = 0
    average_engagement_rate: float = 0.0
    platform_breakdown: Dict[str, PostAnalytics] = Field(default_factory=dict)
    best_performing_post_id: Optional[str] = None
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Optimal Timing Models
# -----------------------------------------------------------------------------


class OptimalTimeSlot(BaseModel):
    """An optimal time slot for posting."""

    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    score: float = Field(..., ge=0.0, le=1.0)  # Confidence score
    expected_engagement_rate: float = 0.0
    timezone: str = "UTC"


class PlatformOptimalTimes(BaseModel):
    """Optimal posting times for a platform."""

    platform: SocialPlatform
    time_slots: List[OptimalTimeSlot]
    best_days: List[int]  # Days of week with highest engagement
    worst_days: List[int]  # Days of week with lowest engagement
    analysis_period_days: int = 30
    sample_size: int = 0  # Number of posts analyzed
    last_analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class OptimalTimesResponse(BaseModel):
    """Response containing optimal posting times."""

    success: bool = True
    user_id: str
    platforms: List[PlatformOptimalTimes]
    recommendations: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Request/Response Models for API
# -----------------------------------------------------------------------------


class ConnectAccountRequest(BaseModel):
    """Request to initiate OAuth connection."""

    platform: SocialPlatform
    redirect_uri: str


class ConnectAccountResponse(BaseModel):
    """Response with OAuth authorization URL."""

    success: bool = True
    authorization_url: str
    state: str


class SchedulePostRequest(BaseModel):
    """Request to schedule a new post."""

    account_id: str
    content: PostContent
    scheduled_at: datetime
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    campaign_id: Optional[str] = None
    source_content_id: Optional[str] = None

    @validator("scheduled_at")
    def validate_future_date(cls, v: datetime) -> datetime:
        """Ensure scheduled time is in the future."""
        if v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class SchedulePostResponse(BaseModel):
    """Response after scheduling a post."""

    success: bool = True
    post: ScheduledPost


class UpdateScheduledPostRequest(BaseModel):
    """Request to update a scheduled post."""

    content: Optional[PostContent] = None
    scheduled_at: Optional[datetime] = None
    recurrence: Optional[RecurrenceType] = None
    recurrence_end_date: Optional[datetime] = None

    @validator("scheduled_at")
    def validate_future_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled time is in the future."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class CreateCampaignRequest(BaseModel):
    """Request to create a new campaign."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: PostContent
    platforms: List[CampaignPlatformConfig]
    scheduled_at: datetime
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    source_content_id: Optional[str] = None

    @validator("platforms")
    def validate_platforms(cls, v: List[CampaignPlatformConfig]) -> List[CampaignPlatformConfig]:
        """Ensure at least one platform is configured."""
        if not v:
            raise ValueError("At least one platform must be configured")
        return v


class CreateCampaignResponse(BaseModel):
    """Response after creating a campaign."""

    success: bool = True
    campaign: SocialCampaign
    scheduled_posts: List[ScheduledPost]


class ListScheduledPostsResponse(BaseModel):
    """Response listing scheduled posts."""

    success: bool = True
    posts: List[ScheduledPost]
    total: int
    page: int = 1
    page_size: int = 20


class ListCampaignsResponse(BaseModel):
    """Response listing campaigns."""

    success: bool = True
    campaigns: List[SocialCampaign]
    total: int
    page: int = 1
    page_size: int = 20


class ListAccountsResponse(BaseModel):
    """Response listing connected accounts."""

    success: bool = True
    accounts: List[SocialConnection]


class DeleteResponse(BaseModel):
    """Generic delete response."""

    success: bool = True
    message: str


# -----------------------------------------------------------------------------
# Platform Configuration
# -----------------------------------------------------------------------------


@dataclass
class PlatformConfig:
    """Configuration for a social media platform."""

    platform: SocialPlatform
    name: str
    max_text_length: int
    max_media_count: int
    supported_media_types: List[str]
    requires_media: bool = False
    supports_threads: bool = False
    supports_scheduling: bool = True
    oauth_scopes: List[str] = field(default_factory=list)
    rate_limit_posts_per_day: int = 100
    rate_limit_posts_per_hour: int = 25


# Platform configurations
PLATFORM_CONFIGS: Dict[SocialPlatform, PlatformConfig] = {
    SocialPlatform.TWITTER: PlatformConfig(
        platform=SocialPlatform.TWITTER,
        name="Twitter/X",
        max_text_length=280,
        max_media_count=4,
        supported_media_types=["image", "gif", "video"],
        supports_threads=True,
        oauth_scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
        rate_limit_posts_per_day=2400,
        rate_limit_posts_per_hour=100,
    ),
    SocialPlatform.LINKEDIN: PlatformConfig(
        platform=SocialPlatform.LINKEDIN,
        name="LinkedIn",
        max_text_length=3000,
        max_media_count=9,
        supported_media_types=["image", "video"],
        oauth_scopes=["w_member_social", "r_liteprofile"],
        rate_limit_posts_per_day=100,
        rate_limit_posts_per_hour=25,
    ),
    SocialPlatform.FACEBOOK: PlatformConfig(
        platform=SocialPlatform.FACEBOOK,
        name="Facebook",
        max_text_length=63206,
        max_media_count=10,
        supported_media_types=["image", "video"],
        oauth_scopes=["pages_manage_posts", "pages_read_engagement"],
        rate_limit_posts_per_day=200,
        rate_limit_posts_per_hour=50,
    ),
    SocialPlatform.INSTAGRAM: PlatformConfig(
        platform=SocialPlatform.INSTAGRAM,
        name="Instagram",
        max_text_length=2200,
        max_media_count=10,
        supported_media_types=["image", "video"],
        requires_media=True,
        oauth_scopes=["instagram_basic", "instagram_content_publish"],
        rate_limit_posts_per_day=25,
        rate_limit_posts_per_hour=10,
    ),
}


def get_platform_config(platform: SocialPlatform) -> PlatformConfig:
    """Get configuration for a platform."""
    return PLATFORM_CONFIGS[platform]
