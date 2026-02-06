"""
Webhook storage with Redis backend and in-memory fallback.

This module provides persistent storage for webhook subscriptions and
delivery logs with:
- Redis as primary storage for durability
- In-memory fallback when Redis is unavailable
- Automatic TTL management for delivery logs
- Multi-tenant support with user ownership
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.storage.redis_client import redis_client
from src.types.webhooks import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEventType,
    WebhookSubscription,
)

logger = logging.getLogger(__name__)

# Redis key prefixes
SUBSCRIPTION_PREFIX = "webhook:subscription:"
DELIVERY_PREFIX = "webhook:delivery:"
USER_SUBSCRIPTIONS_PREFIX = "webhook:user_subs:"
EVENT_SUBSCRIPTIONS_PREFIX = "webhook:event_subs:"
RECENT_EVENTS_PREFIX = "webhook:recent_events:"

# TTLs
SUBSCRIPTION_TTL = 86400 * 365  # 1 year
DELIVERY_LOG_TTL = 86400 * 30  # 30 days
RECENT_EVENTS_TTL = 86400 * 7  # 7 days


class WebhookStorage:
    """
    Redis-backed webhook storage with fallback to in-memory.

    Provides persistent storage for webhook subscriptions and delivery
    logs with automatic fallback to in-memory when Redis is unavailable.
    """

    def __init__(self) -> None:
        """Initialize WebhookStorage with empty fallback storage."""
        # In-memory fallback storage
        self._fallback_subscriptions: Dict[str, dict] = {}
        self._fallback_deliveries: Dict[str, dict] = {}
        self._fallback_user_subs: Dict[str, List[str]] = {}  # user_id -> [sub_ids]
        self._fallback_event_subs: Dict[str, List[str]] = {}  # event_type -> [sub_ids]
        self._fallback_recent_events: Dict[str, List[dict]] = {}  # user_id -> [events]
        self._using_fallback: bool = False

    async def _get_redis(self):
        """Get Redis client, returns None if unavailable."""
        client = await redis_client.get_client()
        self._using_fallback = client is None
        return client

    @property
    def using_fallback(self) -> bool:
        """Check if currently using in-memory fallback."""
        return self._using_fallback

    # =========================================================================
    # Subscription Operations
    # =========================================================================

    async def save_subscription(
        self,
        subscription: WebhookSubscription,
    ) -> bool:
        """
        Save a webhook subscription.

        Args:
            subscription: WebhookSubscription to save

        Returns:
            True if saved successfully
        """
        redis = await self._get_redis()
        sub_data = subscription.model_dump(mode="json")

        if redis:
            try:
                key = f"{SUBSCRIPTION_PREFIX}{subscription.id}"
                await redis.set(key, json.dumps(sub_data), ex=SUBSCRIPTION_TTL)

                # Add to user's subscription index
                user_key = f"{USER_SUBSCRIPTIONS_PREFIX}{subscription.user_id}"
                await redis.sadd(user_key, subscription.id)
                await redis.expire(user_key, SUBSCRIPTION_TTL)

                # Add to event type indexes
                for event_type in subscription.event_types:
                    event_key = f"{EVENT_SUBSCRIPTIONS_PREFIX}{event_type.value}"
                    await redis.sadd(event_key, subscription.id)
                    await redis.expire(event_key, SUBSCRIPTION_TTL)

                logger.debug(f"Saved webhook subscription {subscription.id} to Redis")
                return True
            except Exception as e:
                logger.warning(f"Redis save_subscription error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_subscriptions[subscription.id] = sub_data

        # Update user index
        if subscription.user_id not in self._fallback_user_subs:
            self._fallback_user_subs[subscription.user_id] = []
        if subscription.id not in self._fallback_user_subs[subscription.user_id]:
            self._fallback_user_subs[subscription.user_id].append(subscription.id)

        # Update event indexes
        for event_type in subscription.event_types:
            event_key = event_type.value
            if event_key not in self._fallback_event_subs:
                self._fallback_event_subs[event_key] = []
            if subscription.id not in self._fallback_event_subs[event_key]:
                self._fallback_event_subs[event_key].append(subscription.id)

        logger.debug(f"Saved webhook subscription {subscription.id} to in-memory storage")
        return True

    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """
        Get a subscription by ID.

        Args:
            subscription_id: Unique subscription ID

        Returns:
            WebhookSubscription if found, None otherwise
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{SUBSCRIPTION_PREFIX}{subscription_id}"
                data = await redis.get(key)
                if data:
                    return WebhookSubscription.model_validate(json.loads(data))
            except Exception as e:
                logger.warning(f"Redis get_subscription error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        sub_data = self._fallback_subscriptions.get(subscription_id)
        if sub_data:
            return WebhookSubscription.model_validate(sub_data)
        return None

    async def get_subscription_if_owned(
        self,
        subscription_id: str,
        user_id: str,
    ) -> Optional[WebhookSubscription]:
        """
        Get a subscription only if the user owns it.

        Args:
            subscription_id: Unique subscription ID
            user_id: User ID requesting access

        Returns:
            WebhookSubscription if user owns it, None otherwise
        """
        subscription = await self.get_subscription(subscription_id)
        if subscription and subscription.user_id == user_id:
            return subscription
        return None

    async def update_subscription(
        self,
        subscription_id: str,
        updates: dict,
    ) -> bool:
        """
        Update specific fields in a subscription.

        Args:
            subscription_id: Unique subscription ID
            updates: Dictionary of fields to update

        Returns:
            True if updated successfully
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        # Handle event_types changes (need to update indexes)
        old_event_types = set(subscription.event_types)

        # Apply updates
        sub_data = subscription.model_dump()
        sub_data.update(updates)
        sub_data["updated_at"] = datetime.utcnow().isoformat()

        updated_subscription = WebhookSubscription.model_validate(sub_data)

        # Update event type indexes if they changed
        new_event_types = set(updated_subscription.event_types)
        if old_event_types != new_event_types:
            redis = await self._get_redis()
            if redis:
                try:
                    # Remove from old event indexes
                    for event_type in old_event_types - new_event_types:
                        event_key = f"{EVENT_SUBSCRIPTIONS_PREFIX}{event_type.value}"
                        await redis.srem(event_key, subscription_id)
                    # Add to new event indexes
                    for event_type in new_event_types - old_event_types:
                        event_key = f"{EVENT_SUBSCRIPTIONS_PREFIX}{event_type.value}"
                        await redis.sadd(event_key, subscription_id)
                except Exception as e:
                    logger.warning(f"Redis event index update error: {str(e)}")
            else:
                # Fallback: Update in-memory indexes
                for event_type in old_event_types - new_event_types:
                    event_key = event_type.value
                    if event_key in self._fallback_event_subs:
                        if subscription_id in self._fallback_event_subs[event_key]:
                            self._fallback_event_subs[event_key].remove(subscription_id)
                for event_type in new_event_types - old_event_types:
                    event_key = event_type.value
                    if event_key not in self._fallback_event_subs:
                        self._fallback_event_subs[event_key] = []
                    self._fallback_event_subs[event_key].append(subscription_id)

        return await self.save_subscription(updated_subscription)

    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription.

        Args:
            subscription_id: Unique subscription ID

        Returns:
            True if deleted successfully
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        redis = await self._get_redis()

        if redis:
            try:
                # Delete subscription
                key = f"{SUBSCRIPTION_PREFIX}{subscription_id}"
                await redis.delete(key)

                # Remove from user index
                user_key = f"{USER_SUBSCRIPTIONS_PREFIX}{subscription.user_id}"
                await redis.srem(user_key, subscription_id)

                # Remove from event indexes
                for event_type in subscription.event_types:
                    event_key = f"{EVENT_SUBSCRIPTIONS_PREFIX}{event_type.value}"
                    await redis.srem(event_key, subscription_id)

                logger.debug(f"Deleted webhook subscription {subscription_id} from Redis")
            except Exception as e:
                logger.warning(f"Redis delete_subscription error: {str(e)}")

        # Also clean from fallback
        self._fallback_subscriptions.pop(subscription_id, None)
        if subscription.user_id in self._fallback_user_subs:
            if subscription_id in self._fallback_user_subs[subscription.user_id]:
                self._fallback_user_subs[subscription.user_id].remove(subscription_id)
        for event_type in subscription.event_types:
            event_key = event_type.value
            if event_key in self._fallback_event_subs:
                if subscription_id in self._fallback_event_subs[event_key]:
                    self._fallback_event_subs[event_key].remove(subscription_id)

        return True

    async def list_user_subscriptions(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WebhookSubscription]:
        """
        List subscriptions owned by a user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of WebhookSubscription instances
        """
        redis = await self._get_redis()
        subscriptions: List[WebhookSubscription] = []

        if redis:
            try:
                user_key = f"{USER_SUBSCRIPTIONS_PREFIX}{user_id}"
                sub_ids = await redis.smembers(user_key)

                for sub_id in sub_ids:
                    subscription = await self.get_subscription(sub_id)
                    if subscription:
                        subscriptions.append(subscription)
            except Exception as e:
                logger.warning(f"Redis list_user_subscriptions error: {str(e)}, falling back to memory")
                subscriptions = []

        # Fallback or merge with in-memory
        if not subscriptions or self._using_fallback:
            sub_ids = self._fallback_user_subs.get(user_id, [])
            for sub_id in sub_ids:
                sub_data = self._fallback_subscriptions.get(sub_id)
                if sub_data:
                    subscription = WebhookSubscription.model_validate(sub_data)
                    if subscription not in subscriptions:
                        subscriptions.append(subscription)

        # Sort by created_at descending
        subscriptions.sort(key=lambda s: s.created_at, reverse=True)

        # Apply pagination
        return subscriptions[offset : offset + limit]

    async def get_subscriptions_for_event(
        self,
        event_type: WebhookEventType,
        active_only: bool = True,
    ) -> List[WebhookSubscription]:
        """
        Get all subscriptions listening for an event type.

        Args:
            event_type: Event type to look up
            active_only: Only return active subscriptions

        Returns:
            List of WebhookSubscription instances
        """
        redis = await self._get_redis()
        subscriptions: List[WebhookSubscription] = []

        if redis:
            try:
                event_key = f"{EVENT_SUBSCRIPTIONS_PREFIX}{event_type.value}"
                sub_ids = await redis.smembers(event_key)

                for sub_id in sub_ids:
                    subscription = await self.get_subscription(sub_id)
                    if subscription:
                        if not active_only or subscription.is_active:
                            subscriptions.append(subscription)
            except Exception as e:
                logger.warning(f"Redis get_subscriptions_for_event error: {str(e)}, falling back to memory")
                subscriptions = []

        # Fallback or merge with in-memory
        if not subscriptions or self._using_fallback:
            sub_ids = self._fallback_event_subs.get(event_type.value, [])
            for sub_id in sub_ids:
                sub_data = self._fallback_subscriptions.get(sub_id)
                if sub_data:
                    subscription = WebhookSubscription.model_validate(sub_data)
                    if subscription not in subscriptions:
                        if not active_only or subscription.is_active:
                            subscriptions.append(subscription)

        return subscriptions

    # =========================================================================
    # Delivery Log Operations
    # =========================================================================

    async def save_delivery(self, delivery: WebhookDelivery) -> bool:
        """
        Save a delivery log entry.

        Args:
            delivery: WebhookDelivery to save

        Returns:
            True if saved successfully
        """
        redis = await self._get_redis()
        delivery_data = delivery.model_dump(mode="json")

        if redis:
            try:
                key = f"{DELIVERY_PREFIX}{delivery.id}"
                await redis.set(key, json.dumps(delivery_data), ex=DELIVERY_LOG_TTL)
                logger.debug(f"Saved delivery {delivery.id} to Redis")
                return True
            except Exception as e:
                logger.warning(f"Redis save_delivery error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_deliveries[delivery.id] = delivery_data
        logger.debug(f"Saved delivery {delivery.id} to in-memory storage")
        return True

    async def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """
        Get a delivery log entry by ID.

        Args:
            delivery_id: Unique delivery ID

        Returns:
            WebhookDelivery if found, None otherwise
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{DELIVERY_PREFIX}{delivery_id}"
                data = await redis.get(key)
                if data:
                    return WebhookDelivery.model_validate(json.loads(data))
            except Exception as e:
                logger.warning(f"Redis get_delivery error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        delivery_data = self._fallback_deliveries.get(delivery_id)
        if delivery_data:
            return WebhookDelivery.model_validate(delivery_data)
        return None

    async def update_delivery(
        self,
        delivery_id: str,
        updates: dict,
    ) -> bool:
        """
        Update a delivery log entry.

        Args:
            delivery_id: Unique delivery ID
            updates: Fields to update

        Returns:
            True if updated successfully
        """
        delivery = await self.get_delivery(delivery_id)
        if not delivery:
            return False

        delivery_data = delivery.model_dump()
        delivery_data.update(updates)
        updated_delivery = WebhookDelivery.model_validate(delivery_data)
        return await self.save_delivery(updated_delivery)

    # =========================================================================
    # Recent Events (for Zapier polling triggers)
    # =========================================================================

    async def save_recent_event(
        self,
        user_id: str,
        event_data: dict,
        max_events: int = 100,
    ) -> bool:
        """
        Save a recent event for polling triggers.

        Args:
            user_id: User who owns this event
            event_data: Event data with 'id' field
            max_events: Maximum events to keep per user

        Returns:
            True if saved successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{RECENT_EVENTS_PREFIX}{user_id}"
                # Add to sorted set by timestamp
                score = datetime.utcnow().timestamp()
                await redis.zadd(key, {json.dumps(event_data): score})
                # Trim to max events
                await redis.zremrangebyrank(key, 0, -(max_events + 1))
                await redis.expire(key, RECENT_EVENTS_TTL)
                return True
            except Exception as e:
                logger.warning(f"Redis save_recent_event error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        if user_id not in self._fallback_recent_events:
            self._fallback_recent_events[user_id] = []
        self._fallback_recent_events[user_id].append(event_data)
        # Trim to max events
        self._fallback_recent_events[user_id] = self._fallback_recent_events[user_id][-max_events:]
        return True

    async def get_recent_events(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[dict]:
        """
        Get recent events for polling triggers.

        Args:
            user_id: User to get events for
            limit: Maximum events to return

        Returns:
            List of event data dictionaries, newest first
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{RECENT_EVENTS_PREFIX}{user_id}"
                # Get newest events first
                events_raw = await redis.zrevrange(key, 0, limit - 1)
                events = [json.loads(e) for e in events_raw]
                return events
            except Exception as e:
                logger.warning(f"Redis get_recent_events error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        events = self._fallback_recent_events.get(user_id, [])
        # Return newest first
        return list(reversed(events[-limit:]))

    # =========================================================================
    # Statistics
    # =========================================================================

    async def update_subscription_stats(
        self,
        subscription_id: str,
        success: bool,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update delivery statistics for a subscription.

        Args:
            subscription_id: Subscription to update
            success: Whether delivery was successful
            error_message: Error message if failed

        Returns:
            True if updated successfully
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        now = datetime.utcnow().isoformat()
        updates = {
            "total_deliveries": subscription.total_deliveries + 1,
            "last_delivery_at": now,
        }

        if success:
            updates["successful_deliveries"] = subscription.successful_deliveries + 1
            updates["last_success_at"] = now
            updates["last_error"] = None
        else:
            updates["failed_deliveries"] = subscription.failed_deliveries + 1
            updates["last_failure_at"] = now
            updates["last_error"] = error_message

        return await self.update_subscription(subscription_id, updates)

    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        redis = await self._get_redis()
        stats = {
            "backend": "redis" if redis else "memory",
            "redis_available": redis is not None,
        }

        if not redis:
            stats["subscription_count"] = len(self._fallback_subscriptions)
            stats["delivery_count"] = len(self._fallback_deliveries)

        return stats


# Singleton instance
webhook_storage = WebhookStorage()
