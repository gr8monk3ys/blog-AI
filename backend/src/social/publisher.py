"""
Social media post publishing service.

Provides:
- Async post publishing with retry logic
- Rate limit handling
- Media upload support
- Webhook notifications for publish events
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.types.social import (
    PostAnalytics,
    PostContent,
    PostStatus,
    ScheduledPost,
    SocialAccount,
    SocialPlatform,
)

from .platforms.base import (
    AuthenticationError,
    BasePlatform,
    PlatformError,
    RateLimitError,
)
from .platforms.buffer import buffer_platform
from .platforms.linkedin import linkedin_platform
from .platforms.twitter import twitter_platform

logger = logging.getLogger(__name__)


class PublisherService:
    """
    Service for publishing social media posts.

    Handles async publishing with retry logic, rate limit handling,
    and webhook notifications.
    """

    # Retry configuration
    DEFAULT_MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min

    def __init__(self) -> None:
        """Initialize the publisher service."""
        self._enabled = os.environ.get("SOCIAL_SCHEDULER_ENABLED", "true").lower() == "true"

        # Platform instances
        self._platforms: Dict[SocialPlatform, BasePlatform] = {
            SocialPlatform.TWITTER: twitter_platform,
            SocialPlatform.LINKEDIN: linkedin_platform,
        }

        # Fallback to Buffer for platforms without direct integration
        self._buffer_fallback = buffer_platform

        # Webhook callback
        self._webhook_callback: Optional[Callable] = None

        # Rate limit tracking per account
        self._rate_limits: Dict[str, Dict[str, Any]] = {}

        if self._enabled:
            logger.info("Social publisher service initialized")
        else:
            logger.warning("Social publisher is disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if the publisher is enabled."""
        return self._enabled

    def _ensure_enabled(self) -> None:
        """Raise an error if publisher is disabled."""
        if not self._enabled:
            raise ValueError("Social publisher is disabled")

    def get_platform(
        self,
        platform: SocialPlatform,
    ) -> BasePlatform:
        """
        Get the platform integration for a given platform.

        Falls back to Buffer if direct integration not available.
        """
        direct_platform = self._platforms.get(platform)

        if direct_platform and direct_platform.is_configured:
            return direct_platform

        # Fall back to Buffer
        if self._buffer_fallback.is_configured:
            return self._buffer_fallback

        raise ValueError(
            f"No integration configured for {platform.value}. "
            f"Configure platform credentials or BUFFER_ACCESS_TOKEN."
        )

    def set_webhook_callback(
        self,
        callback: Callable[[ScheduledPost, str], None],
    ) -> None:
        """
        Set a callback function for webhook notifications.

        The callback receives (post, event_type) where event_type is one of:
        - "published": Post was successfully published
        - "failed": Post publishing failed
        - "rate_limited": Post hit rate limit, will retry
        """
        self._webhook_callback = callback

    async def _notify_webhook(
        self,
        post: ScheduledPost,
        event_type: str,
    ) -> None:
        """Send webhook notification for a post event."""
        if self._webhook_callback:
            try:
                await asyncio.to_thread(self._webhook_callback, post, event_type)
            except Exception as e:
                logger.warning(f"Webhook notification failed: {e}")

    # -------------------------------------------------------------------------
    # Publishing
    # -------------------------------------------------------------------------

    async def publish_post(
        self,
        post: ScheduledPost,
        account: SocialAccount,
    ) -> Tuple[str, str]:
        """
        Publish a scheduled post immediately.

        Args:
            post: The scheduled post to publish
            account: The social account to publish from

        Returns:
            Tuple of (platform_post_id, platform_post_url)

        Raises:
            PlatformError: If publishing fails
            RateLimitError: If rate limited
            AuthenticationError: If auth fails
        """
        self._ensure_enabled()

        platform = self.get_platform(post.platform)

        # Check rate limits before attempting
        await self._check_rate_limit(account)

        logger.info(
            f"Publishing post {post.id} to {post.platform.value} "
            f"(account: {account.platform_username})"
        )

        try:
            # Attempt to publish
            post_id, post_url = await platform.publish_post(account, post.content)

            # Update rate limit tracking
            await self._record_post(account)

            logger.info(f"Successfully published post {post.id} as {post_id}")

            return post_id, post_url

        except RateLimitError as e:
            logger.warning(
                f"Rate limited publishing post {post.id}: {e.message} "
                f"(retry after {e.retry_after}s)"
            )
            await self._record_rate_limit(account, e.retry_after)
            raise

        except AuthenticationError as e:
            logger.error(f"Authentication failed for post {post.id}: {e.message}")
            raise

        except PlatformError as e:
            logger.error(f"Failed to publish post {post.id}: {e.message}")
            raise

    async def publish_with_retry(
        self,
        post: ScheduledPost,
        account: SocialAccount,
        max_retries: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publish a post with automatic retry on failure.

        Args:
            post: The scheduled post to publish
            account: The social account to publish from
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Tuple of (success, platform_post_id, error_message)
        """
        self._ensure_enabled()

        retries = max_retries or self.DEFAULT_MAX_RETRIES
        last_error = None

        for attempt in range(retries + 1):
            try:
                post_id, post_url = await self.publish_post(post, account)

                # Update post status
                post.status = PostStatus.PUBLISHED
                post.published_at = datetime.utcnow()
                post.platform_post_id = post_id
                post.platform_post_url = post_url

                await self._notify_webhook(post, "published")

                return True, post_id, None

            except RateLimitError as e:
                last_error = str(e)
                post.retry_count = attempt + 1

                if attempt < retries:
                    delay = e.retry_after or self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.info(f"Retrying post {post.id} in {delay}s (attempt {attempt + 1}/{retries})")
                    await self._notify_webhook(post, "rate_limited")
                    await asyncio.sleep(delay)
                else:
                    post.status = PostStatus.FAILED
                    post.error_message = f"Rate limit exceeded after {retries} retries"
                    await self._notify_webhook(post, "failed")

            except AuthenticationError as e:
                # Don't retry auth errors
                last_error = str(e)
                post.status = PostStatus.FAILED
                post.error_message = f"Authentication failed: {e.message}"
                await self._notify_webhook(post, "failed")
                break

            except PlatformError as e:
                last_error = str(e)
                post.retry_count = attempt + 1

                if attempt < retries:
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.info(f"Retrying post {post.id} in {delay}s after error (attempt {attempt + 1}/{retries})")
                    await asyncio.sleep(delay)
                else:
                    post.status = PostStatus.FAILED
                    post.error_message = f"Publishing failed: {e.message}"
                    await self._notify_webhook(post, "failed")

            except Exception as e:
                last_error = str(e)
                logger.exception(f"Unexpected error publishing post {post.id}")
                post.status = PostStatus.FAILED
                post.error_message = f"Unexpected error: {str(e)}"
                await self._notify_webhook(post, "failed")
                break

        return False, None, last_error

    async def publish_batch(
        self,
        posts: List[Tuple[ScheduledPost, SocialAccount]],
        max_concurrent: int = 5,
    ) -> Dict[str, Tuple[bool, Optional[str], Optional[str]]]:
        """
        Publish multiple posts concurrently.

        Args:
            posts: List of (post, account) tuples to publish
            max_concurrent: Maximum concurrent publishing tasks

        Returns:
            Dictionary mapping post_id to (success, platform_post_id, error)
        """
        self._ensure_enabled()

        semaphore = asyncio.Semaphore(max_concurrent)
        results: Dict[str, Tuple[bool, Optional[str], Optional[str]]] = {}

        async def publish_one(
            post: ScheduledPost,
            account: SocialAccount,
        ) -> None:
            async with semaphore:
                success, post_id, error = await self.publish_with_retry(post, account)
                results[post.id] = (success, post_id, error)

        tasks = [
            publish_one(post, account)
            for post, account in posts
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------

    async def _check_rate_limit(
        self,
        account: SocialAccount,
    ) -> None:
        """
        Check if an account is rate limited.

        Raises:
            RateLimitError: If the account is currently rate limited
        """
        limits = self._rate_limits.get(account.id, {})

        # Check if in cooldown from previous rate limit
        cooldown_until = limits.get("cooldown_until")
        if cooldown_until and datetime.utcnow() < cooldown_until:
            remaining = int((cooldown_until - datetime.utcnow()).total_seconds())
            raise RateLimitError(
                f"Account in rate limit cooldown",
                platform=account.platform,
                retry_after=remaining,
            )

        # Check hourly post limit
        hourly_count = limits.get("hourly_count", 0)
        hourly_reset = limits.get("hourly_reset")

        if hourly_reset and datetime.utcnow() > hourly_reset:
            # Reset counter
            limits["hourly_count"] = 0
            limits["hourly_reset"] = datetime.utcnow()

        # Get platform config for limits
        try:
            platform = self.get_platform(account.platform)
            hourly_limit = platform.config.rate_limit_posts_per_hour
        except ValueError:
            hourly_limit = 25  # Default

        if hourly_count >= hourly_limit:
            raise RateLimitError(
                f"Hourly post limit ({hourly_limit}) reached for account",
                platform=account.platform,
                retry_after=3600,  # 1 hour
            )

    async def _record_post(
        self,
        account: SocialAccount,
    ) -> None:
        """Record a successful post for rate limit tracking."""
        if account.id not in self._rate_limits:
            self._rate_limits[account.id] = {
                "hourly_count": 0,
                "hourly_reset": datetime.utcnow(),
            }

        self._rate_limits[account.id]["hourly_count"] = (
            self._rate_limits[account.id].get("hourly_count", 0) + 1
        )

    async def _record_rate_limit(
        self,
        account: SocialAccount,
        retry_after: int,
    ) -> None:
        """Record a rate limit hit for an account."""
        if account.id not in self._rate_limits:
            self._rate_limits[account.id] = {}

        from datetime import timedelta
        self._rate_limits[account.id]["cooldown_until"] = (
            datetime.utcnow() + timedelta(seconds=retry_after)
        )

    async def get_rate_limit_status(
        self,
        account: SocialAccount,
    ) -> Dict[str, Any]:
        """
        Get the current rate limit status for an account.

        Returns:
            Dictionary with rate limit info
        """
        limits = self._rate_limits.get(account.id, {})

        return {
            "hourly_count": limits.get("hourly_count", 0),
            "hourly_limit": 25,  # Would come from platform config
            "hourly_reset": limits.get("hourly_reset"),
            "in_cooldown": bool(
                limits.get("cooldown_until")
                and datetime.utcnow() < limits.get("cooldown_until")
            ),
            "cooldown_until": limits.get("cooldown_until"),
        }

    # -------------------------------------------------------------------------
    # Media Upload
    # -------------------------------------------------------------------------

    async def upload_media(
        self,
        account: SocialAccount,
        media_url: str,
        media_type: str = "image",
        alt_text: Optional[str] = None,
    ) -> str:
        """
        Upload media to a platform.

        Args:
            account: The social account to upload to
            media_url: URL of the media to upload
            media_type: Type of media (image, video, gif)
            alt_text: Optional alt text for accessibility

        Returns:
            Platform's media ID
        """
        self._ensure_enabled()

        from src.types.social import MediaAttachment

        platform = self.get_platform(account.platform)

        media = MediaAttachment(
            url=media_url,
            type=media_type,  # type: ignore
            alt_text=alt_text,
        )

        return await platform.upload_media(account, media)

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    async def get_post_analytics(
        self,
        post: ScheduledPost,
        account: SocialAccount,
    ) -> Optional[PostAnalytics]:
        """
        Get analytics for a published post.

        Args:
            post: The published post
            account: The social account

        Returns:
            PostAnalytics or None if not available
        """
        self._ensure_enabled()

        if not post.platform_post_id:
            return None

        platform = self.get_platform(post.platform)

        try:
            analytics = await platform.get_post_analytics(
                account,
                post.platform_post_id,
            )
            analytics.id = f"{post.id}_analytics"
            analytics.post_id = post.id
            return analytics

        except Exception as e:
            logger.warning(f"Failed to get analytics for post {post.id}: {e}")
            return None

    async def refresh_analytics_batch(
        self,
        posts: List[Tuple[ScheduledPost, SocialAccount]],
    ) -> Dict[str, PostAnalytics]:
        """
        Refresh analytics for multiple posts.

        Args:
            posts: List of (post, account) tuples

        Returns:
            Dictionary mapping post_id to analytics
        """
        self._ensure_enabled()

        results: Dict[str, PostAnalytics] = {}

        for post, account in posts:
            analytics = await self.get_post_analytics(post, account)
            if analytics:
                results[post.id] = analytics

        return results

    # -------------------------------------------------------------------------
    # Token Refresh
    # -------------------------------------------------------------------------

    async def refresh_account_token(
        self,
        account: SocialAccount,
    ) -> SocialAccount:
        """
        Refresh an account's access token if expired.

        Args:
            account: The account to refresh

        Returns:
            Updated account with new tokens
        """
        self._ensure_enabled()

        if not account.refresh_token:
            raise AuthenticationError(
                "No refresh token available",
                platform=account.platform,
            )

        # Check if token needs refresh
        if account.token_expires_at and datetime.utcnow() < account.token_expires_at:
            return account

        platform = self.get_platform(account.platform)

        try:
            new_tokens = await platform.refresh_access_token(account.refresh_token)

            account.access_token = new_tokens.access_token
            if new_tokens.refresh_token:
                account.refresh_token = new_tokens.refresh_token
            account.token_expires_at = new_tokens.expires_at
            account.updated_at = datetime.utcnow()

            logger.info(f"Refreshed token for account {account.id}")

            return account

        except Exception as e:
            logger.error(f"Failed to refresh token for account {account.id}: {e}")
            raise AuthenticationError(
                f"Token refresh failed: {str(e)}",
                platform=account.platform,
            )


# Global service instance
publisher_service = PublisherService()
