"""
Social media post scheduling service.

Provides:
- Post scheduling for future times
- Recurring schedules (daily, weekly, monthly)
- Optimal time suggestions based on engagement data
- Queue management
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.types.social import (
    OptimalTimeSlot,
    OptimalTimesResponse,
    PlatformOptimalTimes,
    PostContent,
    PostStatus,
    RecurrenceType,
    ScheduledPost,
    SocialAccount,
    SocialPlatform,
)

logger = logging.getLogger(__name__)


# Default optimal posting times based on industry research
# These are used as fallback when no user-specific data is available
DEFAULT_OPTIMAL_TIMES: Dict[SocialPlatform, List[Dict[str, Any]]] = {
    SocialPlatform.TWITTER: [
        {"day": 1, "hour": 9, "score": 0.9},   # Tuesday 9 AM
        {"day": 2, "hour": 12, "score": 0.85},  # Wednesday 12 PM
        {"day": 3, "hour": 9, "score": 0.85},   # Thursday 9 AM
        {"day": 1, "hour": 12, "score": 0.8},   # Tuesday 12 PM
        {"day": 4, "hour": 9, "score": 0.75},   # Friday 9 AM
    ],
    SocialPlatform.LINKEDIN: [
        {"day": 1, "hour": 10, "score": 0.95},  # Tuesday 10 AM
        {"day": 2, "hour": 10, "score": 0.9},   # Wednesday 10 AM
        {"day": 3, "hour": 10, "score": 0.85},  # Thursday 10 AM
        {"day": 1, "hour": 8, "score": 0.8},    # Tuesday 8 AM
        {"day": 2, "hour": 12, "score": 0.75},  # Wednesday 12 PM
    ],
    SocialPlatform.FACEBOOK: [
        {"day": 2, "hour": 11, "score": 0.9},   # Wednesday 11 AM
        {"day": 3, "hour": 13, "score": 0.85},  # Thursday 1 PM
        {"day": 4, "hour": 11, "score": 0.8},   # Friday 11 AM
        {"day": 1, "hour": 9, "score": 0.75},   # Tuesday 9 AM
        {"day": 0, "hour": 12, "score": 0.7},   # Monday 12 PM
    ],
    SocialPlatform.INSTAGRAM: [
        {"day": 0, "hour": 11, "score": 0.9},   # Monday 11 AM
        {"day": 1, "hour": 11, "score": 0.85},  # Tuesday 11 AM
        {"day": 2, "hour": 11, "score": 0.85},  # Wednesday 11 AM
        {"day": 4, "hour": 14, "score": 0.8},   # Friday 2 PM
        {"day": 5, "hour": 10, "score": 0.75},  # Saturday 10 AM
    ],
}


class SchedulerService:
    """
    Service for scheduling social media posts.

    Manages post scheduling, queue operations, and optimal timing suggestions.
    """

    def __init__(self) -> None:
        """Initialize the scheduler service."""
        self._enabled = os.environ.get("SOCIAL_SCHEDULER_ENABLED", "true").lower() == "true"

        # In-memory storage for development
        # In production, use database (Supabase)
        self._scheduled_posts: Dict[str, ScheduledPost] = {}
        self._accounts: Dict[str, SocialAccount] = {}

        if self._enabled:
            logger.info("Social scheduler service initialized")
        else:
            logger.warning("Social scheduler is disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if the scheduler is enabled."""
        return self._enabled

    def _ensure_enabled(self) -> None:
        """Raise an error if scheduler is disabled."""
        if not self._enabled:
            raise ValueError("Social scheduler is disabled")

    # -------------------------------------------------------------------------
    # Post Scheduling
    # -------------------------------------------------------------------------

    async def schedule_post(
        self,
        user_id: str,
        account_id: str,
        content: PostContent,
        scheduled_at: datetime,
        recurrence: RecurrenceType = RecurrenceType.NONE,
        recurrence_end_date: Optional[datetime] = None,
        campaign_id: Optional[str] = None,
        source_content_id: Optional[str] = None,
    ) -> ScheduledPost:
        """
        Schedule a post for future publishing.

        Args:
            user_id: The user scheduling the post
            account_id: The social account to post from
            content: The content to post
            scheduled_at: When to publish the post
            recurrence: Recurrence pattern (none, daily, weekly, monthly)
            recurrence_end_date: When to stop recurring posts
            campaign_id: Optional campaign this post belongs to
            source_content_id: Optional reference to generated content

        Returns:
            The scheduled post object
        """
        self._ensure_enabled()

        # Validate scheduled time is in the future
        if scheduled_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        # Get account to determine platform
        account = await self.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        if account.user_id != user_id:
            raise ValueError("Account does not belong to user")

        # Create the scheduled post
        post = ScheduledPost(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            platform=account.platform,
            content=content,
            scheduled_at=scheduled_at,
            status=PostStatus.SCHEDULED,
            recurrence=recurrence,
            recurrence_end_date=recurrence_end_date,
            campaign_id=campaign_id,
            source_content_id=source_content_id,
        )

        # Store the post
        await self._store_scheduled_post(post)

        logger.info(
            f"Scheduled post {post.id} for {account.platform.value} at {scheduled_at}"
        )

        return post

    async def update_scheduled_post(
        self,
        post_id: str,
        user_id: str,
        content: Optional[PostContent] = None,
        scheduled_at: Optional[datetime] = None,
        recurrence: Optional[RecurrenceType] = None,
        recurrence_end_date: Optional[datetime] = None,
    ) -> ScheduledPost:
        """
        Update a scheduled post.

        Args:
            post_id: The post to update
            user_id: The user making the update
            content: New content (optional)
            scheduled_at: New scheduled time (optional)
            recurrence: New recurrence pattern (optional)
            recurrence_end_date: New recurrence end date (optional)

        Returns:
            The updated post
        """
        self._ensure_enabled()

        post = await self.get_scheduled_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        if post.user_id != user_id:
            raise ValueError("Post does not belong to user")

        if post.status != PostStatus.SCHEDULED:
            raise ValueError(f"Cannot update post with status {post.status.value}")

        # Update fields
        if content is not None:
            post.content = content

        if scheduled_at is not None:
            if scheduled_at <= datetime.utcnow():
                raise ValueError("Scheduled time must be in the future")
            post.scheduled_at = scheduled_at

        if recurrence is not None:
            post.recurrence = recurrence

        if recurrence_end_date is not None:
            post.recurrence_end_date = recurrence_end_date

        post.updated_at = datetime.utcnow()

        # Save the update
        await self._store_scheduled_post(post)

        logger.info(f"Updated scheduled post {post_id}")

        return post

    async def cancel_scheduled_post(
        self,
        post_id: str,
        user_id: str,
    ) -> bool:
        """
        Cancel a scheduled post.

        Args:
            post_id: The post to cancel
            user_id: The user cancelling the post

        Returns:
            True if cancelled successfully
        """
        self._ensure_enabled()

        post = await self.get_scheduled_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        if post.user_id != user_id:
            raise ValueError("Post does not belong to user")

        if post.status not in (PostStatus.SCHEDULED, PostStatus.DRAFT):
            raise ValueError(f"Cannot cancel post with status {post.status.value}")

        post.status = PostStatus.CANCELLED
        post.updated_at = datetime.utcnow()

        await self._store_scheduled_post(post)

        logger.info(f"Cancelled scheduled post {post_id}")

        return True

    async def get_scheduled_post(
        self,
        post_id: str,
    ) -> Optional[ScheduledPost]:
        """Get a scheduled post by ID."""
        # In production, fetch from database
        return self._scheduled_posts.get(post_id)

    async def list_scheduled_posts(
        self,
        user_id: str,
        status: Optional[PostStatus] = None,
        platform: Optional[SocialPlatform] = None,
        account_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ScheduledPost], int]:
        """
        List scheduled posts with filters.

        Args:
            user_id: The user to list posts for
            status: Filter by status
            platform: Filter by platform
            account_id: Filter by account
            campaign_id: Filter by campaign
            from_date: Filter by scheduled date (from)
            to_date: Filter by scheduled date (to)
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (posts, total_count)
        """
        self._ensure_enabled()

        # Filter posts
        posts = [
            p for p in self._scheduled_posts.values()
            if p.user_id == user_id
        ]

        if status:
            posts = [p for p in posts if p.status == status]

        if platform:
            posts = [p for p in posts if p.platform == platform]

        if account_id:
            posts = [p for p in posts if p.account_id == account_id]

        if campaign_id:
            posts = [p for p in posts if p.campaign_id == campaign_id]

        if from_date:
            posts = [p for p in posts if p.scheduled_at >= from_date]

        if to_date:
            posts = [p for p in posts if p.scheduled_at <= to_date]

        # Sort by scheduled time
        posts.sort(key=lambda p: p.scheduled_at)

        # Paginate
        total = len(posts)
        start = (page - 1) * page_size
        end = start + page_size
        posts = posts[start:end]

        return posts, total

    async def get_due_posts(
        self,
        limit: int = 100,
    ) -> List[ScheduledPost]:
        """
        Get posts that are due for publishing.

        Args:
            limit: Maximum number of posts to return

        Returns:
            List of posts ready to be published
        """
        self._ensure_enabled()

        now = datetime.utcnow()

        # Find scheduled posts that are due
        due_posts = [
            p for p in self._scheduled_posts.values()
            if p.status == PostStatus.SCHEDULED and p.scheduled_at <= now
        ]

        # Sort by scheduled time (oldest first)
        due_posts.sort(key=lambda p: p.scheduled_at)

        return due_posts[:limit]

    # -------------------------------------------------------------------------
    # Optimal Time Suggestions
    # -------------------------------------------------------------------------

    async def get_optimal_times(
        self,
        user_id: str,
        platforms: Optional[List[SocialPlatform]] = None,
        timezone: str = "UTC",
    ) -> OptimalTimesResponse:
        """
        Get optimal posting times for a user's platforms.

        This analyzes historical engagement data to suggest the best times
        to post. Falls back to industry defaults if no user data available.

        Args:
            user_id: The user to get suggestions for
            platforms: Platforms to analyze (default: all connected)
            timezone: User's timezone for recommendations

        Returns:
            OptimalTimesResponse with time suggestions
        """
        self._ensure_enabled()

        # Get user's connected accounts to determine platforms
        user_accounts = [
            a for a in self._accounts.values()
            if a.user_id == user_id and a.is_active
        ]

        if platforms:
            user_platforms = [p for p in platforms if p in {a.platform for a in user_accounts}]
        else:
            user_platforms = list({a.platform for a in user_accounts})

        if not user_platforms:
            user_platforms = list(SocialPlatform)  # Show all platforms

        platform_times = []

        for platform in user_platforms:
            # Get historical analytics for this user and platform
            # In production, analyze actual engagement data
            time_slots = await self._calculate_optimal_times(
                user_id=user_id,
                platform=platform,
                timezone=timezone,
            )

            best_days = list(set(ts.day_of_week for ts in time_slots[:3]))
            worst_days = [d for d in range(7) if d not in best_days][:3]

            platform_times.append(
                PlatformOptimalTimes(
                    platform=platform,
                    time_slots=time_slots,
                    best_days=best_days,
                    worst_days=worst_days,
                    analysis_period_days=30,
                    sample_size=0,  # Would be actual count in production
                )
            )

        # Generate recommendations
        recommendations = self._generate_recommendations(platform_times)

        return OptimalTimesResponse(
            success=True,
            user_id=user_id,
            platforms=platform_times,
            recommendations=recommendations,
        )

    async def _calculate_optimal_times(
        self,
        user_id: str,
        platform: SocialPlatform,
        timezone: str = "UTC",
    ) -> List[OptimalTimeSlot]:
        """
        Calculate optimal posting times for a user and platform.

        In production, this would analyze historical engagement data.
        For now, returns industry defaults.
        """
        # Get default times for platform
        defaults = DEFAULT_OPTIMAL_TIMES.get(platform, [])

        time_slots = []
        for slot_data in defaults:
            time_slots.append(
                OptimalTimeSlot(
                    day_of_week=slot_data["day"],
                    hour=slot_data["hour"],
                    minute=0,
                    score=slot_data["score"],
                    expected_engagement_rate=slot_data["score"] * 5.0,  # Rough estimate
                    timezone=timezone,
                )
            )

        return time_slots

    def _generate_recommendations(
        self,
        platform_times: List[PlatformOptimalTimes],
    ) -> List[str]:
        """Generate natural language recommendations based on optimal times."""
        recommendations = []

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for pt in platform_times:
            if pt.time_slots:
                best_slot = pt.time_slots[0]
                day_name = day_names[best_slot.day_of_week]
                hour = best_slot.hour
                am_pm = "AM" if hour < 12 else "PM"
                display_hour = hour if hour <= 12 else hour - 12
                if display_hour == 0:
                    display_hour = 12

                recommendations.append(
                    f"Best time to post on {pt.platform.value}: "
                    f"{day_name}s at {display_hour}:00 {am_pm}"
                )

        if len(platform_times) > 1:
            recommendations.append(
                "Tip: Stagger posts across platforms by 15-30 minutes "
                "to maximize reach without overwhelming your audience."
            )

        return recommendations

    async def suggest_next_time(
        self,
        user_id: str,
        platform: SocialPlatform,
        after: Optional[datetime] = None,
    ) -> datetime:
        """
        Suggest the next optimal time to post.

        Args:
            user_id: The user to suggest for
            platform: The platform to post on
            after: Suggest a time after this datetime (default: now)

        Returns:
            Suggested datetime for posting
        """
        self._ensure_enabled()

        if after is None:
            after = datetime.utcnow()

        # Get optimal times
        time_slots = await self._calculate_optimal_times(user_id, platform)

        if not time_slots:
            # Default to next hour
            return after.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        # Find the next optimal slot
        current_day = after.weekday()
        current_hour = after.hour

        for slot in time_slots:
            # Check if this slot is in the future
            if slot.day_of_week > current_day:
                # This week, later day
                days_ahead = slot.day_of_week - current_day
            elif slot.day_of_week == current_day and slot.hour > current_hour:
                # Today, later hour
                days_ahead = 0
            else:
                # Next week
                days_ahead = 7 - current_day + slot.day_of_week

            suggested_time = after.replace(
                hour=slot.hour,
                minute=slot.minute,
                second=0,
                microsecond=0,
            ) + timedelta(days=days_ahead)

            if suggested_time > after:
                return suggested_time

        # Fallback to first slot next week
        first_slot = time_slots[0]
        days_ahead = 7 - current_day + first_slot.day_of_week
        return after.replace(
            hour=first_slot.hour,
            minute=first_slot.minute,
            second=0,
            microsecond=0,
        ) + timedelta(days=days_ahead)

    # -------------------------------------------------------------------------
    # Recurring Schedules
    # -------------------------------------------------------------------------

    async def create_recurring_posts(
        self,
        post: ScheduledPost,
        count: int = 10,
    ) -> List[ScheduledPost]:
        """
        Create multiple posts based on a recurring schedule.

        Args:
            post: The base post with recurrence settings
            count: Maximum number of recurring posts to create

        Returns:
            List of created scheduled posts
        """
        self._ensure_enabled()

        if post.recurrence == RecurrenceType.NONE:
            return [post]

        posts = [post]
        current_time = post.scheduled_at

        for _ in range(count - 1):
            # Calculate next occurrence
            if post.recurrence == RecurrenceType.DAILY:
                next_time = current_time + timedelta(days=1)
            elif post.recurrence == RecurrenceType.WEEKLY:
                next_time = current_time + timedelta(weeks=1)
            elif post.recurrence == RecurrenceType.MONTHLY:
                # Add roughly a month
                next_time = current_time + timedelta(days=30)
            else:
                break

            # Check if past end date
            if post.recurrence_end_date and next_time > post.recurrence_end_date:
                break

            # Create new post
            new_post = ScheduledPost(
                id=str(uuid.uuid4()),
                user_id=post.user_id,
                account_id=post.account_id,
                platform=post.platform,
                content=post.content,
                scheduled_at=next_time,
                status=PostStatus.SCHEDULED,
                recurrence=RecurrenceType.NONE,  # Individual posts don't recur
                campaign_id=post.campaign_id,
                source_content_id=post.source_content_id,
            )

            await self._store_scheduled_post(new_post)
            posts.append(new_post)
            current_time = next_time

        return posts

    # -------------------------------------------------------------------------
    # Account Management
    # -------------------------------------------------------------------------

    async def get_account(
        self,
        account_id: str,
    ) -> Optional[SocialAccount]:
        """Get a social account by ID."""
        # In production, fetch from database
        return self._accounts.get(account_id)

    async def store_account(
        self,
        account: SocialAccount,
    ) -> None:
        """Store a social account."""
        self._accounts[account.id] = account

    async def list_user_accounts(
        self,
        user_id: str,
    ) -> List[SocialAccount]:
        """List all accounts for a user."""
        return [
            a for a in self._accounts.values()
            if a.user_id == user_id and a.is_active
        ]

    # -------------------------------------------------------------------------
    # Internal Storage
    # -------------------------------------------------------------------------

    async def _store_scheduled_post(
        self,
        post: ScheduledPost,
    ) -> None:
        """Store a scheduled post."""
        # In production, save to database
        self._scheduled_posts[post.id] = post

    async def _delete_scheduled_post(
        self,
        post_id: str,
    ) -> None:
        """Delete a scheduled post."""
        # In production, delete from database
        self._scheduled_posts.pop(post_id, None)


# Global service instance
scheduler_service = SchedulerService()
