"""
Social media campaign management service.

Provides:
- Multi-platform campaign creation
- Campaign scheduling with platform offsets
- Campaign analytics aggregation
- Campaign lifecycle management
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.types.social import (
    CampaignAnalytics,
    CampaignPlatformConfig,
    CampaignStatus,
    PostAnalytics,
    PostContent,
    PostStatus,
    RecurrenceType,
    ScheduledPost,
    SocialCampaign,
    SocialPlatform,
)

from .publisher import publisher_service
from .scheduler import scheduler_service

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Service for managing multi-platform social media campaigns.

    A campaign coordinates posting the same (or similar) content across
    multiple social platforms with configurable timing offsets.
    """

    def __init__(self) -> None:
        """Initialize the campaign service."""
        self._enabled = os.environ.get("SOCIAL_SCHEDULER_ENABLED", "true").lower() == "true"

        # In-memory storage for development
        # In production, use database (Supabase)
        self._campaigns: Dict[str, SocialCampaign] = {}

        if self._enabled:
            logger.info("Social campaign service initialized")
        else:
            logger.warning("Social campaign service is disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if the campaign service is enabled."""
        return self._enabled

    def _ensure_enabled(self) -> None:
        """Raise an error if service is disabled."""
        if not self._enabled:
            raise ValueError("Social campaign service is disabled")

    # -------------------------------------------------------------------------
    # Campaign Creation
    # -------------------------------------------------------------------------

    async def create_campaign(
        self,
        user_id: str,
        name: str,
        content: PostContent,
        platforms: List[CampaignPlatformConfig],
        scheduled_at: datetime,
        description: Optional[str] = None,
        recurrence: RecurrenceType = RecurrenceType.NONE,
        recurrence_end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        source_content_id: Optional[str] = None,
    ) -> Tuple[SocialCampaign, List[ScheduledPost]]:
        """
        Create a new multi-platform campaign.

        Args:
            user_id: The user creating the campaign
            name: Campaign name
            content: Base content for all platforms
            platforms: Platform configurations with offsets
            scheduled_at: Base scheduled time
            description: Optional campaign description
            recurrence: Recurrence pattern
            recurrence_end_date: When to stop recurring
            tags: Optional tags for organization
            source_content_id: Optional reference to generated content

        Returns:
            Tuple of (campaign, scheduled_posts)
        """
        self._ensure_enabled()

        # Validate inputs
        if not platforms:
            raise ValueError("At least one platform must be configured")

        if scheduled_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        # Verify all accounts exist and belong to user
        for platform_config in platforms:
            account = await scheduler_service.get_account(platform_config.account_id)
            if not account:
                raise ValueError(f"Account {platform_config.account_id} not found")
            if account.user_id != user_id:
                raise ValueError(f"Account {platform_config.account_id} does not belong to user")

        # Create the campaign
        campaign_id = str(uuid.uuid4())

        campaign = SocialCampaign(
            id=campaign_id,
            user_id=user_id,
            name=name,
            description=description,
            content=content,
            platforms=platforms,
            scheduled_at=scheduled_at,
            status=CampaignStatus.DRAFT,
            recurrence=recurrence,
            recurrence_end_date=recurrence_end_date,
            tags=tags or [],
            source_content_id=source_content_id,
            post_ids=[],
        )

        # Create scheduled posts for each platform
        scheduled_posts = await self._create_campaign_posts(campaign)
        campaign.post_ids = [p.id for p in scheduled_posts]

        # Activate the campaign
        campaign.status = CampaignStatus.ACTIVE

        # Store the campaign
        await self._store_campaign(campaign)

        logger.info(
            f"Created campaign {campaign_id} with {len(scheduled_posts)} scheduled posts"
        )

        return campaign, scheduled_posts

    async def _create_campaign_posts(
        self,
        campaign: SocialCampaign,
    ) -> List[ScheduledPost]:
        """Create scheduled posts for a campaign."""
        posts = []

        for platform_config in campaign.platforms:
            if not platform_config.enabled:
                continue

            # Calculate post time with offset
            post_time = campaign.scheduled_at + timedelta(
                minutes=platform_config.post_offset_minutes
            )

            # Use custom content if provided, otherwise use campaign content
            content = platform_config.custom_content or campaign.content

            # Adapt content for platform
            adapted_content = await self._adapt_content_for_platform(
                content,
                platform_config.platform,
            )

            # Schedule the post
            post = await scheduler_service.schedule_post(
                user_id=campaign.user_id,
                account_id=platform_config.account_id,
                content=adapted_content,
                scheduled_at=post_time,
                recurrence=campaign.recurrence,
                recurrence_end_date=campaign.recurrence_end_date,
                campaign_id=campaign.id,
                source_content_id=campaign.source_content_id,
            )

            posts.append(post)

            # Handle recurring posts
            if campaign.recurrence != RecurrenceType.NONE:
                recurring_posts = await scheduler_service.create_recurring_posts(
                    post,
                    count=10,  # Limit recurring posts
                )
                # First post is already added, add the rest
                posts.extend(recurring_posts[1:])

        return posts

    async def _adapt_content_for_platform(
        self,
        content: PostContent,
        platform: SocialPlatform,
    ) -> PostContent:
        """
        Adapt content to fit platform requirements.

        This includes:
        - Truncating text to platform limits
        - Adjusting hashtags
        - Formatting links
        """
        from src.types.social import PLATFORM_CONFIGS

        config = PLATFORM_CONFIGS.get(platform)
        if not config:
            return content

        # Truncate text if needed
        text = content.text
        if len(text) > config.max_text_length:
            # Leave room for truncation indicator
            max_len = config.max_text_length - 3
            text = text[:max_len] + "..."

        # Limit media count
        media = content.media[:config.max_media_count]

        # Create adapted content
        return PostContent(
            text=text,
            media=media,
            link_url=content.link_url,
            link_title=content.link_title,
            link_description=content.link_description,
            hashtags=content.hashtags,
            mentions=content.mentions,
        )

    # -------------------------------------------------------------------------
    # Campaign Management
    # -------------------------------------------------------------------------

    async def get_campaign(
        self,
        campaign_id: str,
    ) -> Optional[SocialCampaign]:
        """Get a campaign by ID."""
        return self._campaigns.get(campaign_id)

    async def list_campaigns(
        self,
        user_id: str,
        status: Optional[CampaignStatus] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SocialCampaign], int]:
        """
        List campaigns with filters.

        Args:
            user_id: The user to list campaigns for
            status: Filter by status
            tag: Filter by tag
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (campaigns, total_count)
        """
        self._ensure_enabled()

        campaigns = [
            c for c in self._campaigns.values()
            if c.user_id == user_id
        ]

        if status:
            campaigns = [c for c in campaigns if c.status == status]

        if tag:
            campaigns = [c for c in campaigns if tag in c.tags]

        # Sort by scheduled time (newest first)
        campaigns.sort(key=lambda c: c.scheduled_at, reverse=True)

        # Paginate
        total = len(campaigns)
        start = (page - 1) * page_size
        end = start + page_size
        campaigns = campaigns[start:end]

        return campaigns, total

    async def pause_campaign(
        self,
        campaign_id: str,
        user_id: str,
    ) -> SocialCampaign:
        """
        Pause an active campaign.

        Pauses all scheduled posts that haven't been published yet.
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot pause campaign with status {campaign.status.value}")

        # Pause the campaign
        campaign.status = CampaignStatus.PAUSED
        campaign.updated_at = datetime.utcnow()

        # Cancel scheduled posts that haven't been published
        for post_id in campaign.post_ids:
            post = await scheduler_service.get_scheduled_post(post_id)
            if post and post.status == PostStatus.SCHEDULED:
                await scheduler_service.cancel_scheduled_post(post_id, user_id)

        await self._store_campaign(campaign)

        logger.info(f"Paused campaign {campaign_id}")

        return campaign

    async def resume_campaign(
        self,
        campaign_id: str,
        user_id: str,
    ) -> SocialCampaign:
        """
        Resume a paused campaign.

        Reschedules cancelled posts with updated times.
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        if campaign.status != CampaignStatus.PAUSED:
            raise ValueError(f"Cannot resume campaign with status {campaign.status.value}")

        # Recalculate schedule from now
        campaign.scheduled_at = datetime.utcnow() + timedelta(minutes=5)
        campaign.status = CampaignStatus.ACTIVE
        campaign.updated_at = datetime.utcnow()

        # Create new scheduled posts
        new_posts = await self._create_campaign_posts(campaign)
        campaign.post_ids = [p.id for p in new_posts]

        await self._store_campaign(campaign)

        logger.info(f"Resumed campaign {campaign_id}")

        return campaign

    async def cancel_campaign(
        self,
        campaign_id: str,
        user_id: str,
    ) -> SocialCampaign:
        """
        Cancel a campaign entirely.

        Cancels all scheduled posts and marks campaign as cancelled.
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        if campaign.status in (CampaignStatus.COMPLETED, CampaignStatus.CANCELLED):
            raise ValueError(f"Campaign already {campaign.status.value}")

        # Cancel all scheduled posts
        for post_id in campaign.post_ids:
            try:
                await scheduler_service.cancel_scheduled_post(post_id, user_id)
            except Exception as e:
                logger.warning(f"Failed to cancel post {post_id}: {e}")

        campaign.status = CampaignStatus.CANCELLED
        campaign.updated_at = datetime.utcnow()

        await self._store_campaign(campaign)

        logger.info(f"Cancelled campaign {campaign_id}")

        return campaign

    async def complete_campaign(
        self,
        campaign_id: str,
    ) -> SocialCampaign:
        """
        Mark a campaign as completed.

        Called automatically when all posts have been published.
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()

        await self._store_campaign(campaign)

        logger.info(f"Completed campaign {campaign_id}")

        return campaign

    async def check_campaign_completion(
        self,
        campaign_id: str,
    ) -> bool:
        """
        Check if all posts in a campaign are published.

        Returns True if campaign should be marked complete.
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return False

        if campaign.status != CampaignStatus.ACTIVE:
            return False

        # Check all posts
        for post_id in campaign.post_ids:
            post = await scheduler_service.get_scheduled_post(post_id)
            if post and post.status not in (PostStatus.PUBLISHED, PostStatus.FAILED, PostStatus.CANCELLED):
                return False

        return True

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    async def get_campaign_analytics(
        self,
        campaign_id: str,
        user_id: str,
    ) -> CampaignAnalytics:
        """
        Get aggregated analytics for a campaign.

        Args:
            campaign_id: The campaign to get analytics for
            user_id: The user requesting analytics

        Returns:
            CampaignAnalytics with aggregated metrics
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        # Initialize analytics
        analytics = CampaignAnalytics(
            campaign_id=campaign_id,
        )

        # Collect analytics from all posts
        platform_analytics: Dict[str, PostAnalytics] = {}
        total_engagement_rate = 0.0
        posts_with_analytics = 0

        for post_id in campaign.post_ids:
            post = await scheduler_service.get_scheduled_post(post_id)
            if not post:
                continue

            analytics.total_posts += 1

            if post.status == PostStatus.PUBLISHED:
                analytics.published_posts += 1

                # Get post analytics
                account = await scheduler_service.get_account(post.account_id)
                if account and post.platform_post_id:
                    try:
                        post_analytics = await publisher_service.get_post_analytics(
                            post, account
                        )
                        if post_analytics:
                            analytics.total_impressions += post_analytics.impressions
                            analytics.total_reach += post_analytics.reach
                            analytics.total_engagements += post_analytics.engagements
                            analytics.total_clicks += post_analytics.clicks

                            total_engagement_rate += post_analytics.engagement_rate
                            posts_with_analytics += 1

                            # Store by platform
                            platform_key = post.platform.value
                            if platform_key not in platform_analytics:
                                platform_analytics[platform_key] = post_analytics
                            else:
                                # Aggregate platform analytics
                                existing = platform_analytics[platform_key]
                                existing.impressions += post_analytics.impressions
                                existing.engagements += post_analytics.engagements
                                existing.clicks += post_analytics.clicks

                            # Track best performing
                            if (
                                not analytics.best_performing_post_id
                                or post_analytics.engagements > platform_analytics.get(
                                    analytics.best_performing_post_id, PostAnalytics(id="", post_id="", platform=post.platform, platform_post_id="")
                                ).engagements
                            ):
                                analytics.best_performing_post_id = post_id

                    except Exception as e:
                        logger.warning(f"Failed to get analytics for post {post_id}: {e}")

            elif post.status == PostStatus.FAILED:
                analytics.failed_posts += 1

        # Calculate average engagement rate
        if posts_with_analytics > 0:
            analytics.average_engagement_rate = total_engagement_rate / posts_with_analytics

        analytics.platform_breakdown = platform_analytics

        return analytics

    async def get_campaign_posts(
        self,
        campaign_id: str,
        user_id: str,
    ) -> List[ScheduledPost]:
        """
        Get all posts for a campaign.

        Args:
            campaign_id: The campaign to get posts for
            user_id: The user requesting posts

        Returns:
            List of scheduled posts
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        posts = []
        for post_id in campaign.post_ids:
            post = await scheduler_service.get_scheduled_post(post_id)
            if post:
                posts.append(post)

        return posts

    # -------------------------------------------------------------------------
    # Duplicate Campaign
    # -------------------------------------------------------------------------

    async def duplicate_campaign(
        self,
        campaign_id: str,
        user_id: str,
        new_name: Optional[str] = None,
        new_scheduled_at: Optional[datetime] = None,
    ) -> Tuple[SocialCampaign, List[ScheduledPost]]:
        """
        Duplicate an existing campaign.

        Args:
            campaign_id: The campaign to duplicate
            user_id: The user duplicating the campaign
            new_name: Optional new name (default: original + " (Copy)")
            new_scheduled_at: Optional new scheduled time

        Returns:
            Tuple of (new_campaign, scheduled_posts)
        """
        self._ensure_enabled()

        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.user_id != user_id:
            raise ValueError("Campaign does not belong to user")

        # Create duplicate
        return await self.create_campaign(
            user_id=user_id,
            name=new_name or f"{campaign.name} (Copy)",
            content=campaign.content,
            platforms=campaign.platforms,
            scheduled_at=new_scheduled_at or (datetime.utcnow() + timedelta(days=1)),
            description=campaign.description,
            recurrence=campaign.recurrence,
            recurrence_end_date=campaign.recurrence_end_date,
            tags=campaign.tags,
            source_content_id=campaign.source_content_id,
        )

    # -------------------------------------------------------------------------
    # Internal Storage
    # -------------------------------------------------------------------------

    async def _store_campaign(
        self,
        campaign: SocialCampaign,
    ) -> None:
        """Store a campaign."""
        # In production, save to database
        self._campaigns[campaign.id] = campaign


# Global service instance
campaign_service = CampaignService()
