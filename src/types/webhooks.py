"""
Webhook types and models for Zapier-compatible webhook system.

This module defines the data models for webhook subscriptions, deliveries,
and event payloads used throughout the webhook system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WebhookEventType(str, Enum):
    """Supported webhook event types."""

    # Content events
    CONTENT_GENERATED = "content.generated"
    CONTENT_PUBLISHED = "content.published"

    # Batch events
    BATCH_STARTED = "batch.started"
    BATCH_PROGRESS = "batch.progress"
    BATCH_COMPLETED = "batch.completed"
    BATCH_FAILED = "batch.failed"

    # Quota events
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"

    # Test event
    TEST = "test"


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(BaseModel):
    """
    Model for webhook subscription.

    Represents a registered webhook endpoint that will receive
    notifications for specific event types.
    """

    id: str = Field(..., description="Unique subscription ID")
    user_id: str = Field(..., description="Owner user ID")
    target_url: str = Field(..., description="URL to deliver webhooks to")
    event_types: List[WebhookEventType] = Field(
        ...,
        description="Event types this subscription listens for",
        min_length=1,
    )
    secret: Optional[str] = Field(
        default=None,
        description="Secret for signing payloads (set by user)",
    )
    is_active: bool = Field(default=True, description="Whether subscription is active")
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description for the subscription",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata for the subscription",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp when subscription was created",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when subscription was last updated",
    )

    # Delivery stats
    total_deliveries: int = Field(default=0, description="Total delivery attempts")
    successful_deliveries: int = Field(default=0, description="Successful deliveries")
    failed_deliveries: int = Field(default=0, description="Failed deliveries")
    last_delivery_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last delivery attempt",
    )
    last_success_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last successful delivery",
    )
    last_failure_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last failed delivery",
    )
    last_error: Optional[str] = Field(
        default=None,
        description="Error message from last failed delivery",
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Validate that target URL is HTTPS in production."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Target URL must start with http:// or https://")
        return v


class WebhookSubscriptionCreate(BaseModel):
    """Request model for creating a webhook subscription."""

    target_url: str = Field(..., description="URL to deliver webhooks to")
    event_types: List[WebhookEventType] = Field(
        ...,
        description="Event types to subscribe to",
        min_length=1,
    )
    secret: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Secret for HMAC signature verification",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata",
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Validate target URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Target URL must start with http:// or https://")
        # Basic URL validation
        if len(v) > 2048:
            raise ValueError("Target URL exceeds maximum length of 2048 characters")
        return v


class WebhookSubscriptionUpdate(BaseModel):
    """Request model for updating a webhook subscription."""

    target_url: Optional[str] = Field(default=None, description="New target URL")
    event_types: Optional[List[WebhookEventType]] = Field(
        default=None,
        description="New event types",
        min_length=1,
    )
    secret: Optional[str] = Field(
        default=None,
        max_length=256,
        description="New secret",
    )
    is_active: Optional[bool] = Field(default=None, description="Active status")
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New description",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="New metadata",
    )


class WebhookDelivery(BaseModel):
    """
    Model for webhook delivery log entry.

    Tracks individual delivery attempts for auditing and debugging.
    """

    id: str = Field(..., description="Unique delivery ID")
    subscription_id: str = Field(..., description="Associated subscription ID")
    event_type: WebhookEventType = Field(..., description="Event type delivered")
    event_id: str = Field(..., description="Unique event ID for deduplication")
    status: DeliveryStatus = Field(
        default=DeliveryStatus.PENDING,
        description="Delivery status",
    )
    target_url: str = Field(..., description="URL the webhook was sent to")

    # Request details
    request_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Headers sent with request",
    )
    request_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload sent (may be truncated)",
    )

    # Response details
    response_status_code: Optional[int] = Field(
        default=None,
        description="HTTP response status code",
    )
    response_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Response headers received",
    )
    response_body: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Response body (truncated if large)",
    )

    # Timing
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When delivery was created",
    )
    delivered_at: Optional[str] = Field(
        default=None,
        description="When delivery completed",
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Request duration in milliseconds",
    )

    # Retry info
    attempt_number: int = Field(default=1, description="Attempt number (1-indexed)")
    max_attempts: int = Field(default=5, description="Maximum retry attempts")
    next_retry_at: Optional[str] = Field(
        default=None,
        description="When next retry will occur",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if delivery failed",
    )


class WebhookPayload(BaseModel):
    """
    Standard webhook payload structure.

    This is the format sent to webhook endpoints, following
    Zapier and industry best practices.
    """

    # Event identification
    id: str = Field(..., description="Unique event ID for deduplication")
    event_type: WebhookEventType = Field(..., description="Type of event")
    api_version: str = Field(default="2024-01-01", description="API version")

    # Timestamps
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When event was created",
    )

    # Source info
    source: str = Field(default="blog-ai", description="Source system identifier")

    # Event data
    data: Dict[str, Any] = Field(..., description="Event-specific payload data")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context",
    )


class WebhookTestRequest(BaseModel):
    """Request model for testing a webhook."""

    subscription_id: Optional[str] = Field(
        default=None,
        description="Specific subscription to test (optional)",
    )
    target_url: Optional[str] = Field(
        default=None,
        description="Direct URL to test (if not using subscription)",
    )
    event_type: WebhookEventType = Field(
        default=WebhookEventType.TEST,
        description="Event type to send",
    )


class WebhookTestResponse(BaseModel):
    """Response model for webhook test."""

    success: bool = Field(..., description="Whether test was successful")
    delivery_id: str = Field(..., description="Delivery ID for this test")
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP response status code",
    )
    response_time_ms: Optional[int] = Field(
        default=None,
        description="Response time in milliseconds",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if test failed",
    )


# Zapier-specific models


class ZapierSubscribeRequest(BaseModel):
    """
    Zapier REST Hook subscription request.

    Zapier sends this when a user enables a trigger.
    """

    target_url: str = Field(
        ...,
        alias="hookUrl",
        description="URL Zapier wants webhooks sent to",
    )

    class Config:
        populate_by_name = True


class ZapierSubscribeResponse(BaseModel):
    """Response for Zapier subscription request."""

    id: str = Field(..., description="Subscription ID for unsubscribe")


class ZapierTriggerItem(BaseModel):
    """
    Single item in Zapier polling trigger response.

    Must include 'id' field for deduplication.
    """

    id: str = Field(..., description="Unique ID for deduplication")
    created_at: str = Field(..., description="ISO timestamp")
    type: str = Field(..., description="Content type (blog, book)")
    title: str = Field(..., description="Content title")
    description: Optional[str] = Field(default=None, description="Content description")
    word_count: Optional[int] = Field(default=None, description="Word count")
    url: Optional[str] = Field(default=None, description="Content URL if published")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional content metadata",
    )


class ZapierGenerateRequest(BaseModel):
    """
    Request model for Zapier generate action.

    Allows Zapier to trigger content generation.
    """

    topic: str = Field(..., min_length=1, max_length=500, description="Topic to generate content about")
    content_type: str = Field(
        default="blog",
        description="Type of content to generate",
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        description="Optional keywords",
    )
    tone: str = Field(default="professional", description="Content tone")
    research: bool = Field(default=False, description="Enable web research")
    webhook_url: Optional[str] = Field(
        default=None,
        description="URL to send result when complete",
    )


class ZapierGenerateResponse(BaseModel):
    """Response for Zapier generate action."""

    success: bool = Field(..., description="Whether generation started")
    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(default="pending", description="Current status")
    message: str = Field(..., description="Status message")
    estimated_completion_seconds: Optional[int] = Field(
        default=None,
        description="Estimated time to complete",
    )
