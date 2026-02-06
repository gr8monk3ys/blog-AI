"""
Webhook management endpoints.

This module provides Zapier-compatible REST Hook endpoints for:
- Subscribing to webhook events
- Unsubscribing from webhooks
- Listing subscriptions
- Testing webhook delivery

Authorization:
- All endpoints require organization membership
- Creating/managing webhooks requires content.create permission
- Viewing webhooks requires content.view permission
"""

import logging
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.organizations import AuthorizationContext
from src.types.webhooks import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEventType,
    WebhookSubscription,
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookTestRequest,
    WebhookTestResponse,
)
from src.webhooks import webhook_service, webhook_storage

from ..auth import verify_api_key
from ..dependencies import require_content_access, require_content_creation
from ..error_handlers import sanitize_error_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/subscribe",
    status_code=status.HTTP_201_CREATED,
    response_model=WebhookSubscription,
    summary="Subscribe to webhook events",
    description="""
Register a webhook URL to receive event notifications.

**Supported Event Types:**
- `content.generated` - When content generation completes
- `content.published` - When content is published to a platform
- `batch.started` - When a batch job starts
- `batch.progress` - Progress updates for batch jobs
- `batch.completed` - When a batch job completes
- `batch.failed` - When a batch job fails
- `quota.warning` - When approaching quota limits
- `quota.exceeded` - When quota is exceeded

**Webhook Payload Format:**
```json
{
  "id": "evt_abc123",
  "event_type": "content.generated",
  "api_version": "2024-01-01",
  "created_at": "2024-01-15T10:30:00Z",
  "source": "blog-ai",
  "data": { ... event-specific data ... }
}
```

**Signature Verification:**
If you provide a `secret`, webhooks will include an `X-Webhook-Signature` header:
`t=timestamp,v1=signature`

Verify by computing HMAC-SHA256 of `{timestamp}.{payload}` using your secret.

**Authorization:** Requires content.create permission.
    """,
    responses={
        201: {"description": "Subscription created successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Subscription already exists for this URL"},
    },
)
async def subscribe_webhook(
    request: WebhookSubscriptionCreate,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> WebhookSubscription:
    """
    Subscribe to webhook events (Zapier REST Hook compatible).

    Args:
        request: Subscription creation request

    Returns:
        Created WebhookSubscription

    Authorization: Requires content.create permission.
    """
    # Use organization_id for scoping if available, fallback to user_id
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    logger.info(f"Webhook subscription request from user: {auth_ctx.user_id}, org: {auth_ctx.organization_id}")

    try:
        # Check for duplicate subscriptions to same URL for same events
        existing_subs = await webhook_storage.list_user_subscriptions(scope_id)
        for sub in existing_subs:
            if sub.target_url == request.target_url:
                # Check if event types overlap
                existing_events = set(sub.event_types)
                new_events = set(request.event_types)
                if existing_events & new_events:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Subscription already exists for URL {request.target_url} with overlapping events",
                    )

        # Create new subscription
        subscription = WebhookSubscription(
            id=str(uuid.uuid4()),
            user_id=scope_id,
            target_url=request.target_url,
            event_types=request.event_types,
            secret=request.secret,
            description=request.description,
            metadata=request.metadata,
        )

        # Save to storage
        saved = await webhook_storage.save_subscription(subscription)
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save subscription",
            )

        logger.info(f"Created webhook subscription {subscription.id} for user {auth_ctx.user_id} in org {auth_ctx.organization_id}")
        return subscription

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating webhook subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsubscribe from webhook events",
    description="""
Remove a webhook subscription. This is called by Zapier when a user disables a trigger.

**Authorization:** Requires content.create permission.
    """,
    responses={
        204: {"description": "Subscription deleted successfully"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def unsubscribe_webhook(
    subscription_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> None:
    """
    Unsubscribe from webhook events (Zapier REST Hook compatible).

    Args:
        subscription_id: ID of subscription to delete

    Authorization: Requires content.create permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    logger.info(f"Webhook unsubscribe request: {subscription_id} from user {auth_ctx.user_id}, org: {auth_ctx.organization_id}")

    # Verify ownership
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, scope_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    # Delete subscription
    deleted = await webhook_storage.delete_subscription(subscription_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subscription",
        )

    logger.info(f"Deleted webhook subscription {subscription_id}")


@router.get(
    "",
    response_model=Dict,
    summary="List webhook subscriptions",
    description="""
Get all webhook subscriptions for the authenticated user/organization.

**Authorization:** Requires content.view permission.
    """,
    responses={
        200: {"description": "List of subscriptions"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
    },
)
async def list_webhooks(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum subscriptions to return"),
    offset: int = Query(default=0, ge=0, description="Number of subscriptions to skip"),
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> Dict:
    """
    List all webhook subscriptions for the user/organization.

    Args:
        limit: Maximum number to return
        offset: Number to skip

    Returns:
        Paginated list of subscriptions

    Authorization: Requires content.view permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    subscriptions = await webhook_storage.list_user_subscriptions(
        user_id=scope_id,
        limit=limit,
        offset=offset,
    )

    # Get total count
    all_subs = await webhook_storage.list_user_subscriptions(scope_id, limit=1000)
    total = len(all_subs)

    return {
        "subscriptions": [s.model_dump() for s in subscriptions],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.get(
    "/{subscription_id}",
    response_model=WebhookSubscription,
    summary="Get webhook subscription details",
    description="""
Get details of a specific webhook subscription including delivery statistics.

**Authorization:** Requires content.view permission.
    """,
    responses={
        200: {"description": "Subscription details"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def get_webhook(
    subscription_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> WebhookSubscription:
    """
    Get a specific webhook subscription.

    Args:
        subscription_id: Subscription ID to retrieve

    Returns:
        WebhookSubscription details

    Authorization: Requires content.view permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, scope_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    return subscription


@router.patch(
    "/{subscription_id}",
    response_model=WebhookSubscription,
    summary="Update webhook subscription",
    description="""
Update an existing webhook subscription.

**Authorization:** Requires content.create permission.
    """,
    responses={
        200: {"description": "Subscription updated"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def update_webhook(
    subscription_id: str,
    request: WebhookSubscriptionUpdate,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> WebhookSubscription:
    """
    Update a webhook subscription.

    Args:
        subscription_id: Subscription ID to update
        request: Fields to update

    Returns:
        Updated WebhookSubscription

    Authorization: Requires content.create permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    # Verify ownership
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, scope_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    # Build updates dict (only non-None values)
    updates = {}
    if request.target_url is not None:
        updates["target_url"] = request.target_url
    if request.event_types is not None:
        updates["event_types"] = request.event_types
    if request.secret is not None:
        updates["secret"] = request.secret
    if request.is_active is not None:
        updates["is_active"] = request.is_active
    if request.description is not None:
        updates["description"] = request.description
    if request.metadata is not None:
        updates["metadata"] = request.metadata

    if not updates:
        return subscription

    # Apply updates
    updated = await webhook_storage.update_subscription(subscription_id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription",
        )

    # Return updated subscription
    return await webhook_storage.get_subscription(subscription_id)


@router.post(
    "/test",
    response_model=WebhookTestResponse,
    summary="Test webhook delivery",
    description="""
Send a test webhook to verify endpoint configuration.

You can either:
1. Provide a `subscription_id` to test an existing subscription
2. Provide a `target_url` to test a URL directly

The test sends a sample payload and reports the response.

**Authorization:** Requires content.create permission.
    """,
    responses={
        200: {"description": "Test completed (check success field)"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def test_webhook(
    request: WebhookTestRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> WebhookTestResponse:
    """
    Test a webhook endpoint.

    Args:
        request: Test request with either subscription_id or target_url

    Returns:
        WebhookTestResponse with results

    Authorization: Requires content.create permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    target_url: str
    secret: Optional[str] = None

    if request.subscription_id:
        # Test existing subscription
        subscription = await webhook_storage.get_subscription_if_owned(
            request.subscription_id, scope_id
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {request.subscription_id} not found",
            )
        target_url = subscription.target_url
        secret = subscription.secret
    elif request.target_url:
        # Test direct URL
        target_url = request.target_url
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either subscription_id or target_url must be provided",
        )

    logger.info(f"Testing webhook delivery to {target_url}")

    try:
        delivery = await webhook_service.test_webhook(target_url, secret)

        return WebhookTestResponse(
            success=(delivery.status == DeliveryStatus.DELIVERED),
            delivery_id=delivery.id,
            status_code=delivery.response_status_code,
            response_time_ms=delivery.duration_ms,
            error=delivery.error_message,
        )

    except Exception as e:
        logger.error(f"Webhook test failed: {str(e)}", exc_info=True)
        return WebhookTestResponse(
            success=False,
            delivery_id=str(uuid.uuid4()),
            error=sanitize_error_message(str(e)),
        )


@router.get(
    "/events/types",
    response_model=Dict,
    summary="List available event types",
    description="Get a list of all webhook event types that can be subscribed to.",
    responses={
        200: {"description": "List of event types"},
    },
)
async def list_event_types() -> Dict:
    """
    List all available webhook event types.

    Returns:
        Dictionary with event types and descriptions
    """
    event_types = [
        {
            "type": WebhookEventType.CONTENT_GENERATED.value,
            "description": "Triggered when content generation completes",
            "data_fields": ["content_type", "content_id", "title", "word_count"],
        },
        {
            "type": WebhookEventType.CONTENT_PUBLISHED.value,
            "description": "Triggered when content is published to a platform",
            "data_fields": ["content_type", "content_id", "platform", "url"],
        },
        {
            "type": WebhookEventType.BATCH_STARTED.value,
            "description": "Triggered when a batch job starts processing",
            "data_fields": ["job_id", "total_items"],
        },
        {
            "type": WebhookEventType.BATCH_PROGRESS.value,
            "description": "Progress updates during batch processing",
            "data_fields": ["job_id", "completed", "total", "percentage"],
        },
        {
            "type": WebhookEventType.BATCH_COMPLETED.value,
            "description": "Triggered when a batch job completes",
            "data_fields": ["job_id", "total_items", "completed_items", "failed_items"],
        },
        {
            "type": WebhookEventType.BATCH_FAILED.value,
            "description": "Triggered when a batch job fails",
            "data_fields": ["job_id", "error"],
        },
        {
            "type": WebhookEventType.QUOTA_WARNING.value,
            "description": "Triggered when approaching quota limits (80%+)",
            "data_fields": ["usage_percentage", "current_usage", "quota_limit"],
        },
        {
            "type": WebhookEventType.QUOTA_EXCEEDED.value,
            "description": "Triggered when quota is exceeded",
            "data_fields": ["current_usage", "quota_limit"],
        },
    ]

    return {
        "event_types": event_types,
        "total": len(event_types),
    }


@router.post(
    "/{subscription_id}/activate",
    response_model=WebhookSubscription,
    summary="Activate a webhook subscription",
    description="""
Re-activate a paused webhook subscription.

**Authorization:** Requires content.create permission.
    """,
    responses={
        200: {"description": "Subscription activated"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def activate_webhook(
    subscription_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> WebhookSubscription:
    """
    Activate a webhook subscription.

    Args:
        subscription_id: Subscription to activate

    Returns:
        Updated WebhookSubscription

    Authorization: Requires content.create permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, scope_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    await webhook_storage.update_subscription(subscription_id, {"is_active": True})
    return await webhook_storage.get_subscription(subscription_id)


@router.post(
    "/{subscription_id}/deactivate",
    response_model=WebhookSubscription,
    summary="Deactivate a webhook subscription",
    description="""
Pause a webhook subscription without deleting it.

**Authorization:** Requires content.create permission.
    """,
    responses={
        200: {"description": "Subscription deactivated"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Subscription not found"},
    },
)
async def deactivate_webhook(
    subscription_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> WebhookSubscription:
    """
    Deactivate a webhook subscription.

    Args:
        subscription_id: Subscription to deactivate

    Returns:
        Updated WebhookSubscription

    Authorization: Requires content.create permission.
    """
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, scope_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    await webhook_storage.update_subscription(subscription_id, {"is_active": False})
    return await webhook_storage.get_subscription(subscription_id)
