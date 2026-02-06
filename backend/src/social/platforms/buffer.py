"""
Buffer API integration.

Buffer provides a unified API for posting to multiple social platforms,
serving as a fallback when direct platform integration is not available.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.types.social import (
    MediaAttachment,
    OAuthTokens,
    PostAnalytics,
    PostContent,
    SocialAccount,
    SocialPlatform,
    PlatformConfig,
)

from .base import (
    AuthenticationError,
    BasePlatform,
    PlatformError,
    RateLimitError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# Buffer doesn't map directly to a single platform, so we create a custom config
BUFFER_CONFIG = PlatformConfig(
    platform=SocialPlatform.TWITTER,  # Default, but supports multiple
    name="Buffer",
    max_text_length=10000,  # Buffer handles platform-specific limits
    max_media_count=10,
    supported_media_types=["image", "video", "gif"],
    oauth_scopes=[],
    rate_limit_posts_per_day=1000,
    rate_limit_posts_per_hour=100,
)


class BufferPlatform(BasePlatform):
    """
    Buffer API integration.

    Buffer provides a unified publishing API that can post to multiple
    social platforms. Use this as a fallback when direct platform
    integration requires complex OAuth flows.

    Buffer supports:
    - Twitter/X
    - LinkedIn
    - Facebook
    - Instagram
    - Pinterest
    - And more...
    """

    API_BASE = "https://api.bufferapp.com/1"

    # Map our platform enum to Buffer's profile service names
    PLATFORM_SERVICE_MAP = {
        SocialPlatform.TWITTER: "twitter",
        SocialPlatform.LINKEDIN: "linkedin",
        SocialPlatform.FACEBOOK: "facebook",
        SocialPlatform.INSTAGRAM: "instagram",
    }

    def __init__(self) -> None:
        """Initialize Buffer platform integration."""
        super().__init__(BUFFER_CONFIG)

        self._access_token = os.environ.get("BUFFER_ACCESS_TOKEN")

        if self.is_configured:
            logger.info("Buffer platform initialized successfully")
        else:
            logger.warning("Buffer access token not configured")

    @property
    def is_configured(self) -> bool:
        """Check if Buffer is properly configured."""
        return bool(self._access_token)

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """
        Buffer uses simple access token authentication.

        For OAuth flow, users should authorize directly on Buffer's website
        and provide the access token.
        """
        raise NotImplementedError(
            "Buffer uses access token authentication. "
            "Generate a token at https://buffer.com/developers/apps"
        )

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """Buffer uses simple access token authentication."""
        raise NotImplementedError(
            "Buffer uses access token authentication. "
            "Set BUFFER_ACCESS_TOKEN environment variable."
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """Buffer access tokens don't expire in the same way."""
        raise NotImplementedError(
            "Buffer access tokens don't require refresh. "
            "If token is invalid, generate a new one."
        )

    async def revoke_token(
        self,
        access_token: str,
    ) -> bool:
        """Revoke Buffer access token."""
        # Buffer token revocation is done through the web interface
        return True

    async def get_user_profile(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """Get the Buffer user profile."""
        self._ensure_configured()

        params = {"access_token": access_token or self._access_token}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/user.json",
                params=params,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Buffer access token",
                    platform=self.platform,
                )

            if response.status_code == 429:
                raise RateLimitError(
                    "Buffer rate limit exceeded",
                    platform=self.platform,
                    retry_after=60,
                )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise PlatformError(
                    f"Failed to get Buffer profile: {response.status_code}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            data = response.json()

        return {
            "id": data.get("id"),
            "username": data.get("id"),
            "display_name": data.get("name"),
            "profile_image_url": data.get("avatar"),
            "plan": data.get("plan"),
        }

    async def get_profiles(
        self,
        platform_filter: Optional[SocialPlatform] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get connected social profiles from Buffer.

        Args:
            platform_filter: Optional platform to filter profiles

        Returns:
            List of connected profiles
        """
        self._ensure_configured()

        params = {"access_token": self._access_token}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/profiles.json",
                params=params,
            )

            if response.status_code != 200:
                return []

            profiles = response.json()

        if platform_filter:
            service_name = self.PLATFORM_SERVICE_MAP.get(platform_filter)
            if service_name:
                profiles = [p for p in profiles if p.get("service") == service_name]

        return profiles

    async def publish_post(
        self,
        account: SocialAccount,
        content: PostContent,
    ) -> Tuple[str, str]:
        """
        Publish a post via Buffer.

        Note: The 'account' here should have the Buffer profile ID stored
        in the platform_user_id field.
        """
        self._ensure_configured()

        # Validate content
        errors = self.validate_content(content)
        if errors:
            raise ValidationError(
                f"Content validation failed: {'; '.join(errors)}",
                platform=self.platform,
            )

        # Build the update payload
        data = {
            "access_token": self._access_token,
            "profile_ids[]": account.platform_user_id,  # Buffer profile ID
            "text": content.text,
            "now": "true",  # Post immediately
        }

        # Add media if present
        if content.media:
            for i, media in enumerate(content.media):
                data[f"media[photo]"] = media.url
                if media.alt_text:
                    data[f"media[description]"] = media.alt_text
                break  # Buffer only supports one media per update in basic API

        # Add link if present
        if content.link_url:
            data["media[link]"] = content.link_url
            if content.link_title:
                data["media[title]"] = content.link_title
            if content.link_description:
                data["media[description]"] = content.link_description

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/updates/create.json",
                data=data,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid Buffer access token",
                    platform=self.platform,
                )

            if response.status_code == 429:
                raise RateLimitError(
                    "Buffer rate limit exceeded",
                    platform=self.platform,
                    retry_after=60,
                )

            if response.status_code not in (200, 201):
                error_data = response.json() if response.content else {}
                raise PlatformError(
                    f"Failed to create Buffer update: {error_data.get('message', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            result = response.json()

        update = result.get("updates", [{}])[0]
        update_id = update.get("id", "")

        # Buffer doesn't immediately provide the final post URL
        # It goes through their queue even with now=true
        post_url = f"https://buffer.com/app/post/{update_id}"

        logger.info(f"Created Buffer update {update_id}")

        return update_id, post_url

    async def schedule_post(
        self,
        account: SocialAccount,
        content: PostContent,
        scheduled_at: datetime,
    ) -> Tuple[str, str]:
        """
        Schedule a post via Buffer.

        Args:
            account: The Buffer profile to post to
            content: The content to post
            scheduled_at: When to publish the post

        Returns:
            Tuple of (update_id, buffer_url)
        """
        self._ensure_configured()

        # Build the update payload
        data = {
            "access_token": self._access_token,
            "profile_ids[]": account.platform_user_id,
            "text": content.text,
            "scheduled_at": scheduled_at.isoformat(),
        }

        # Add media if present
        if content.media:
            data["media[photo]"] = content.media[0].url

        # Add link if present
        if content.link_url:
            data["media[link]"] = content.link_url

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/updates/create.json",
                data=data,
            )

            if response.status_code not in (200, 201):
                error_data = response.json() if response.content else {}
                raise PlatformError(
                    f"Failed to schedule Buffer update: {error_data.get('message', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            result = response.json()

        update = result.get("updates", [{}])[0]
        update_id = update.get("id", "")
        post_url = f"https://buffer.com/app/post/{update_id}"

        logger.info(f"Scheduled Buffer update {update_id} for {scheduled_at}")

        return update_id, post_url

    async def delete_post(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> bool:
        """Delete a scheduled or sent update from Buffer."""
        self._ensure_configured()

        params = {"access_token": self._access_token}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/updates/{platform_post_id}/destroy.json",
                params=params,
            )

            return response.status_code == 200

    async def get_post_analytics(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> PostAnalytics:
        """Get analytics for a Buffer update."""
        self._ensure_configured()

        params = {"access_token": self._access_token}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/updates/{platform_post_id}/interactions.json",
                params=params,
            )

            if response.status_code != 200:
                return PostAnalytics(
                    id="",
                    post_id="",
                    platform=self.platform,
                    platform_post_id=platform_post_id,
                )

            data = response.json()

        interactions = data.get("interactions", [])

        # Aggregate interactions by type
        likes = 0
        comments = 0
        shares = 0
        clicks = 0

        for interaction in interactions:
            int_type = interaction.get("type", "")
            if int_type == "like":
                likes += 1
            elif int_type == "comment":
                comments += 1
            elif int_type == "share":
                shares += 1
            elif int_type == "click":
                clicks += 1

        total_engagements = likes + comments + shares + clicks

        return PostAnalytics(
            id="",
            post_id="",
            platform=self.platform,
            platform_post_id=platform_post_id,
            likes=likes,
            comments=comments,
            shares=shares,
            clicks=clicks,
            engagements=total_engagements,
            raw_data=data,
        )

    async def get_pending_updates(
        self,
        profile_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get pending (scheduled) updates for a Buffer profile.

        Args:
            profile_id: Buffer profile ID

        Returns:
            List of pending updates
        """
        self._ensure_configured()

        params = {"access_token": self._access_token}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/profiles/{profile_id}/updates/pending.json",
                params=params,
            )

            if response.status_code != 200:
                return []

            data = response.json()

        return data.get("updates", [])

    async def get_sent_updates(
        self,
        profile_id: str,
        count: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get sent (published) updates for a Buffer profile.

        Args:
            profile_id: Buffer profile ID
            count: Number of updates to retrieve

        Returns:
            List of sent updates
        """
        self._ensure_configured()

        params = {
            "access_token": self._access_token,
            "count": count,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/profiles/{profile_id}/updates/sent.json",
                params=params,
            )

            if response.status_code != 200:
                return []

            data = response.json()

        return data.get("updates", [])


# Global instance
buffer_platform = BufferPlatform()
