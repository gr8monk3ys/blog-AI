"""
Background worker for social media post publishing.

Runs as a background job to:
- Poll for scheduled posts that are due
- Publish posts asynchronously
- Handle retries and failures
- Send webhook notifications
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SocialPublishingWorker:
    """
    Background worker for publishing scheduled social media posts.

    Uses APScheduler for scheduling tasks and handles graceful shutdown.
    """

    def __init__(
        self,
        poll_interval_seconds: int = 30,
        batch_size: int = 10,
        max_concurrent: int = 5,
    ) -> None:
        """
        Initialize the worker.

        Args:
            poll_interval_seconds: How often to poll for due posts
            batch_size: Max posts to process per poll
            max_concurrent: Max concurrent publishing tasks
        """
        self._poll_interval = poll_interval_seconds
        self._batch_size = batch_size
        self._max_concurrent = max_concurrent

        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Webhook callbacks
        self._webhook_callbacks: List[Callable] = []

        # Metrics
        self._metrics = {
            "posts_processed": 0,
            "posts_published": 0,
            "posts_failed": 0,
            "last_poll_at": None,
            "started_at": None,
        }

        logger.info(
            f"Worker initialized (poll_interval={poll_interval_seconds}s, "
            f"batch_size={batch_size}, max_concurrent={max_concurrent})"
        )

    @property
    def is_running(self) -> bool:
        """Check if worker is currently running."""
        return self._running

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get worker metrics."""
        return {**self._metrics, "is_running": self._running}

    def add_webhook_callback(
        self,
        callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        """
        Add a webhook callback for publishing events.

        Args:
            callback: Function to call with event data
        """
        self._webhook_callbacks.append(callback)

    async def _notify_webhooks(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Send notifications to registered webhooks."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        for callback in self._webhook_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    await asyncio.to_thread(callback, event)
            except Exception as e:
                logger.warning(f"Webhook callback failed: {e}")

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            logger.warning("Worker is already running")
            return

        self._running = True
        self._metrics["started_at"] = datetime.utcnow()

        logger.info("Starting social publishing worker")

        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._handle_shutdown)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

        # Start the main loop
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Stop the background worker gracefully.

        Args:
            timeout: Max seconds to wait for current tasks to complete
        """
        if not self._running:
            return

        logger.info("Stopping social publishing worker")
        self._running = False

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Worker stop timed out, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Worker stopped")

    def _handle_shutdown(self) -> None:
        """Handle shutdown signal."""
        logger.info("Received shutdown signal")
        self._running = False

    async def _run_loop(self) -> None:
        """Main worker loop."""
        logger.info("Worker loop started")

        while self._running:
            try:
                await self._poll_and_process()
                self._metrics["last_poll_at"] = datetime.utcnow()
            except Exception as e:
                logger.exception(f"Error in worker loop: {e}")

            # Sleep until next poll
            await asyncio.sleep(self._poll_interval)

        logger.info("Worker loop ended")

    async def _poll_and_process(self) -> None:
        """Poll for due posts and process them."""
        from .publisher import publisher_service
        from .scheduler import scheduler_service

        # Get posts that are due
        due_posts = await scheduler_service.get_due_posts(limit=self._batch_size)

        if not due_posts:
            return

        logger.info(f"Found {len(due_posts)} posts due for publishing")

        # Create publishing tasks
        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def process_post(post):
            async with semaphore:
                await self._publish_post(post)

        tasks = [process_post(post) for post in due_posts]

        # Execute with gather
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _publish_post(self, post) -> None:
        """
        Publish a single post.

        Args:
            post: The scheduled post to publish
        """
        from .publisher import publisher_service
        from .scheduler import scheduler_service
        from src.types.social import PostStatus

        self._metrics["posts_processed"] += 1

        logger.info(f"Publishing post {post.id} to {post.platform.value}")

        # Get the account
        account = await scheduler_service.get_account(post.account_id)
        if not account:
            logger.error(f"Account {post.account_id} not found for post {post.id}")
            post.status = PostStatus.FAILED
            post.error_message = "Account not found"
            await scheduler_service._store_scheduled_post(post)
            self._metrics["posts_failed"] += 1
            return

        # Mark as publishing
        post.status = PostStatus.PUBLISHING
        await scheduler_service._store_scheduled_post(post)

        # Attempt to publish with retry
        success, platform_post_id, error = await publisher_service.publish_with_retry(
            post=post,
            account=account,
        )

        # Update post
        await scheduler_service._store_scheduled_post(post)

        if success:
            self._metrics["posts_published"] += 1
            logger.info(f"Successfully published post {post.id} as {platform_post_id}")

            await self._notify_webhooks("post.published", {
                "post_id": post.id,
                "platform": post.platform.value,
                "platform_post_id": platform_post_id,
                "platform_post_url": post.platform_post_url,
            })

            # Check if campaign is complete
            if post.campaign_id:
                await self._check_campaign_completion(post.campaign_id)
        else:
            self._metrics["posts_failed"] += 1
            logger.error(f"Failed to publish post {post.id}: {error}")

            await self._notify_webhooks("post.failed", {
                "post_id": post.id,
                "platform": post.platform.value,
                "error": error,
            })

    async def _check_campaign_completion(self, campaign_id: str) -> None:
        """Check if a campaign should be marked complete."""
        from .campaign_service import campaign_service

        try:
            is_complete = await campaign_service.check_campaign_completion(campaign_id)
            if is_complete:
                await campaign_service.complete_campaign(campaign_id)
                logger.info(f"Campaign {campaign_id} marked as complete")

                await self._notify_webhooks("campaign.completed", {
                    "campaign_id": campaign_id,
                })
        except Exception as e:
            logger.warning(f"Error checking campaign completion: {e}")


# Global worker instance
worker = SocialPublishingWorker()


async def run_worker() -> None:
    """Run the worker as a standalone process."""
    import os

    # Configure logging
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting social publishing worker process")

    # Check if scheduler is enabled
    if os.environ.get("SOCIAL_SCHEDULER_ENABLED", "true").lower() != "true":
        logger.warning("Social scheduler is disabled (SOCIAL_SCHEDULER_ENABLED != true)")
        return

    # Configure worker
    poll_interval = int(os.environ.get("SOCIAL_WORKER_POLL_INTERVAL", "30"))
    batch_size = int(os.environ.get("SOCIAL_WORKER_BATCH_SIZE", "10"))
    max_concurrent = int(os.environ.get("SOCIAL_WORKER_MAX_CONCURRENT", "5"))

    global worker
    worker = SocialPublishingWorker(
        poll_interval_seconds=poll_interval,
        batch_size=batch_size,
        max_concurrent=max_concurrent,
    )

    # Add webhook callback if configured
    webhook_url = os.environ.get("SOCIAL_WEBHOOK_URL")
    if webhook_url:
        import httpx

        async def webhook_callback(event: Dict[str, Any]) -> None:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        webhook_url,
                        json=event,
                        timeout=30.0,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send webhook: {e}")

        worker.add_webhook_callback(webhook_callback)

    # Start worker
    await worker.start()

    # Keep running until stopped
    try:
        while worker.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await worker.stop()


def main() -> None:
    """Entry point for running worker as standalone script."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
