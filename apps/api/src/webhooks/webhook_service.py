"""
Webhook service for async delivery with retries.

This module provides the core webhook delivery functionality including:
- Async HTTP delivery with configurable timeouts
- Exponential backoff retries
- HMAC-SHA256 payload signing
- Delivery logging and monitoring
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.types.webhooks import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEventType,
    WebhookPayload,
    WebhookSubscription,
)

from .webhook_storage import webhook_storage

logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_TIMEOUT_SECONDS = 30
WEBHOOK_MAX_RETRIES = 5
WEBHOOK_RETRY_BASE_DELAY = 1  # seconds
WEBHOOK_RETRY_MAX_DELAY = 300  # 5 minutes max delay
WEBHOOK_USER_AGENT = "BlogAI-Webhooks/1.0"


class WebhookService:
    """
    Service for managing webhook delivery.

    Provides methods for:
    - Emitting events to all subscribed webhooks
    - Delivering webhooks with retries and exponential backoff
    - Signing payloads with HMAC-SHA256
    - Logging delivery attempts
    """

    def __init__(self) -> None:
        """Initialize the webhook service."""
        self._http_client: Optional[httpx.AsyncClient] = None
        self._global_secret = os.environ.get("WEBHOOK_SECRET", "")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(WEBHOOK_TIMEOUT_SECONDS),
                follow_redirects=True,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _generate_signature(
        self,
        payload: str,
        secret: str,
        timestamp: str,
    ) -> str:
        """
        Generate HMAC-SHA256 signature for payload.

        The signature is computed over: timestamp + "." + payload
        This prevents replay attacks by including the timestamp.

        Args:
            payload: JSON payload string
            secret: Secret key for signing
            timestamp: Unix timestamp string

        Returns:
            Hex-encoded signature
        """
        if not secret:
            return ""

        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _build_headers(
        self,
        payload: str,
        secret: str,
        event_id: str,
        event_type: WebhookEventType,
    ) -> Dict[str, str]:
        """
        Build headers for webhook delivery.

        Includes:
        - Content-Type: application/json
        - User-Agent: BlogAI identifier
        - X-Webhook-ID: Unique event ID
        - X-Webhook-Event: Event type
        - X-Webhook-Timestamp: Unix timestamp
        - X-Webhook-Signature: HMAC-SHA256 signature (if secret provided)

        Args:
            payload: JSON payload string
            secret: Secret for signing
            event_id: Unique event ID
            event_type: Event type being delivered

        Returns:
            Headers dictionary
        """
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": WEBHOOK_USER_AGENT,
            "X-Webhook-ID": event_id,
            "X-Webhook-Event": event_type.value,
            "X-Webhook-Timestamp": timestamp,
        }

        if secret:
            signature = self._generate_signature(payload, secret, timestamp)
            # Format: t=timestamp,v1=signature (similar to Stripe's format)
            headers["X-Webhook-Signature"] = f"t={timestamp},v1={signature}"

        return headers

    def _calculate_retry_delay(self, attempt: int) -> int:
        """
        Calculate retry delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: 1, 2, 4, 8, 16, ... seconds
        delay = WEBHOOK_RETRY_BASE_DELAY * (2 ** (attempt - 1))
        # Add jitter (up to 25% of delay)
        import random
        jitter = random.uniform(0, delay * 0.25)
        delay = min(delay + jitter, WEBHOOK_RETRY_MAX_DELAY)
        return int(delay)

    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        delivery_id: str,
        attempt: int = 1,
    ) -> WebhookDelivery:
        """
        Deliver a webhook to a subscription endpoint.

        Args:
            subscription: Target subscription
            payload: Webhook payload to deliver
            delivery_id: Unique delivery ID
            attempt: Current attempt number

        Returns:
            WebhookDelivery record
        """
        client = await self._get_client()
        start_time = time.time()

        # Serialize payload
        payload_json = payload.model_dump_json()

        # Get secret (prefer subscription secret, fall back to global)
        secret = subscription.secret or self._global_secret

        # Build headers
        headers = self._build_headers(
            payload_json,
            secret,
            payload.id,
            payload.event_type,
        )

        # Create initial delivery record
        delivery = WebhookDelivery(
            id=delivery_id,
            subscription_id=subscription.id,
            event_type=payload.event_type,
            event_id=payload.id,
            status=DeliveryStatus.PENDING,
            target_url=subscription.target_url,
            request_headers={k: v for k, v in headers.items() if "signature" not in k.lower()},
            request_payload=payload.model_dump(),
            attempt_number=attempt,
            max_attempts=WEBHOOK_MAX_RETRIES,
        )

        try:
            # Make the request
            response = await client.post(
                subscription.target_url,
                content=payload_json,
                headers=headers,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Update delivery record
            delivery.response_status_code = response.status_code
            delivery.response_headers = dict(response.headers)
            delivery.response_body = response.text[:10000]  # Truncate large responses
            delivery.duration_ms = duration_ms
            delivery.delivered_at = datetime.utcnow().isoformat()

            # Check if successful (2xx status codes)
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                logger.info(
                    f"Webhook delivered successfully: {delivery_id} "
                    f"to {subscription.target_url} ({response.status_code})"
                )
            else:
                # Non-2xx response is a failure
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(
                    f"Webhook delivery failed: {delivery_id} "
                    f"to {subscription.target_url} ({response.status_code})"
                )

        except httpx.TimeoutException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = f"Timeout after {WEBHOOK_TIMEOUT_SECONDS}s"
            delivery.duration_ms = duration_ms
            logger.warning(f"Webhook delivery timed out: {delivery_id} to {subscription.target_url}")

        except httpx.RequestError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = f"Request error: {str(e)}"
            delivery.duration_ms = duration_ms
            logger.warning(f"Webhook delivery request error: {delivery_id} - {str(e)}")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = f"Unexpected error: {str(e)}"
            delivery.duration_ms = duration_ms
            logger.error(f"Webhook delivery unexpected error: {delivery_id} - {str(e)}", exc_info=True)

        # Save delivery log
        await webhook_storage.save_delivery(delivery)

        # Update subscription stats
        await webhook_storage.update_subscription_stats(
            subscription.id,
            success=(delivery.status == DeliveryStatus.DELIVERED),
            error_message=delivery.error_message,
        )

        return delivery

    async def _deliver_with_retries(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
    ) -> WebhookDelivery:
        """
        Deliver a webhook with automatic retries on failure.

        Uses exponential backoff between retries.

        Args:
            subscription: Target subscription
            payload: Webhook payload

        Returns:
            Final WebhookDelivery record
        """
        delivery_id = str(uuid.uuid4())

        for attempt in range(1, WEBHOOK_MAX_RETRIES + 1):
            delivery = await self._deliver_webhook(
                subscription=subscription,
                payload=payload,
                delivery_id=f"{delivery_id}-{attempt}",
                attempt=attempt,
            )

            if delivery.status == DeliveryStatus.DELIVERED:
                return delivery

            if attempt < WEBHOOK_MAX_RETRIES:
                # Calculate and wait for retry delay
                delay = self._calculate_retry_delay(attempt)
                delivery.status = DeliveryStatus.RETRYING
                delivery.next_retry_at = (
                    datetime.utcnow() + timedelta(seconds=delay)
                ).isoformat()

                logger.info(
                    f"Webhook delivery failed, retrying in {delay}s "
                    f"(attempt {attempt}/{WEBHOOK_MAX_RETRIES})"
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            f"Webhook delivery failed after {WEBHOOK_MAX_RETRIES} attempts: "
            f"{delivery_id} to {subscription.target_url}"
        )
        return delivery

    async def emit_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit an event to all subscribed webhooks.

        This is the main entry point for triggering webhooks.

        Args:
            event_type: Type of event to emit
            data: Event-specific data payload
            user_id: Optional user ID to filter subscriptions
            metadata: Optional additional metadata

        Returns:
            List of delivery IDs for tracking
        """
        # Create the payload
        payload = WebhookPayload(
            id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            metadata=metadata or {},
        )

        # Get subscriptions for this event
        subscriptions = await webhook_storage.get_subscriptions_for_event(
            event_type,
            active_only=True,
        )

        # Filter by user if specified
        if user_id:
            subscriptions = [s for s in subscriptions if s.user_id == user_id]

        if not subscriptions:
            logger.debug(f"No subscriptions for event {event_type.value}")
            return []

        logger.info(
            f"Emitting {event_type.value} event to {len(subscriptions)} subscription(s)"
        )

        # Deliver to all subscriptions concurrently
        delivery_ids: List[str] = []
        tasks = []

        for subscription in subscriptions:
            task = asyncio.create_task(
                self._deliver_with_retries(subscription, payload)
            )
            tasks.append(task)

        # Wait for all deliveries (with timeout)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300,  # 5 minute total timeout
            )
            for result in results:
                if isinstance(result, WebhookDelivery):
                    delivery_ids.append(result.id)
                elif isinstance(result, Exception):
                    logger.error(f"Webhook delivery task failed: {result}")
        except asyncio.TimeoutError:
            logger.error("Webhook delivery batch timed out")

        # Save event for polling triggers
        if user_id:
            event_data = {
                "id": payload.id,
                "event_type": event_type.value,
                "created_at": payload.created_at,
                **data,
            }
            await webhook_storage.save_recent_event(user_id, event_data)

        return delivery_ids

    async def test_webhook(
        self,
        target_url: str,
        secret: Optional[str] = None,
    ) -> WebhookDelivery:
        """
        Send a test webhook to verify endpoint configuration.

        Args:
            target_url: URL to test
            secret: Optional secret for signing

        Returns:
            WebhookDelivery record with results
        """
        # Create test payload
        payload = WebhookPayload(
            id=str(uuid.uuid4()),
            event_type=WebhookEventType.TEST,
            data={
                "message": "This is a test webhook from Blog AI",
                "test_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Create temporary subscription for the test
        temp_subscription = WebhookSubscription(
            id=f"test-{uuid.uuid4()}",
            user_id="test",
            target_url=target_url,
            event_types=[WebhookEventType.TEST],
            secret=secret,
        )

        # Deliver without retries for test
        delivery = await self._deliver_webhook(
            subscription=temp_subscription,
            payload=payload,
            delivery_id=str(uuid.uuid4()),
            attempt=1,
        )

        return delivery

    async def emit_content_generated(
        self,
        user_id: str,
        content_type: str,
        title: str,
        content_id: str,
        word_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a content.generated event.

        Convenience method for content generation completion.

        Args:
            user_id: User who generated the content
            content_type: Type of content (blog, book)
            title: Content title
            content_id: Unique content ID
            word_count: Optional word count
            metadata: Additional metadata

        Returns:
            List of delivery IDs
        """
        data = {
            "content_type": content_type,
            "content_id": content_id,
            "title": title,
            "word_count": word_count,
            "generated_at": datetime.utcnow().isoformat(),
        }
        if metadata:
            data["metadata"] = metadata

        return await self.emit_event(
            event_type=WebhookEventType.CONTENT_GENERATED,
            data=data,
            user_id=user_id,
        )

    async def emit_batch_completed(
        self,
        user_id: str,
        job_id: str,
        total_items: int,
        completed_items: int,
        failed_items: int,
        total_cost_usd: Optional[float] = None,
    ) -> List[str]:
        """
        Emit a batch.completed event.

        Convenience method for batch processing completion.

        Args:
            user_id: User who ran the batch
            job_id: Batch job ID
            total_items: Total items in batch
            completed_items: Successfully completed items
            failed_items: Failed items
            total_cost_usd: Total cost of the batch

        Returns:
            List of delivery IDs
        """
        data = {
            "job_id": job_id,
            "total_items": total_items,
            "completed_items": completed_items,
            "failed_items": failed_items,
            "success_rate": round(completed_items / total_items * 100, 1) if total_items > 0 else 0,
            "total_cost_usd": total_cost_usd,
            "completed_at": datetime.utcnow().isoformat(),
        }

        return await self.emit_event(
            event_type=WebhookEventType.BATCH_COMPLETED,
            data=data,
            user_id=user_id,
        )

    async def emit_quota_warning(
        self,
        user_id: str,
        usage_percentage: float,
        current_usage: int,
        quota_limit: int,
    ) -> List[str]:
        """
        Emit a quota.warning event.

        Convenience method for quota warnings.

        Args:
            user_id: User approaching quota limit
            usage_percentage: Percentage of quota used
            current_usage: Current usage count
            quota_limit: Maximum allowed usage

        Returns:
            List of delivery IDs
        """
        data = {
            "usage_percentage": usage_percentage,
            "current_usage": current_usage,
            "quota_limit": quota_limit,
            "remaining": quota_limit - current_usage,
            "warning_at": datetime.utcnow().isoformat(),
        }

        return await self.emit_event(
            event_type=WebhookEventType.QUOTA_WARNING,
            data=data,
            user_id=user_id,
        )


# Singleton instance
webhook_service = WebhookService()
