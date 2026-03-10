"""
LinkedIn API integration.

Implements OAuth 2.0 and LinkedIn Share API for posting.
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx

from src.types.social import (
    MediaAttachment,
    OAuthTokens,
    PLATFORM_CONFIGS,
    PostAnalytics,
    PostContent,
    SocialAccount,
    SocialPlatform,
)

from .base import (
    AuthenticationError,
    BasePlatform,
    MediaUploadError,
    PlatformError,
    RateLimitError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class LinkedInPlatform(BasePlatform):
    """
    LinkedIn API integration.

    Uses OAuth 2.0 for authentication and the Share API for posting.
    """

    # LinkedIn OAuth 2.0 endpoints
    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    REVOKE_URL = "https://www.linkedin.com/oauth/v2/revoke"

    # LinkedIn API endpoints
    API_BASE = "https://api.linkedin.com/v2"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

    def __init__(self) -> None:
        """Initialize LinkedIn platform integration."""
        super().__init__(PLATFORM_CONFIGS[SocialPlatform.LINKEDIN])

        self._client_id = os.environ.get("LINKEDIN_CLIENT_ID")
        self._client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")

        if self.is_configured:
            logger.info("LinkedIn platform initialized successfully")
        else:
            logger.warning("LinkedIn credentials not configured")

    @property
    def is_configured(self) -> bool:
        """Check if LinkedIn is properly configured."""
        return bool(self._client_id and self._client_secret)

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """Get LinkedIn OAuth 2.0 authorization URL."""
        self._ensure_configured()

        scope_list = scopes or self.config.oauth_scopes
        # LinkedIn also requires openid and profile for userinfo
        required_scopes = ["openid", "profile"]
        all_scopes = list(set(scope_list + required_scopes))
        scope_str = " ".join(all_scopes)

        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_str,
            "state": state,
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """Exchange authorization code for access tokens."""
        self._ensure_configured()

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers=headers,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise AuthenticationError(
                    f"Failed to exchange code: {error_data.get('error_description', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """Refresh an expired access token."""
        self._ensure_configured()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers=headers,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise AuthenticationError(
                    f"Failed to refresh token: {error_data.get('error_description', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", refresh_token),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
        )

    async def revoke_token(
        self,
        access_token: str,
    ) -> bool:
        """Revoke an access token."""
        self._ensure_configured()

        data = {
            "token": access_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.REVOKE_URL,
                data=data,
                headers=headers,
            )

            return response.status_code == 200

    async def get_user_profile(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """Get the authenticated user's LinkedIn profile."""
        self._ensure_configured()

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        async with httpx.AsyncClient() as client:
            # Get basic profile info from userinfo endpoint
            response = await client.get(
                self.USERINFO_URL,
                headers=headers,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired access token",
                    platform=self.platform,
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 60))
                raise RateLimitError(
                    "Rate limit exceeded",
                    platform=self.platform,
                    retry_after=retry_after,
                )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise PlatformError(
                    f"Failed to get user profile: {response.status_code}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            user_data = response.json()

        return {
            "id": user_data.get("sub"),
            "username": user_data.get("sub"),  # LinkedIn uses sub as unique identifier
            "display_name": user_data.get("name"),
            "profile_image_url": user_data.get("picture"),
            "email": user_data.get("email"),
            "given_name": user_data.get("given_name"),
            "family_name": user_data.get("family_name"),
        }

    async def publish_post(
        self,
        account: SocialAccount,
        content: PostContent,
    ) -> Tuple[str, str]:
        """Publish a post to LinkedIn."""
        self._ensure_configured()

        # Validate content
        errors = self.validate_content(content)
        if errors:
            raise ValidationError(
                f"Content validation failed: {'; '.join(errors)}",
                platform=self.platform,
            )

        # Get the user's URN (person ID)
        person_urn = f"urn:li:person:{account.platform_user_id}"

        # Build share content
        share_content: Dict[str, Any] = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content.text,
                    },
                    "shareMediaCategory": "NONE",
                },
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }

        # Add link if present
        if content.link_url:
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": content.link_url,
                    "title": {
                        "text": content.link_title or content.link_url,
                    },
                    "description": {
                        "text": content.link_description or "",
                    },
                }
            ]

        # Handle image uploads
        media_assets = []
        for media in content.media:
            if media.type == "image":
                try:
                    asset_urn = await self._upload_image(account, media)
                    media_assets.append({
                        "status": "READY",
                        "media": asset_urn,
                    })
                except Exception as e:
                    logger.warning(f"Failed to upload image: {e}")

        if media_assets:
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/ugcPosts",
                headers=headers,
                json=share_content,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired access token",
                    platform=self.platform,
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 60))
                raise RateLimitError(
                    "Rate limit exceeded",
                    platform=self.platform,
                    retry_after=retry_after,
                )

            if response.status_code not in (200, 201):
                error_data = response.json() if response.content else {}
                raise PlatformError(
                    f"Failed to post to LinkedIn: {error_data.get('message', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            # Get the post ID from the response header
            post_id = response.headers.get("x-restli-id", "")

        # Extract activity ID from the URN
        activity_id = post_id.split(":")[-1] if ":" in post_id else post_id
        post_url = f"https://www.linkedin.com/feed/update/{post_id}"

        logger.info(f"Published LinkedIn post {post_id}")

        return activity_id, post_url

    async def _upload_image(
        self,
        account: SocialAccount,
        media: MediaAttachment,
    ) -> str:
        """
        Upload an image to LinkedIn.

        LinkedIn image upload is a two-step process:
        1. Register the upload to get an upload URL
        2. Upload the image binary to that URL

        Returns:
            The asset URN for the uploaded image
        """
        person_urn = f"urn:li:person:{account.platform_user_id}"

        # Step 1: Register the upload
        register_request = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/assets?action=registerUpload",
                headers=headers,
                json=register_request,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise MediaUploadError(
                    f"Failed to register image upload: {error_data.get('message', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            register_data = response.json()

        upload_url = register_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset_urn = register_data["value"]["asset"]

        # Step 2: Upload the image
        # Fetch the image from the URL
        async with httpx.AsyncClient() as client:
            image_response = await client.get(media.url)
            if image_response.status_code != 200:
                raise MediaUploadError(
                    f"Failed to fetch image from {media.url}",
                    platform=self.platform,
                )
            image_data = image_response.content

            # Upload to LinkedIn
            upload_response = await client.put(
                upload_url,
                content=image_data,
                headers={
                    "Authorization": f"Bearer {account.access_token}",
                },
            )

            if upload_response.status_code not in (200, 201):
                raise MediaUploadError(
                    f"Failed to upload image to LinkedIn",
                    platform=self.platform,
                )

        return asset_urn

    async def delete_post(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> bool:
        """Delete a LinkedIn post."""
        self._ensure_configured()

        # Reconstruct the URN if needed
        if not platform_post_id.startswith("urn:"):
            platform_post_id = f"urn:li:share:{platform_post_id}"

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.API_BASE}/ugcPosts/{platform_post_id}",
                headers=headers,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired access token",
                    platform=self.platform,
                )

            return response.status_code in (200, 204)

    async def get_post_analytics(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> PostAnalytics:
        """Get analytics for a LinkedIn post."""
        self._ensure_configured()

        # Reconstruct the URN if needed
        share_urn = platform_post_id
        if not platform_post_id.startswith("urn:"):
            share_urn = f"urn:li:share:{platform_post_id}"

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # LinkedIn analytics requires specific permissions
        # This is a simplified implementation
        params = {
            "q": "organizationalEntity",
            "organizationalEntity": f"urn:li:person:{account.platform_user_id}",
            "timeIntervals.timeGranularityType": "ALL",
            "timeIntervals.timeRange.start": "0",
            "shares": share_urn,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/organizationalEntityShareStatistics",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                # Return empty analytics if can't fetch
                return PostAnalytics(
                    id="",
                    post_id="",
                    platform=self.platform,
                    platform_post_id=platform_post_id,
                )

            data = response.json()

        # Parse analytics data
        elements = data.get("elements", [])
        if not elements:
            return PostAnalytics(
                id="",
                post_id="",
                platform=self.platform,
                platform_post_id=platform_post_id,
            )

        stats = elements[0].get("totalShareStatistics", {})

        impressions = stats.get("impressionCount", 0)
        engagements = stats.get("engagement", 0)
        clicks = stats.get("clickCount", 0)

        engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0.0

        return PostAnalytics(
            id="",
            post_id="",
            platform=self.platform,
            platform_post_id=platform_post_id,
            impressions=impressions,
            engagements=engagements,
            likes=stats.get("likeCount", 0),
            comments=stats.get("commentCount", 0),
            shares=stats.get("shareCount", 0),
            reposts=stats.get("shareCount", 0),
            clicks=clicks,
            engagement_rate=engagement_rate,
            raw_data=stats,
        )


# Global instance
linkedin_platform = LinkedInPlatform()
