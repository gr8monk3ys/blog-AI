"""
Quota enforcement middleware and dependency for FastAPI.

Provides a dependency that checks user quota before allowing
generation endpoints to proceed. Returns 429 Too Many Requests
when quota is exceeded.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from src.types.usage import QuotaExceededError, SubscriptionTier
from src.usage.quota_service import (
    QuotaExceeded,
    check_quota as service_check_quota,
    get_usage_stats as service_get_usage_stats,
    increment_usage as service_increment_usage,
    get_quota_service,
)

from ..auth import verify_api_key

logger = logging.getLogger(__name__)


class QuotaCheckError(HTTPException):
    """Exception raised when quota check fails."""

    def __init__(self, error: QuotaExceededError):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error.model_dump(),
            headers={"Retry-After": "3600"},  # Suggest retry after 1 hour
        )


async def require_quota(user_id: str = Depends(verify_api_key)) -> str:
    """
    FastAPI dependency that enforces quota limits.

    This dependency should be added to generation endpoints to ensure
    users cannot exceed their subscription limits.

    Args:
        user_id: The authenticated user ID from API key verification.

    Returns:
        The user_id if quota check passes.

    Raises:
        HTTPException: 429 Too Many Requests if quota is exceeded.

    Usage:
        @router.post("/generate-blog")
        async def generate_blog(
            request: BlogRequest,
            user_id: str = Depends(require_quota)
        ):
            # Will only reach here if user has remaining quota
            ...
    """
    try:
        await service_check_quota(user_id)
        logger.debug(f"Quota check passed for user: {user_id[:8]}...")
        return user_id

    except QuotaExceeded as e:
        logger.warning(
            f"Quota exceeded for user {user_id[:8]}...: "
            f"{e.current_usage}/{e.quota_limit} ({e.tier.value})"
        )
        raise QuotaCheckError(e.to_error_response())


async def check_quota_soft(user_id: str = Depends(verify_api_key)) -> tuple[str, bool]:
    """
    Soft quota check that returns status instead of raising exception.

    Useful for endpoints that want to warn users about quota status
    without blocking the request.

    Args:
        user_id: The authenticated user ID.

    Returns:
        Tuple of (user_id, has_quota).
    """
    try:
        await service_check_quota(user_id)
        return user_id, True
    except QuotaExceeded:
        return user_id, False


class QuotaTracker:
    """
    Context manager for tracking quota usage around generation operations.

    Automatically increments usage after successful operation and
    handles errors gracefully.

    Usage:
        async with QuotaTracker(user_id, "blog") as tracker:
            result = await generate_blog(...)
            tracker.tokens_used = 5000  # Optional: track token usage
        # Usage automatically incremented after successful completion
    """

    def __init__(
        self,
        user_id: str,
        operation_type: str,
        metadata: Optional[dict] = None,
    ):
        self.user_id = user_id
        self.operation_type = operation_type
        self.metadata = metadata or {}
        self.tokens_used = 0
        self._success = False

    async def __aenter__(self) -> "QuotaTracker":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            # Operation succeeded, increment usage
            self._success = True
            try:
                await service_increment_usage(
                    user_id=self.user_id,
                    operation_type=self.operation_type,
                    tokens_used=self.tokens_used,
                    metadata=self.metadata,
                )
                logger.info(
                    f"Usage incremented for {self.user_id[:8]}...: "
                    f"{self.operation_type} ({self.tokens_used} tokens)"
                )
            except Exception as e:
                # Log but don't fail the request if usage tracking fails
                logger.error(f"Failed to increment usage: {e}")

        return False  # Don't suppress exceptions


async def get_quota_status(user_id: str = Depends(verify_api_key)) -> dict:
    """
    Get current quota status for the user.

    Returns a summary suitable for including in API responses.

    Args:
        user_id: The authenticated user ID.

    Returns:
        Dictionary with quota status information.
    """
    stats = await service_get_usage_stats(user_id)

    return {
        "tier": stats.tier.value,
        "current_usage": stats.current_usage,
        "quota_limit": stats.quota_limit,
        "remaining": stats.remaining,
        "percentage_used": stats.percentage_used,
        "is_quota_exceeded": stats.is_quota_exceeded,
        "reset_date": stats.reset_date.isoformat(),
    }


async def increment_usage_for_operation(
    user_id: str,
    operation_type: str,
    tokens_used: int = 0,
    metadata: Optional[dict] = None,
) -> None:
    """
    Increment usage counter for a completed operation.

    Call this after a successful generation operation.

    Args:
        user_id: The user identifier.
        operation_type: Type of operation (blog, book, batch, remix, tool).
        tokens_used: Number of tokens consumed.
        metadata: Additional metadata about the operation.
    """
    try:
        await service_increment_usage(
            user_id=user_id,
            operation_type=operation_type,
            tokens_used=tokens_used,
            metadata=metadata,
        )
    except Exception as e:
        # Log but don't fail the request
        logger.error(f"Failed to increment usage: {e}")


def create_quota_check_for_tier(min_tier: SubscriptionTier):
    """
    Factory function to create tier-specific quota checks.

    Args:
        min_tier: Minimum subscription tier required for the endpoint.

    Returns:
        Dependency function that checks both quota and tier.

    Usage:
        @router.post("/batch/jobs")
        async def create_batch_job(
            request: BatchRequest,
            user_id: str = Depends(create_quota_check_for_tier(SubscriptionTier.PRO))
        ):
            ...
    """
    tier_order = [
        SubscriptionTier.FREE,
        SubscriptionTier.STARTER,
        SubscriptionTier.PRO,
        SubscriptionTier.BUSINESS,
    ]

    async def check_tier_and_quota(user_id: str = Depends(verify_api_key)) -> str:
        """Check that user has required tier and quota."""
        # First check quota (which also validates tier)
        try:
            await service_check_quota(user_id)
        except QuotaExceeded as e:
            raise QuotaCheckError(e.to_error_response())

        # Then check tier level
        stats = await service_get_usage_stats(user_id)
        user_tier_index = tier_order.index(stats.tier) if stats.tier in tier_order else 0
        min_tier_index = tier_order.index(min_tier) if min_tier in tier_order else 0

        if user_tier_index < min_tier_index:
            from src.types.usage import get_tier_config
            min_config = get_tier_config(min_tier)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"This feature requires {min_config.name} tier or higher",
                    "error_code": "TIER_REQUIRED",
                    "current_tier": stats.tier.value,
                    "required_tier": min_tier.value,
                    "upgrade_url": "/pricing",
                },
            )

        return user_id

    return check_tier_and_quota


# Pre-built tier check dependencies
require_starter_tier = create_quota_check_for_tier(SubscriptionTier.STARTER)
require_pro_tier = create_quota_check_for_tier(SubscriptionTier.PRO)
require_business_tier = create_quota_check_for_tier(SubscriptionTier.BUSINESS)
