"""
Background scheduler for subscription reconciliation.

Runs the Stripe-to-database subscription reconciliation on a configurable
interval (default: every 24 hours at ~3 AM UTC). Designed to be started
from server.py as a non-blocking asyncio background task.

Configuration:
    RECONCILIATION_INTERVAL_HOURS - Hours between runs (default: 24)
    RECONCILIATION_ENABLED - Set to "false" to disable (default: true)
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _env_true(name: str, default: bool = True) -> bool:
    """Read a boolean env var."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_interval_hours() -> float:
    """Get the reconciliation interval from env (default 24 hours)."""
    try:
        return float(os.environ.get("RECONCILIATION_INTERVAL_HOURS", "24"))
    except (ValueError, TypeError):
        return 24.0


def _seconds_until_3am_utc() -> float:
    """
    Calculate seconds until the next 3:00 AM UTC.

    On first startup we wait until 3 AM so the heavy reconciliation
    does not run during peak traffic hours.
    """
    now = datetime.now(timezone.utc)
    target = now.replace(hour=3, minute=0, second=0, microsecond=0)
    if target <= now:
        # Already past 3 AM today, schedule for tomorrow
        from datetime import timedelta
        target = target + timedelta(days=1)
    delta = (target - now).total_seconds()
    return max(delta, 0)


async def _run_reconciliation() -> None:
    """Execute a single reconciliation run and log the results."""
    try:
        from src.payments.subscription_sync import get_sync_service

        sync_service = get_sync_service()
        result = await sync_service.reconcile_subscriptions(
            skip_manual_overrides=True,
            dry_run=False,
        )

        logger.info(
            "Scheduled reconciliation completed: "
            f"checked={result.get('checked', 0)}, "
            f"mismatches={result.get('mismatches_found', 0)}, "
            f"fixed={result.get('fixed', 0)}, "
            f"errors={result.get('errors', 0)}"
        )
    except Exception as e:
        logger.error(f"Scheduled reconciliation failed: {e}", exc_info=True)


async def start_reconciliation_scheduler() -> None:
    """
    Start the background reconciliation loop.

    This coroutine never returns (runs until the event loop is cancelled).
    It is safe to call from a FastAPI lifespan or on_startup hook via
    ``asyncio.create_task()``.

    Behaviour:
    1. Wait until 3 AM UTC on the first run so the initial sweep happens
       during low-traffic hours.
    2. After the first run, repeat every ``RECONCILIATION_INTERVAL_HOURS``.
    """
    if not _env_true("RECONCILIATION_ENABLED", default=True):
        logger.info("Reconciliation scheduler disabled (RECONCILIATION_ENABLED=false)")
        return

    interval_hours = _get_interval_hours()
    interval_seconds = interval_hours * 3600

    # Wait until 3 AM UTC for the first run
    initial_delay = _seconds_until_3am_utc()
    logger.info(
        f"Reconciliation scheduler started: first run in "
        f"{initial_delay / 3600:.1f}h, then every {interval_hours}h"
    )

    await asyncio.sleep(initial_delay)

    while True:
        await _run_reconciliation()
        await asyncio.sleep(interval_seconds)
