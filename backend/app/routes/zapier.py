"""
Zapier-specific trigger and action endpoints.

This module provides Zapier App integration endpoints:
- Polling triggers for content events
- Actions for generating content
- Authentication test endpoint

These endpoints follow Zapier's API requirements for triggers and actions.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from functools import partial
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from src.blog.make_blog import (
    BlogGenerationError,
    generate_blog_post,
    generate_blog_post_with_research,
)
from src.text_generation.core import GenerationOptions, RateLimitError, TextGenerationError
from src.types.webhooks import (
    WebhookEventType,
    WebhookSubscription,
    ZapierGenerateRequest,
    ZapierGenerateResponse,
    ZapierSubscribeRequest,
    ZapierSubscribeResponse,
    ZapierTriggerItem,
)
from src.webhooks import webhook_service, webhook_storage

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zapier", tags=["zapier"])


# =============================================================================
# Authentication Test Endpoint
# =============================================================================


@router.get(
    "/me",
    response_model=Dict,
    summary="Test authentication",
    description="""
Zapier uses this endpoint to verify API key validity during connection setup.

Returns basic account information if authentication succeeds.
    """,
    responses={
        200: {"description": "Authentication successful"},
        401: {"description": "Invalid API key"},
    },
)
async def test_authentication(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Test API key authentication for Zapier.

    This endpoint is called by Zapier to verify the API key when
    a user connects their account.

    Args:
        user_id: Authenticated user ID

    Returns:
        Basic account information
    """
    return {
        "authenticated": True,
        "user_id": user_id,
        "platform": "Blog AI",
        "api_version": "v1",
    }


# =============================================================================
# Polling Triggers
# =============================================================================


@router.get(
    "/triggers/new-content",
    response_model=List[ZapierTriggerItem],
    summary="Polling trigger: New content",
    description="""
Returns recently generated content for Zapier polling trigger.

Zapier calls this endpoint periodically to check for new content.
Results are sorted newest first and include an `id` field for deduplication.

**Important:** This is a polling trigger, not a webhook. For real-time
notifications, use the REST Hook subscription endpoints instead.
    """,
    responses={
        200: {"description": "List of recent content items"},
        401: {"description": "Invalid API key"},
    },
)
async def trigger_new_content(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum items to return"),
    user_id: str = Depends(verify_api_key),
) -> List[ZapierTriggerItem]:
    """
    Zapier polling trigger for new content.

    Returns recent content generation events for the user.
    Results are ordered newest first for proper Zapier deduplication.

    Args:
        limit: Maximum items to return
        user_id: Authenticated user ID

    Returns:
        List of content items in Zapier trigger format
    """
    # Get recent events from webhook storage
    events = await webhook_storage.get_recent_events(user_id, limit=limit)

    # Filter to content events only
    content_events = [
        e for e in events
        if e.get("event_type") in [
            WebhookEventType.CONTENT_GENERATED.value,
            WebhookEventType.CONTENT_PUBLISHED.value,
        ]
    ]

    # Convert to Zapier trigger format
    items: List[ZapierTriggerItem] = []
    for event in content_events:
        items.append(
            ZapierTriggerItem(
                id=event.get("id", str(uuid.uuid4())),
                created_at=event.get("created_at", datetime.utcnow().isoformat()),
                type=event.get("content_type", "blog"),
                title=event.get("title", "Untitled"),
                description=event.get("description"),
                word_count=event.get("word_count"),
                url=event.get("url"),
                metadata={
                    k: v for k, v in event.items()
                    if k not in ["id", "created_at", "content_type", "title", "description", "word_count", "url"]
                },
            )
        )

    return items


@router.get(
    "/triggers/batch-complete",
    response_model=List[Dict],
    summary="Polling trigger: Batch complete",
    description="""
Returns recently completed batch jobs for Zapier polling trigger.

Zapier calls this endpoint periodically to check for completed batches.
    """,
    responses={
        200: {"description": "List of completed batch jobs"},
        401: {"description": "Invalid API key"},
    },
)
async def trigger_batch_complete(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(verify_api_key),
) -> List[Dict]:
    """
    Zapier polling trigger for batch completion.

    Args:
        limit: Maximum items to return
        user_id: Authenticated user ID

    Returns:
        List of completed batch jobs
    """
    events = await webhook_storage.get_recent_events(user_id, limit=limit)

    # Filter to batch completion events
    batch_events = [
        e for e in events
        if e.get("event_type") == WebhookEventType.BATCH_COMPLETED.value
    ]

    # Format for Zapier
    return [
        {
            "id": e.get("id", str(uuid.uuid4())),
            "job_id": e.get("job_id"),
            "total_items": e.get("total_items", 0),
            "completed_items": e.get("completed_items", 0),
            "failed_items": e.get("failed_items", 0),
            "success_rate": e.get("success_rate", 0),
            "total_cost_usd": e.get("total_cost_usd"),
            "completed_at": e.get("completed_at", e.get("created_at")),
        }
        for e in batch_events
    ]


# =============================================================================
# REST Hook Subscriptions (for Zapier REST Hook triggers)
# =============================================================================


@router.post(
    "/hooks/subscribe/{event_type}",
    response_model=ZapierSubscribeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to REST Hook",
    description="""
Zapier calls this endpoint when a user enables a trigger using REST Hooks.

This is the subscription endpoint for Zapier's REST Hook implementation.
Zapier will send the `hookUrl` in the request body.
    """,
    responses={
        201: {"description": "Subscription created"},
        401: {"description": "Invalid API key"},
    },
)
async def zapier_subscribe(
    event_type: str,
    request: ZapierSubscribeRequest,
    user_id: str = Depends(verify_api_key),
) -> ZapierSubscribeResponse:
    """
    Subscribe to REST Hook events (Zapier integration).

    Args:
        event_type: Event type to subscribe to (from URL path)
        request: Zapier subscription request with hookUrl
        user_id: Authenticated user ID

    Returns:
        Subscription ID for unsubscribe
    """
    # Validate event type
    try:
        webhook_event_type = WebhookEventType(event_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_type}",
        )

    # Create subscription
    subscription = WebhookSubscription(
        id=str(uuid.uuid4()),
        user_id=user_id,
        target_url=request.target_url,
        event_types=[webhook_event_type],
        description=f"Zapier REST Hook for {event_type}",
        metadata={"source": "zapier", "event_type": event_type},
    )

    await webhook_storage.save_subscription(subscription)
    logger.info(f"Zapier REST Hook subscription created: {subscription.id}")

    return ZapierSubscribeResponse(id=subscription.id)


@router.delete(
    "/hooks/unsubscribe/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsubscribe from REST Hook",
    description="Zapier calls this endpoint when a user disables a trigger.",
    responses={
        204: {"description": "Subscription deleted"},
        401: {"description": "Invalid API key"},
        404: {"description": "Subscription not found"},
    },
)
async def zapier_unsubscribe(
    subscription_id: str,
    user_id: str = Depends(verify_api_key),
) -> None:
    """
    Unsubscribe from REST Hook events (Zapier integration).

    Args:
        subscription_id: Subscription ID to delete
        user_id: Authenticated user ID
    """
    subscription = await webhook_storage.get_subscription_if_owned(subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    await webhook_storage.delete_subscription(subscription_id)
    logger.info(f"Zapier REST Hook subscription deleted: {subscription_id}")


# =============================================================================
# Actions
# =============================================================================


async def _generate_content_async(
    request: ZapierGenerateRequest,
    user_id: str,
    job_id: str,
) -> None:
    """
    Background task to generate content and emit webhook.

    Args:
        request: Generation request
        user_id: User who requested generation
        job_id: Job ID for tracking
    """
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
        )

        # Generate content
        if request.research:
            blog_post = await asyncio.to_thread(
                partial(
                    generate_blog_post_with_research,
                    title=request.topic,
                    keywords=request.keywords or [],
                    tone=request.tone,
                    provider_type="openai",
                    options=options,
                )
            )
        else:
            blog_post = await asyncio.to_thread(
                partial(
                    generate_blog_post,
                    title=request.topic,
                    keywords=request.keywords or [],
                    tone=request.tone,
                    provider_type="openai",
                    options=options,
                )
            )

        # Calculate word count
        word_count = 0
        for section in blog_post.sections:
            for subtopic in section.subtopics:
                word_count += len(subtopic.content.split())

        # Emit webhook event
        await webhook_service.emit_content_generated(
            user_id=user_id,
            content_type=request.content_type,
            title=blog_post.title,
            content_id=job_id,
            word_count=word_count,
            metadata={
                "topic": request.topic,
                "tone": request.tone,
                "research": request.research,
            },
        )

        # If callback URL provided, send result directly
        if request.webhook_url:
            from src.types.webhooks import WebhookPayload

            payload = WebhookPayload(
                id=str(uuid.uuid4()),
                event_type=WebhookEventType.CONTENT_GENERATED,
                data={
                    "job_id": job_id,
                    "status": "completed",
                    "content_type": request.content_type,
                    "title": blog_post.title,
                    "description": blog_post.description,
                    "word_count": word_count,
                    "content": {
                        "title": blog_post.title,
                        "description": blog_post.description,
                        "sections": [
                            {
                                "title": section.title,
                                "subtopics": [
                                    {"title": st.title, "content": st.content}
                                    for st in section.subtopics
                                ],
                            }
                            for section in blog_post.sections
                        ],
                    },
                },
            )

            temp_sub = WebhookSubscription(
                id=f"callback-{job_id}",
                user_id=user_id,
                target_url=request.webhook_url,
                event_types=[WebhookEventType.CONTENT_GENERATED],
            )

            await webhook_service._deliver_webhook(
                subscription=temp_sub,
                payload=payload,
                delivery_id=str(uuid.uuid4()),
            )

        logger.info(f"Zapier content generation completed: {job_id}")

    except Exception as e:
        logger.error(f"Zapier content generation failed: {job_id} - {str(e)}", exc_info=True)


@router.post(
    "/actions/generate",
    response_model=ZapierGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Action: Generate content",
    description="""
Trigger content generation from Zapier.

This action starts content generation in the background and returns immediately.
The result will be sent to the configured webhook URL when complete.

**Content Types:**
- `blog` - Generate a blog post

**Tones:**
- `professional`, `casual`, `informative`, `persuasive`, `friendly`
    """,
    responses={
        202: {"description": "Generation started"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit or quota exceeded"},
    },
)
async def zapier_generate(
    request: ZapierGenerateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_quota),
) -> ZapierGenerateResponse:
    """
    Generate content via Zapier action.

    Starts content generation in the background and returns a job ID.
    Results are sent via webhook when complete.

    Args:
        request: Generation request
        background_tasks: FastAPI background tasks
        user_id: Authenticated user ID

    Returns:
        Job information for tracking
    """
    logger.info(f"Zapier generate action from user {user_id}: {request.topic[:50]}")

    # Validate content type
    if request.content_type not in ["blog", "book"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content_type: {request.content_type}. Must be 'blog' or 'book'.",
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Start generation in background
    background_tasks.add_task(
        _generate_content_async,
        request,
        user_id,
        job_id,
    )

    # Increment usage
    await increment_usage_for_operation(
        user_id=user_id,
        operation_type=request.content_type,
        tokens_used=4000,  # Estimated
        metadata={"source": "zapier", "topic": request.topic[:50]},
    )

    return ZapierGenerateResponse(
        success=True,
        job_id=job_id,
        status="pending",
        message=f"Content generation started for: {request.topic[:50]}",
        estimated_completion_seconds=60,
    )


# =============================================================================
# Sample Data (for Zapier app setup)
# =============================================================================


@router.get(
    "/sample/content",
    response_model=List[ZapierTriggerItem],
    summary="Sample data: Content",
    description="""
Returns sample content data for Zapier trigger setup.

Zapier uses this to show users what data fields are available.
    """,
)
async def sample_content() -> List[ZapierTriggerItem]:
    """
    Return sample content data for Zapier setup.

    This endpoint helps Zapier understand the data structure
    when users are setting up their Zaps.

    Returns:
        Sample content items
    """
    return [
        ZapierTriggerItem(
            id="sample_content_1",
            created_at=datetime.utcnow().isoformat(),
            type="blog",
            title="10 Tips for Effective Remote Work",
            description="A comprehensive guide to staying productive while working from home.",
            word_count=2500,
            url="https://example.com/blog/remote-work-tips",
            metadata={
                "tone": "professional",
                "keywords": ["remote work", "productivity", "work from home"],
                "research_enabled": True,
            },
        ),
        ZapierTriggerItem(
            id="sample_content_2",
            created_at=datetime.utcnow().isoformat(),
            type="blog",
            title="The Future of AI in Content Creation",
            description="Exploring how artificial intelligence is transforming content generation.",
            word_count=1800,
            metadata={
                "tone": "informative",
                "keywords": ["AI", "content creation", "automation"],
            },
        ),
    ]


@router.get(
    "/sample/batch",
    response_model=List[Dict],
    summary="Sample data: Batch",
    description="Returns sample batch completion data for Zapier trigger setup.",
)
async def sample_batch() -> List[Dict]:
    """
    Return sample batch completion data for Zapier setup.

    Returns:
        Sample batch completion items
    """
    return [
        {
            "id": "sample_batch_1",
            "job_id": "job_abc123",
            "total_items": 10,
            "completed_items": 9,
            "failed_items": 1,
            "success_rate": 90.0,
            "total_cost_usd": 0.45,
            "completed_at": datetime.utcnow().isoformat(),
        },
    ]
