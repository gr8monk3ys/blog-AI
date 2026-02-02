"""
Social media scheduling and publishing endpoints.

Provides API endpoints for:
- Connecting social media accounts (OAuth flow)
- Scheduling posts for future publishing
- Managing multi-platform campaigns
- Getting optimal posting times
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.social import campaign_service, publisher_service, scheduler_service
from src.social.platforms.base import AuthenticationError, PlatformError, RateLimitError
from src.social.platforms.linkedin import linkedin_platform
from src.social.platforms.twitter import twitter_platform
from src.types.social import (
    CampaignStatus,
    ConnectAccountRequest,
    ConnectAccountResponse,
    CreateCampaignRequest,
    CreateCampaignResponse,
    DeleteResponse,
    ListAccountsResponse,
    ListCampaignsResponse,
    ListScheduledPostsResponse,
    PostContent,
    PostStatus,
    SchedulePostRequest,
    SchedulePostResponse,
    SocialAccount,
    SocialConnection,
    SocialPlatform,
    UpdateScheduledPostRequest,
)

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social"])


# =============================================================================
# Account Management Endpoints
# =============================================================================


@router.get(
    "/accounts",
    response_model=ListAccountsResponse,
    responses={
        500: {"description": "Internal server error"},
    },
)
async def list_connected_accounts(
    user_id: str = Depends(verify_api_key),
) -> ListAccountsResponse:
    """
    List all connected social media accounts.

    Returns all active social accounts connected by the authenticated user.
    """
    try:
        accounts = await scheduler_service.list_user_accounts(user_id)

        connections = [
            SocialConnection(
                id=account.id,
                platform=account.platform,
                platform_username=account.platform_username,
                display_name=account.display_name,
                profile_image_url=account.profile_image_url,
                is_active=account.is_active,
                connected_at=account.created_at,
            )
            for account in accounts
        ]

        return ListAccountsResponse(success=True, accounts=connections)

    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to list accounts", "success": False},
        )


@router.post(
    "/accounts/connect/{platform}",
    response_model=ConnectAccountResponse,
    responses={
        400: {"description": "Platform not supported or not configured"},
        500: {"description": "Failed to generate authorization URL"},
    },
)
async def connect_account(
    platform: SocialPlatform,
    request: ConnectAccountRequest,
    user_id: str = Depends(verify_api_key),
) -> ConnectAccountResponse:
    """
    Start OAuth flow to connect a social media account.

    Returns an authorization URL that the user should be redirected to.
    After authorization, the user will be redirected back to the callback URL.
    """
    try:
        # Generate state token for CSRF protection
        state_token = secrets.token_urlsafe(32)

        # Get platform instance
        if platform == SocialPlatform.TWITTER:
            platform_client = twitter_platform
        elif platform == SocialPlatform.LINKEDIN:
            platform_client = linkedin_platform
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Platform {platform.value} not supported for direct OAuth",
                    "success": False,
                },
            )

        if not platform_client.is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"{platform.value} credentials not configured",
                    "success": False,
                },
            )

        # Generate authorization URL
        auth_url = await platform_client.get_authorization_url(
            redirect_uri=request.redirect_uri,
            state=state_token,
        )

        logger.info(f"Generated OAuth URL for {platform.value} (user: {user_id[:8]}...)")

        return ConnectAccountResponse(
            success=True,
            authorization_url=auth_url,
            state=state_token,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to generate authorization URL", "success": False},
        )


@router.get(
    "/accounts/callback/{platform}",
    responses={
        400: {"description": "Invalid callback parameters"},
        500: {"description": "Failed to exchange code"},
    },
)
async def oauth_callback(
    platform: SocialPlatform,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="State token for CSRF protection"),
    redirect_uri: str = Query(..., description="Redirect URI used in authorization"),
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Handle OAuth callback from social platform.

    Exchanges the authorization code for access tokens and creates the account.
    """
    try:
        # Get platform instance
        if platform == SocialPlatform.TWITTER:
            platform_client = twitter_platform
        elif platform == SocialPlatform.LINKEDIN:
            platform_client = linkedin_platform
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Platform {platform.value} not supported", "success": False},
            )

        # Exchange code for tokens
        tokens = await platform_client.exchange_code_for_tokens(
            code=code,
            redirect_uri=redirect_uri,
        )

        # Get user profile
        profile = await platform_client.get_user_profile(tokens.access_token)

        # Create account
        import uuid

        account = SocialAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=platform,
            platform_user_id=profile["id"],
            platform_username=profile["username"],
            display_name=profile.get("display_name"),
            profile_image_url=profile.get("profile_image_url"),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_expires_at=tokens.expires_at,
        )

        # Store account
        await scheduler_service.store_account(account)

        logger.info(
            f"Connected {platform.value} account {profile['username']} for user {user_id[:8]}..."
        )

        return {
            "success": True,
            "account": {
                "id": account.id,
                "platform": account.platform.value,
                "username": account.platform_username,
                "display_name": account.display_name,
            },
        }

    except AuthenticationError as e:
        logger.error(f"OAuth authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": sanitize_error_message(str(e)), "success": False},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to complete OAuth flow", "success": False},
        )


@router.delete(
    "/accounts/{account_id}",
    response_model=DeleteResponse,
    responses={
        404: {"description": "Account not found"},
        500: {"description": "Failed to disconnect account"},
    },
)
async def disconnect_account(
    account_id: str,
    user_id: str = Depends(verify_api_key),
) -> DeleteResponse:
    """
    Disconnect a social media account.

    This revokes access tokens and removes the account connection.
    Scheduled posts for this account will be cancelled.
    """
    try:
        account = await scheduler_service.get_account(account_id)

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Account not found", "success": False},
            )

        if account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Account not found", "success": False},
            )

        # Revoke tokens
        try:
            if account.platform == SocialPlatform.TWITTER:
                await twitter_platform.revoke_token(account.access_token)
            elif account.platform == SocialPlatform.LINKEDIN:
                await linkedin_platform.revoke_token(account.access_token)
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")

        # Mark account as inactive
        account.is_active = False
        account.updated_at = datetime.utcnow()
        await scheduler_service.store_account(account)

        logger.info(f"Disconnected account {account_id} for user {user_id[:8]}...")

        return DeleteResponse(
            success=True,
            message=f"Disconnected {account.platform.value} account",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to disconnect account", "success": False},
        )


# =============================================================================
# Post Scheduling Endpoints
# =============================================================================


@router.post(
    "/posts/schedule",
    response_model=SchedulePostResponse,
    responses={
        400: {"description": "Invalid request"},
        404: {"description": "Account not found"},
        500: {"description": "Failed to schedule post"},
    },
)
async def schedule_post(
    request: SchedulePostRequest,
    user_id: str = Depends(verify_api_key),
) -> SchedulePostResponse:
    """
    Schedule a post for future publishing.

    The post will be automatically published at the scheduled time.
    """
    try:
        post = await scheduler_service.schedule_post(
            user_id=user_id,
            account_id=request.account_id,
            content=request.content,
            scheduled_at=request.scheduled_at,
            recurrence=request.recurrence,
            recurrence_end_date=request.recurrence_end_date,
            campaign_id=request.campaign_id,
            source_content_id=request.source_content_id,
        )

        logger.info(f"Scheduled post {post.id} for {post.scheduled_at}")

        return SchedulePostResponse(success=True, post=post)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "success": False},
        )
    except Exception as e:
        logger.error(f"Error scheduling post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to schedule post", "success": False},
        )


@router.get(
    "/posts/scheduled",
    response_model=ListScheduledPostsResponse,
    responses={
        500: {"description": "Failed to list posts"},
    },
)
async def list_scheduled_posts(
    status_filter: Optional[PostStatus] = Query(None, alias="status"),
    platform: Optional[SocialPlatform] = None,
    account_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(verify_api_key),
) -> ListScheduledPostsResponse:
    """
    List scheduled posts with optional filters.
    """
    try:
        posts, total = await scheduler_service.list_scheduled_posts(
            user_id=user_id,
            status=status_filter,
            platform=platform,
            account_id=account_id,
            campaign_id=campaign_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        return ListScheduledPostsResponse(
            success=True,
            posts=posts,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error listing scheduled posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to list scheduled posts", "success": False},
        )


@router.patch(
    "/posts/{post_id}",
    response_model=SchedulePostResponse,
    responses={
        400: {"description": "Invalid request or post cannot be updated"},
        404: {"description": "Post not found"},
        500: {"description": "Failed to update post"},
    },
)
async def update_scheduled_post(
    post_id: str,
    request: UpdateScheduledPostRequest,
    user_id: str = Depends(verify_api_key),
) -> SchedulePostResponse:
    """
    Update a scheduled post.

    Can only update posts that haven't been published yet.
    """
    try:
        post = await scheduler_service.update_scheduled_post(
            post_id=post_id,
            user_id=user_id,
            content=request.content,
            scheduled_at=request.scheduled_at,
            recurrence=request.recurrence,
            recurrence_end_date=request.recurrence_end_date,
        )

        logger.info(f"Updated scheduled post {post_id}")

        return SchedulePostResponse(success=True, post=post)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error updating scheduled post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to update post", "success": False},
        )


@router.delete(
    "/posts/{post_id}",
    response_model=DeleteResponse,
    responses={
        400: {"description": "Post cannot be cancelled"},
        404: {"description": "Post not found"},
        500: {"description": "Failed to cancel post"},
    },
)
async def cancel_scheduled_post(
    post_id: str,
    user_id: str = Depends(verify_api_key),
) -> DeleteResponse:
    """
    Cancel a scheduled post.

    Can only cancel posts that haven't been published yet.
    """
    try:
        await scheduler_service.cancel_scheduled_post(post_id, user_id)

        logger.info(f"Cancelled scheduled post {post_id}")

        return DeleteResponse(success=True, message="Post cancelled successfully")

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error cancelling post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to cancel post", "success": False},
        )


# =============================================================================
# Campaign Endpoints
# =============================================================================


@router.post(
    "/campaigns",
    response_model=CreateCampaignResponse,
    responses={
        400: {"description": "Invalid request"},
        500: {"description": "Failed to create campaign"},
    },
)
async def create_campaign(
    request: CreateCampaignRequest,
    user_id: str = Depends(verify_api_key),
) -> CreateCampaignResponse:
    """
    Create a multi-platform campaign.

    Creates scheduled posts for each configured platform with optional
    time offsets between platforms.
    """
    try:
        campaign, posts = await campaign_service.create_campaign(
            user_id=user_id,
            name=request.name,
            content=request.content,
            platforms=request.platforms,
            scheduled_at=request.scheduled_at,
            description=request.description,
            recurrence=request.recurrence,
            recurrence_end_date=request.recurrence_end_date,
            tags=request.tags,
            source_content_id=request.source_content_id,
        )

        logger.info(f"Created campaign {campaign.id} with {len(posts)} posts")

        return CreateCampaignResponse(
            success=True,
            campaign=campaign,
            scheduled_posts=posts,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "success": False},
        )
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create campaign", "success": False},
        )


@router.get(
    "/campaigns",
    response_model=ListCampaignsResponse,
    responses={
        500: {"description": "Failed to list campaigns"},
    },
)
async def list_campaigns(
    status_filter: Optional[CampaignStatus] = Query(None, alias="status"),
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(verify_api_key),
) -> ListCampaignsResponse:
    """
    List campaigns with optional filters.
    """
    try:
        campaigns, total = await campaign_service.list_campaigns(
            user_id=user_id,
            status=status_filter,
            tag=tag,
            page=page,
            page_size=page_size,
        )

        return ListCampaignsResponse(
            success=True,
            campaigns=campaigns,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to list campaigns", "success": False},
        )


@router.get(
    "/campaigns/{campaign_id}",
    responses={
        404: {"description": "Campaign not found"},
        500: {"description": "Failed to get campaign"},
    },
)
async def get_campaign(
    campaign_id: str,
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Get a campaign by ID with its posts.
    """
    try:
        campaign = await campaign_service.get_campaign(campaign_id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Campaign not found", "success": False},
            )

        if campaign.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Campaign not found", "success": False},
            )

        posts = await campaign_service.get_campaign_posts(campaign_id, user_id)

        return {
            "success": True,
            "campaign": campaign.model_dump(),
            "posts": [p.model_dump() for p in posts],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get campaign", "success": False},
        )


@router.post(
    "/campaigns/{campaign_id}/pause",
    responses={
        400: {"description": "Campaign cannot be paused"},
        404: {"description": "Campaign not found"},
        500: {"description": "Failed to pause campaign"},
    },
)
async def pause_campaign(
    campaign_id: str,
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Pause an active campaign.

    All pending scheduled posts will be cancelled.
    """
    try:
        campaign = await campaign_service.pause_campaign(campaign_id, user_id)

        return {"success": True, "campaign": campaign.model_dump()}

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error pausing campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to pause campaign", "success": False},
        )


@router.post(
    "/campaigns/{campaign_id}/resume",
    responses={
        400: {"description": "Campaign cannot be resumed"},
        404: {"description": "Campaign not found"},
        500: {"description": "Failed to resume campaign"},
    },
)
async def resume_campaign(
    campaign_id: str,
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Resume a paused campaign.

    New scheduled posts will be created with updated times.
    """
    try:
        campaign = await campaign_service.resume_campaign(campaign_id, user_id)

        return {"success": True, "campaign": campaign.model_dump()}

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error resuming campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to resume campaign", "success": False},
        )


@router.delete(
    "/campaigns/{campaign_id}",
    response_model=DeleteResponse,
    responses={
        400: {"description": "Campaign cannot be cancelled"},
        404: {"description": "Campaign not found"},
        500: {"description": "Failed to cancel campaign"},
    },
)
async def cancel_campaign(
    campaign_id: str,
    user_id: str = Depends(verify_api_key),
) -> DeleteResponse:
    """
    Cancel a campaign entirely.

    All scheduled posts will be cancelled.
    """
    try:
        await campaign_service.cancel_campaign(campaign_id, user_id)

        return DeleteResponse(success=True, message="Campaign cancelled successfully")

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error cancelling campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to cancel campaign", "success": False},
        )


@router.get(
    "/campaigns/{campaign_id}/analytics",
    responses={
        404: {"description": "Campaign not found"},
        500: {"description": "Failed to get analytics"},
    },
)
async def get_campaign_analytics(
    campaign_id: str,
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Get aggregated analytics for a campaign.
    """
    try:
        analytics = await campaign_service.get_campaign_analytics(campaign_id, user_id)

        return {"success": True, "analytics": analytics.model_dump()}

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": error_msg, "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_msg, "success": False},
        )
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get analytics", "success": False},
        )


# =============================================================================
# Optimal Times Endpoint
# =============================================================================


@router.get(
    "/optimal-times",
    responses={
        500: {"description": "Failed to get optimal times"},
    },
)
async def get_optimal_times(
    platforms: Optional[str] = Query(
        None,
        description="Comma-separated list of platforms (e.g., 'twitter,linkedin')",
    ),
    timezone: str = Query("UTC", description="Timezone for recommendations"),
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Get optimal posting times for connected platforms.

    Returns recommended posting times based on engagement analysis
    and industry best practices.
    """
    try:
        # Parse platforms
        platform_list = None
        if platforms:
            platform_list = [
                SocialPlatform(p.strip())
                for p in platforms.split(",")
                if p.strip()
            ]

        response = await scheduler_service.get_optimal_times(
            user_id=user_id,
            platforms=platform_list,
            timezone=timezone,
        )

        return {"success": True, **response.model_dump()}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "success": False},
        )
    except Exception as e:
        logger.error(f"Error getting optimal times: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to get optimal times", "success": False},
        )


@router.get(
    "/suggest-time",
    responses={
        400: {"description": "Invalid platform"},
        500: {"description": "Failed to suggest time"},
    },
)
async def suggest_next_time(
    platform: SocialPlatform,
    after: Optional[datetime] = Query(None, description="Suggest time after this datetime"),
    user_id: str = Depends(verify_api_key),
) -> dict:
    """
    Suggest the next optimal time to post.

    Returns a specific datetime recommendation for posting.
    """
    try:
        suggested_time = await scheduler_service.suggest_next_time(
            user_id=user_id,
            platform=platform,
            after=after,
        )

        return {
            "success": True,
            "platform": platform.value,
            "suggested_time": suggested_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error suggesting time: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to suggest time", "success": False},
        )
