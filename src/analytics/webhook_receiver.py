"""
Webhook receiver for external platform performance data.

This module handles incoming webhooks from:
- WordPress (post views, comments)
- Medium (reads, claps)
- Mailchimp/email platforms (opens, clicks)
- Social platforms (shares, engagement)
- Custom integrations
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..types.performance import MetricType, PerformanceEvent

logger = logging.getLogger(__name__)


class WebhookReceiverError(Exception):
    """Exception raised for webhook processing errors."""

    pass


class WebhookReceiver:
    """
    Receiver for performance webhooks from external platforms.

    This class handles signature verification, payload parsing,
    and event normalization from various platforms.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        performance_service: Optional[Any] = None,
    ):
        """
        Initialize the webhook receiver.

        Args:
            secret_key: Secret key for webhook signature verification.
            performance_service: PerformanceService instance for event tracking.
        """
        self._secret_key = secret_key or os.environ.get("WEBHOOK_SECRET")
        self._performance_service = performance_service
        self._platform_handlers: Dict[str, Callable] = {
            "wordpress": self._handle_wordpress,
            "medium": self._handle_medium,
            "mailchimp": self._handle_mailchimp,
            "sendgrid": self._handle_sendgrid,
            "twitter": self._handle_twitter,
            "linkedin": self._handle_linkedin,
            "google_analytics": self._handle_google_analytics,
            "custom": self._handle_custom,
        }

    def _get_performance_service(self):
        """Get or create performance service."""
        if self._performance_service is not None:
            return self._performance_service

        from .performance_service import PerformanceService

        self._performance_service = PerformanceService()
        return self._performance_service

    # =========================================================================
    # Signature Verification
    # =========================================================================

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        platform: Optional[str] = None,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw request payload bytes.
            signature: Signature from webhook headers.
            platform: Optional platform for platform-specific verification.

        Returns:
            True if signature is valid.
        """
        if not self._secret_key:
            logger.warning("No webhook secret configured, skipping verification")
            return True

        try:
            # Different platforms use different signature schemes
            if platform == "mailchimp":
                # Mailchimp uses MD5
                expected = hashlib.md5(
                    (self._secret_key + payload.decode()).encode()
                ).hexdigest()
                return hmac.compare_digest(signature, expected)

            elif platform == "sendgrid":
                # SendGrid uses HMAC-SHA256 with timestamp
                # Signature format: "v1,timestamp,signature"
                parts = signature.split(",")
                if len(parts) == 3:
                    timestamp = parts[1]
                    sig = parts[2]
                    payload_to_sign = f"{timestamp}.{payload.decode()}"
                    expected = hmac.new(
                        self._secret_key.encode(),
                        payload_to_sign.encode(),
                        hashlib.sha256,
                    ).hexdigest()
                    return hmac.compare_digest(sig, expected)
                return False

            else:
                # Default: HMAC-SHA256
                expected = hmac.new(
                    self._secret_key.encode(),
                    payload,
                    hashlib.sha256,
                ).hexdigest()

                # Handle different signature formats
                if signature.startswith("sha256="):
                    signature = signature[7:]

                return hmac.compare_digest(signature, expected)

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    # =========================================================================
    # Main Processing
    # =========================================================================

    async def process_webhook(
        self,
        platform: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Process an incoming webhook.

        Args:
            platform: Source platform identifier.
            payload: Webhook payload.
            headers: Request headers for signature verification.

        Returns:
            Processing result dictionary.
        """
        logger.info(f"Processing webhook from platform: {platform}")

        handler = self._platform_handlers.get(platform.lower())
        if not handler:
            logger.warning(f"Unknown platform: {platform}, using custom handler")
            handler = self._handle_custom

        try:
            events = handler(payload)
            tracked_count = 0

            service = self._get_performance_service()
            for event in events:
                success = await service.track_event(event)
                if success:
                    tracked_count += 1

            return {
                "success": True,
                "platform": platform,
                "events_received": len(events),
                "events_tracked": tracked_count,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # =========================================================================
    # Platform-Specific Handlers
    # =========================================================================

    def _handle_wordpress(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle WordPress webhooks."""
        events = []

        event_type = payload.get("event_type") or payload.get("hook")

        if event_type in ["post_view", "post.view"]:
            events.append(
                PerformanceEvent(
                    event_type=MetricType.VIEW,
                    content_id=str(payload.get("post_id", "")),
                    source="webhook",
                    platform="wordpress",
                    metadata={
                        "post_title": payload.get("post_title"),
                        "post_url": payload.get("post_url"),
                    },
                    referrer=payload.get("referrer"),
                    user_agent=payload.get("user_agent"),
                )
            )

        elif event_type in ["comment_post", "comment.created"]:
            events.append(
                PerformanceEvent(
                    event_type=MetricType.COMMENT,
                    content_id=str(payload.get("post_id", "")),
                    source="webhook",
                    platform="wordpress",
                    metadata={
                        "comment_id": payload.get("comment_id"),
                        "comment_author": payload.get("author_name"),
                    },
                )
            )

        elif event_type in ["share", "post.share"]:
            events.append(
                PerformanceEvent(
                    event_type=MetricType.SHARE,
                    content_id=str(payload.get("post_id", "")),
                    source="webhook",
                    platform="wordpress",
                    metadata={
                        "share_platform": payload.get("share_platform"),
                    },
                )
            )

        return events

    def _handle_medium(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle Medium webhooks."""
        events = []

        # Medium post stats
        if "stats" in payload:
            stats = payload["stats"]
            post_id = payload.get("post_id") or payload.get("id")

            if stats.get("views"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.VIEW,
                        content_id=str(post_id),
                        value=float(stats["views"]),
                        source="webhook",
                        platform="medium",
                        metadata={
                            "title": payload.get("title"),
                            "url": payload.get("url"),
                        },
                    )
                )

            if stats.get("reads"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.UNIQUE_VIEW,
                        content_id=str(post_id),
                        value=float(stats["reads"]),
                        source="webhook",
                        platform="medium",
                    )
                )

            if stats.get("claps"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.SHARE,  # Claps as engagement
                        content_id=str(post_id),
                        value=float(stats["claps"]),
                        source="webhook",
                        platform="medium",
                        metadata={"claps": stats["claps"]},
                    )
                )

        return events

    def _handle_mailchimp(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle Mailchimp webhooks."""
        events = []

        event_type = payload.get("type")
        data = payload.get("data", {})

        # Map Mailchimp events to our types
        if event_type == "open":
            events.append(
                PerformanceEvent(
                    event_type=MetricType.VIEW,
                    content_id=data.get("campaign_id", ""),
                    source="webhook",
                    platform="mailchimp",
                    metadata={
                        "email_id": data.get("id"),
                        "list_id": data.get("list_id"),
                        "email": self._hash_email(data.get("email", "")),
                    },
                    timestamp=self._parse_timestamp(payload.get("fired_at")),
                )
            )

        elif event_type == "click":
            events.append(
                PerformanceEvent(
                    event_type=MetricType.CLICK,
                    content_id=data.get("campaign_id", ""),
                    source="webhook",
                    platform="mailchimp",
                    metadata={
                        "url": data.get("url"),
                        "list_id": data.get("list_id"),
                    },
                    timestamp=self._parse_timestamp(payload.get("fired_at")),
                )
            )

        return events

    def _handle_sendgrid(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle SendGrid webhooks (can be array of events)."""
        events = []

        # SendGrid sends arrays of events
        event_list = payload if isinstance(payload, list) else [payload]

        for event_data in event_list:
            event_type = event_data.get("event")

            if event_type == "open":
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.VIEW,
                        content_id=event_data.get("campaign_id", event_data.get("sg_message_id", "")),
                        source="webhook",
                        platform="sendgrid",
                        metadata={
                            "email": self._hash_email(event_data.get("email", "")),
                            "ip": event_data.get("ip"),
                            "useragent": event_data.get("useragent"),
                        },
                        timestamp=self._parse_timestamp(event_data.get("timestamp")),
                    )
                )

            elif event_type == "click":
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.CLICK,
                        content_id=event_data.get("campaign_id", event_data.get("sg_message_id", "")),
                        source="webhook",
                        platform="sendgrid",
                        metadata={
                            "url": event_data.get("url"),
                            "url_offset": event_data.get("url_offset", {}),
                        },
                        timestamp=self._parse_timestamp(event_data.get("timestamp")),
                    )
                )

        return events

    def _handle_twitter(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle Twitter/X webhooks."""
        events = []

        # Twitter Account Activity API format
        if "tweet_create_events" in payload:
            for tweet in payload["tweet_create_events"]:
                # Check if it's a retweet or quote of our content
                if tweet.get("retweeted_status") or tweet.get("is_quote_status"):
                    events.append(
                        PerformanceEvent(
                            event_type=MetricType.SHARE,
                            content_id=tweet.get("retweeted_status", {}).get("id_str", ""),
                            source="webhook",
                            platform="twitter",
                            metadata={
                                "tweet_id": tweet.get("id_str"),
                                "retweet_count": tweet.get("retweet_count"),
                                "favorite_count": tweet.get("favorite_count"),
                            },
                        )
                    )

        # Twitter Analytics API format
        if "engagement" in payload:
            content_id = payload.get("tweet_id") or payload.get("content_id")
            engagement = payload["engagement"]

            if engagement.get("impressions"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.VIEW,
                        content_id=str(content_id),
                        value=float(engagement["impressions"]),
                        source="webhook",
                        platform="twitter",
                    )
                )

            if engagement.get("retweets"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.SHARE,
                        content_id=str(content_id),
                        value=float(engagement["retweets"]),
                        source="webhook",
                        platform="twitter",
                    )
                )

        return events

    def _handle_linkedin(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle LinkedIn webhooks."""
        events = []

        # LinkedIn Share Statistics
        if "statistics" in payload:
            stats = payload["statistics"]
            content_id = payload.get("share_urn") or payload.get("activity")

            if stats.get("impressionCount"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.VIEW,
                        content_id=str(content_id),
                        value=float(stats["impressionCount"]),
                        source="webhook",
                        platform="linkedin",
                    )
                )

            if stats.get("shareCount"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.SHARE,
                        content_id=str(content_id),
                        value=float(stats["shareCount"]),
                        source="webhook",
                        platform="linkedin",
                    )
                )

            if stats.get("clickCount"):
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.CLICK,
                        content_id=str(content_id),
                        value=float(stats["clickCount"]),
                        source="webhook",
                        platform="linkedin",
                    )
                )

        return events

    def _handle_google_analytics(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle Google Analytics webhooks/exports."""
        events = []

        # Handle GA4 export format
        rows = payload.get("rows", [payload])

        for row in rows:
            content_id = (
                row.get("pagePath") or
                row.get("page_path") or
                row.get("content_id")
            )

            if not content_id:
                continue

            metrics = row.get("metrics", row)

            if metrics.get("screenPageViews") or metrics.get("pageviews"):
                views = metrics.get("screenPageViews") or metrics.get("pageviews")
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.VIEW,
                        content_id=str(content_id),
                        value=float(views),
                        source="webhook",
                        platform="google_analytics",
                        metadata={
                            "source": metrics.get("source"),
                            "medium": metrics.get("medium"),
                        },
                    )
                )

            if metrics.get("activeUsers") or metrics.get("users"):
                users = metrics.get("activeUsers") or metrics.get("users")
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.UNIQUE_VIEW,
                        content_id=str(content_id),
                        value=float(users),
                        source="webhook",
                        platform="google_analytics",
                    )
                )

            if metrics.get("averageSessionDuration") or metrics.get("avgTimeOnPage"):
                duration = metrics.get("averageSessionDuration") or metrics.get("avgTimeOnPage")
                events.append(
                    PerformanceEvent(
                        event_type=MetricType.TIME_ON_PAGE,
                        content_id=str(content_id),
                        value=float(duration),
                        source="webhook",
                        platform="google_analytics",
                    )
                )

        return events

    def _handle_custom(self, payload: Dict[str, Any]) -> List[PerformanceEvent]:
        """Handle custom/generic webhooks."""
        events = []

        # Expect a standardized format
        content_id = payload.get("content_id")
        if not content_id:
            logger.warning("Custom webhook missing content_id")
            return events

        event_type_str = payload.get("event_type", "view")

        # Map string to MetricType
        event_type_map = {
            "view": MetricType.VIEW,
            "unique_view": MetricType.UNIQUE_VIEW,
            "time_on_page": MetricType.TIME_ON_PAGE,
            "scroll_depth": MetricType.SCROLL_DEPTH,
            "bounce": MetricType.BOUNCE,
            "share": MetricType.SHARE,
            "click": MetricType.CLICK,
            "conversion": MetricType.CONVERSION,
            "comment": MetricType.COMMENT,
            "backlink": MetricType.BACKLINK,
        }

        event_type = event_type_map.get(event_type_str.lower(), MetricType.VIEW)

        events.append(
            PerformanceEvent(
                event_type=event_type,
                content_id=str(content_id),
                value=float(payload.get("value", 1)),
                user_id=payload.get("user_id"),
                session_id=payload.get("session_id"),
                source="webhook",
                platform=payload.get("platform", "custom"),
                metadata=payload.get("metadata", {}),
                timestamp=self._parse_timestamp(payload.get("timestamp")),
            )
        )

        return events

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _hash_email(self, email: str) -> str:
        """Hash email for privacy-compliant storage."""
        if not email:
            return ""
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]

    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse timestamp from various formats."""
        if ts is None:
            return datetime.utcnow()

        if isinstance(ts, datetime):
            return ts

        if isinstance(ts, (int, float)):
            # Unix timestamp
            return datetime.utcfromtimestamp(ts)

        if isinstance(ts, str):
            # Try ISO format
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass

            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    continue

        return datetime.utcnow()

    def register_handler(
        self,
        platform: str,
        handler: Callable[[Dict[str, Any]], List[PerformanceEvent]],
    ) -> None:
        """
        Register a custom platform handler.

        Args:
            platform: Platform identifier.
            handler: Function that takes payload and returns list of events.
        """
        self._platform_handlers[platform.lower()] = handler
        logger.info(f"Registered custom handler for platform: {platform}")
