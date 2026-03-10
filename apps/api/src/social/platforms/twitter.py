"""
Twitter/X API v2 integration.

Implements OAuth 2.0 PKCE flow and Twitter API v2 for posting.
"""

import asyncio
import base64
import hashlib
import logging
import os
import secrets
from functools import partial
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


class TwitterPlatform(BasePlatform):
    """
    Twitter/X API v2 integration.

    Uses OAuth 2.0 with PKCE for user authentication and Twitter API v2
    for posting tweets.
    """

    # Twitter OAuth 2.0 endpoints
    AUTHORIZATION_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    REVOKE_URL = "https://api.twitter.com/2/oauth2/revoke"

    # Twitter API v2 endpoints
    API_BASE = "https://api.twitter.com/2"
    UPLOAD_BASE = "https://upload.twitter.com/1.1"

    def __init__(self) -> None:
        """Initialize Twitter platform integration."""
        super().__init__(PLATFORM_CONFIGS[SocialPlatform.TWITTER])

        self._client_id = os.environ.get("TWITTER_CLIENT_ID")
        self._client_secret = os.environ.get("TWITTER_CLIENT_SECRET")

        # For media upload (v1.1 API requires OAuth 1.0a)
        self._api_key = os.environ.get("TWITTER_API_KEY")
        self._api_secret = os.environ.get("TWITTER_API_SECRET")

        # Store PKCE verifiers temporarily (in production, use Redis/session)
        self._pkce_verifiers: Dict[str, str] = {}

        if self.is_configured:
            logger.info("Twitter platform initialized successfully")
        else:
            logger.warning("Twitter credentials not configured")

    @property
    def is_configured(self) -> bool:
        """Check if Twitter is properly configured."""
        return bool(self._client_id and self._client_secret)

    def _generate_pkce_pair(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate a random verifier
        verifier = secrets.token_urlsafe(32)

        # Create SHA256 hash and base64url encode
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        return verifier, challenge

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """Get Twitter OAuth 2.0 authorization URL with PKCE."""
        self._ensure_configured()

        # Generate PKCE pair
        verifier, challenge = self._generate_pkce_pair()
        self._pkce_verifiers[state] = verifier

        # Build scopes string
        scope_list = scopes or self.config.oauth_scopes
        scope_str = " ".join(scope_list)

        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_str,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> OAuthTokens:
        """Exchange authorization code for access tokens."""
        self._ensure_configured()

        # Get PKCE verifier
        verifier = self._pkce_verifiers.pop(state, None) if state else None
        if not verifier:
            raise AuthenticationError(
                "Invalid or expired OAuth state",
                platform=self.platform,
            )

        # Prepare token request
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._client_id,
            "code_verifier": verifier,
        }

        # Basic auth header
        credentials = f"{self._client_id}:{self._client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
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
        }

        credentials = f"{self._client_id}:{self._client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
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
            "token_type_hint": "access_token",
            "client_id": self._client_id,
        }

        credentials = f"{self._client_id}:{self._client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
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
        """Get the authenticated user's Twitter profile."""
        self._ensure_configured()

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        params = {
            "user.fields": "id,name,username,profile_image_url,description",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/users/me",
                headers=headers,
                params=params,
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

            data = response.json()

        user_data = data.get("data", {})
        return {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "display_name": user_data.get("name"),
            "profile_image_url": user_data.get("profile_image_url"),
            "description": user_data.get("description"),
        }

    async def publish_post(
        self,
        account: SocialAccount,
        content: PostContent,
    ) -> Tuple[str, str]:
        """Publish a tweet."""
        self._ensure_configured()

        # Validate content
        errors = self.validate_content(content)
        if errors:
            raise ValidationError(
                f"Content validation failed: {'; '.join(errors)}",
                platform=self.platform,
            )

        # Build tweet payload
        payload: Dict[str, Any] = {
            "text": content.text,
        }

        # Upload media if present
        media_ids = []
        for media in content.media:
            try:
                media_id = await self.upload_media(account, media)
                media_ids.append(media_id)
            except Exception as e:
                logger.warning(f"Failed to upload media: {e}")

        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE}/tweets",
                headers=headers,
                json=payload,
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
                    f"Failed to post tweet: {error_data.get('detail', 'Unknown error')}",
                    platform=self.platform,
                    raw_error=error_data,
                )

            data = response.json()

        tweet_id = data["data"]["id"]
        tweet_url = f"https://twitter.com/{account.platform_username}/status/{tweet_id}"

        logger.info(f"Published tweet {tweet_id} for user {account.platform_username}")

        return tweet_id, tweet_url

    async def delete_post(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> bool:
        """Delete a tweet."""
        self._ensure_configured()

        headers = {
            "Authorization": f"Bearer {account.access_token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.API_BASE}/tweets/{platform_post_id}",
                headers=headers,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired access token",
                    platform=self.platform,
                )

            return response.status_code == 200

    async def upload_media(
        self,
        account: SocialAccount,
        media: MediaAttachment,
    ) -> str:
        """
        Upload media to Twitter.

        Note: This uses the v1.1 media upload endpoint which may require
        different authentication. For production, implement OAuth 1.0a
        or use the v2 media upload when available.
        """
        # Simplified implementation - in production, implement full media upload
        # with chunked upload for large files and proper OAuth 1.0a signing

        raise MediaUploadError(
            "Direct media upload requires OAuth 1.0a credentials",
            platform=self.platform,
        )

    async def get_post_analytics(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> PostAnalytics:
        """Get analytics for a tweet."""
        self._ensure_configured()

        headers = {
            "Authorization": f"Bearer {account.access_token}",
        }

        params = {
            "tweet.fields": "public_metrics,non_public_metrics,organic_metrics",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/tweets/{platform_post_id}",
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

        tweet_data = data.get("data", {})
        public_metrics = tweet_data.get("public_metrics", {})
        non_public_metrics = tweet_data.get("non_public_metrics", {})

        impressions = non_public_metrics.get("impression_count", 0)
        engagements = (
            public_metrics.get("like_count", 0)
            + public_metrics.get("retweet_count", 0)
            + public_metrics.get("reply_count", 0)
            + public_metrics.get("quote_count", 0)
        )

        engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0.0

        return PostAnalytics(
            id="",  # Will be set by caller
            post_id="",  # Will be set by caller
            platform=self.platform,
            platform_post_id=platform_post_id,
            impressions=impressions,
            likes=public_metrics.get("like_count", 0),
            retweets=public_metrics.get("retweet_count", 0),
            comments=public_metrics.get("reply_count", 0),
            shares=public_metrics.get("quote_count", 0),
            clicks=non_public_metrics.get("url_link_clicks", 0),
            profile_visits=non_public_metrics.get("user_profile_clicks", 0),
            engagement_rate=engagement_rate,
            raw_data=tweet_data,
        )

    async def publish_thread(
        self,
        account: SocialAccount,
        tweets: List[str],
    ) -> List[Tuple[str, str]]:
        """
        Publish a Twitter thread.

        Args:
            account: The social account to post from
            tweets: List of tweet texts for the thread

        Returns:
            List of (tweet_id, tweet_url) tuples for each tweet
        """
        self._ensure_configured()

        results = []
        reply_to_id = None

        for tweet_text in tweets:
            payload: Dict[str, Any] = {"text": tweet_text}

            if reply_to_id:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

            headers = {
                "Authorization": f"Bearer {account.access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_BASE}/tweets",
                    headers=headers,
                    json=payload,
                )

                if response.status_code not in (200, 201):
                    error_data = response.json() if response.content else {}
                    raise PlatformError(
                        f"Failed to post thread tweet: {error_data.get('detail', 'Unknown error')}",
                        platform=self.platform,
                        raw_error=error_data,
                    )

                data = response.json()

            tweet_id = data["data"]["id"]
            tweet_url = f"https://twitter.com/{account.platform_username}/status/{tweet_id}"
            results.append((tweet_id, tweet_url))

            # Next tweet replies to this one
            reply_to_id = tweet_id

            # Small delay between tweets to avoid rate limits
            await asyncio.sleep(1)

        return results


# Global instance
twitter_platform = TwitterPlatform()
