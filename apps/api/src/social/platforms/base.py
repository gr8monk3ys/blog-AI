"""
Base class for social media platform integrations.

Defines the interface that all platform implementations must follow.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.types.social import (
    MediaAttachment,
    OAuthTokens,
    PlatformConfig,
    PostAnalytics,
    PostContent,
    SocialAccount,
    SocialPlatform,
)

logger = logging.getLogger(__name__)


class PlatformError(Exception):
    """Base exception for platform errors."""

    def __init__(
        self,
        message: str,
        platform: Optional[SocialPlatform] = None,
        error_code: Optional[str] = None,
        retry_after: Optional[int] = None,
        raw_error: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize platform error.

        Args:
            message: Human-readable error message
            platform: The platform that raised the error
            error_code: Platform-specific error code
            retry_after: Seconds to wait before retry (for rate limits)
            raw_error: Raw error response from the platform
        """
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.error_code = error_code
        self.retry_after = retry_after
        self.raw_error = raw_error


class RateLimitError(PlatformError):
    """Exception raised when rate limited by platform."""

    def __init__(
        self,
        message: str,
        platform: SocialPlatform,
        retry_after: int,
        error_code: Optional[str] = None,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Human-readable error message
            platform: The platform that raised the error
            retry_after: Seconds to wait before retry
            error_code: Platform-specific error code
        """
        super().__init__(
            message=message,
            platform=platform,
            error_code=error_code,
            retry_after=retry_after,
        )


class AuthenticationError(PlatformError):
    """Exception raised when authentication fails."""

    pass


class ValidationError(PlatformError):
    """Exception raised when content validation fails."""

    pass


class MediaUploadError(PlatformError):
    """Exception raised when media upload fails."""

    pass


class BasePlatform(ABC):
    """
    Abstract base class for social media platform integrations.

    All platform implementations must inherit from this class and
    implement the abstract methods.
    """

    def __init__(self, config: PlatformConfig) -> None:
        """
        Initialize the platform integration.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.platform = config.platform
        self._logger = logging.getLogger(f"{__name__}.{config.platform.value}")

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the platform is properly configured with API credentials."""
        pass

    def _ensure_configured(self) -> None:
        """Raise an error if platform is not configured."""
        if not self.is_configured:
            raise PlatformError(
                f"{self.platform.value} is not configured. Check API credentials.",
                platform=self.platform,
            )

    # -------------------------------------------------------------------------
    # OAuth Methods
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """
        Get the OAuth authorization URL for user authentication.

        Args:
            redirect_uri: URL to redirect to after authorization
            state: State parameter for CSRF protection
            scopes: Optional list of scopes to request

        Returns:
            Authorization URL to redirect the user to
        """
        pass

    @abstractmethod
    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization request

        Returns:
            OAuth tokens including access token and optional refresh token
        """
        pass

    @abstractmethod
    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token to use

        Returns:
            New OAuth tokens
        """
        pass

    @abstractmethod
    async def revoke_token(
        self,
        access_token: str,
    ) -> bool:
        """
        Revoke an access token.

        Args:
            access_token: The token to revoke

        Returns:
            True if revocation was successful
        """
        pass

    # -------------------------------------------------------------------------
    # User/Account Methods
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_user_profile(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Get the authenticated user's profile information.

        Args:
            access_token: Valid access token

        Returns:
            User profile data including id, username, display name, etc.
        """
        pass

    async def verify_account(
        self,
        account: SocialAccount,
    ) -> bool:
        """
        Verify that an account connection is still valid.

        Args:
            account: The social account to verify

        Returns:
            True if the account connection is valid
        """
        try:
            await self.get_user_profile(account.access_token)
            return True
        except AuthenticationError:
            return False
        except Exception as e:
            self._logger.warning(f"Error verifying account: {e}")
            return False

    # -------------------------------------------------------------------------
    # Content Publishing Methods
    # -------------------------------------------------------------------------

    @abstractmethod
    async def publish_post(
        self,
        account: SocialAccount,
        content: PostContent,
    ) -> Tuple[str, str]:
        """
        Publish a post to the platform.

        Args:
            account: The social account to post from
            content: The content to publish

        Returns:
            Tuple of (platform_post_id, platform_post_url)
        """
        pass

    @abstractmethod
    async def delete_post(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> bool:
        """
        Delete a published post.

        Args:
            account: The social account that owns the post
            platform_post_id: The platform's ID for the post

        Returns:
            True if deletion was successful
        """
        pass

    async def upload_media(
        self,
        account: SocialAccount,
        media: MediaAttachment,
    ) -> str:
        """
        Upload media to the platform.

        Args:
            account: The social account to upload to
            media: The media attachment to upload

        Returns:
            Platform's media ID for the uploaded content

        Note:
            Default implementation raises NotImplementedError.
            Platforms that support media should override this method.
        """
        raise NotImplementedError(
            f"{self.platform.value} does not support direct media upload"
        )

    # -------------------------------------------------------------------------
    # Analytics Methods
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_post_analytics(
        self,
        account: SocialAccount,
        platform_post_id: str,
    ) -> PostAnalytics:
        """
        Get analytics for a published post.

        Args:
            account: The social account that owns the post
            platform_post_id: The platform's ID for the post

        Returns:
            PostAnalytics with engagement metrics
        """
        pass

    # -------------------------------------------------------------------------
    # Validation Methods
    # -------------------------------------------------------------------------

    def validate_content(
        self,
        content: PostContent,
    ) -> List[str]:
        """
        Validate content against platform requirements.

        Args:
            content: The content to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check text length
        if len(content.text) > self.config.max_text_length:
            errors.append(
                f"Text exceeds maximum length of {self.config.max_text_length} characters"
            )

        # Check media count
        if len(content.media) > self.config.max_media_count:
            errors.append(
                f"Too many media attachments. Maximum is {self.config.max_media_count}"
            )

        # Check required media
        if self.config.requires_media and not content.media:
            errors.append(f"{self.platform.value} requires at least one media attachment")

        # Check media types
        for media in content.media:
            if media.type not in self.config.supported_media_types:
                errors.append(
                    f"Media type '{media.type}' not supported. "
                    f"Supported types: {', '.join(self.config.supported_media_types)}"
                )

        return errors

    def truncate_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        ellipsis: str = "...",
    ) -> str:
        """
        Truncate text to fit platform limits.

        Args:
            text: The text to truncate
            max_length: Maximum length (defaults to platform limit)
            ellipsis: String to append when truncating

        Returns:
            Truncated text
        """
        max_len = max_length or self.config.max_text_length
        if len(text) <= max_len:
            return text
        return text[: max_len - len(ellipsis)] + ellipsis

    # -------------------------------------------------------------------------
    # Rate Limiting Methods
    # -------------------------------------------------------------------------

    async def check_rate_limit(
        self,
        account: SocialAccount,
    ) -> Dict[str, Any]:
        """
        Check current rate limit status for an account.

        Args:
            account: The social account to check

        Returns:
            Dictionary with rate limit info:
            - remaining: Requests remaining in current window
            - limit: Total requests allowed in window
            - reset_at: When the rate limit resets
        """
        # Default implementation returns unlimited
        # Platforms should override with actual rate limit checking
        return {
            "remaining": self.config.rate_limit_posts_per_hour,
            "limit": self.config.rate_limit_posts_per_hour,
            "reset_at": None,
        }

    def _handle_rate_limit_response(
        self,
        response_headers: Dict[str, str],
    ) -> None:
        """
        Handle rate limit headers from API response.

        Args:
            response_headers: HTTP response headers

        Raises:
            RateLimitError: If rate limited
        """
        # Common header names for rate limiting
        remaining = response_headers.get(
            "x-rate-limit-remaining",
            response_headers.get("ratelimit-remaining"),
        )
        reset = response_headers.get(
            "x-rate-limit-reset",
            response_headers.get("ratelimit-reset"),
        )

        if remaining is not None and int(remaining) <= 0:
            retry_after = 60  # Default
            if reset:
                try:
                    reset_time = datetime.fromtimestamp(int(reset))
                    retry_after = max(1, int((reset_time - datetime.utcnow()).total_seconds()))
                except (ValueError, OSError):
                    pass

            raise RateLimitError(
                message=f"Rate limit exceeded for {self.platform.value}",
                platform=self.platform,
                retry_after=retry_after,
            )
