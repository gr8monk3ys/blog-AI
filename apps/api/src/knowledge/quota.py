"""
Knowledge Base tier-based quota enforcement.

Checks document count and storage limits based on the user's subscription tier
before allowing uploads.

Tier limits (configurable via KnowledgeBaseSettings):
- Free:    2 documents / 5 MB
- Starter: 20 documents / 50 MB
- Pro:     Unlimited
"""

import logging
from typing import Optional

from .knowledge_service import KnowledgeBaseError

logger = logging.getLogger(__name__)


class KBQuotaExceededError(KnowledgeBaseError):
    """Raised when a KB upload would exceed the user's tier limits."""

    def __init__(self, message: str, tier: str, upgrade_message: Optional[str] = None):
        self.tier = tier
        self.upgrade_message = upgrade_message
        super().__init__(message, operation="quota_check")


async def _get_user_tier(user_id: str) -> str:
    """
    Get the user's subscription tier.

    Queries the existing quota/usage system. Falls back to 'free' if unavailable.
    """
    try:
        from ..db import get_pool

        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT tier FROM user_subscriptions
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    user_id,
                )
                if row:
                    return row["tier"]
    except Exception as e:
        logger.debug(f"Could not determine user tier, defaulting to free: {e}")

    return "free"


async def _get_kb_usage(user_id: str) -> dict:
    """Get current KB usage from kb_usage_stats view."""
    try:
        from ..db import get_pool

        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM kb_usage_stats WHERE user_id = $1",
                    user_id,
                )
                if row:
                    return {
                        "document_count": row["document_count"],
                        "total_storage_bytes": row["total_storage_bytes"],
                    }
    except Exception as e:
        logger.debug(f"Could not query KB usage stats: {e}")

    return {"document_count": 0, "total_storage_bytes": 0}


async def check_kb_quota(user_id: str, additional_bytes: int = 0) -> None:
    """
    Check whether the user can upload another document to the KB.

    Args:
        user_id: The user/org ID to check.
        additional_bytes: Size of the new file in bytes.

    Raises:
        KBQuotaExceededError: If the upload would exceed the user's tier limits.
    """
    from ..config import get_settings

    settings = get_settings()
    kb = settings.knowledge_base

    tier = await _get_user_tier(user_id)
    usage = await _get_kb_usage(user_id)

    current_docs = usage["document_count"]
    current_bytes = usage["total_storage_bytes"]

    # Determine limits based on tier
    if tier in ("pro", "business"):
        # Unlimited
        return
    elif tier == "starter":
        max_docs = kb.kb_starter_max_docs
        max_bytes = kb.kb_starter_max_storage_mb * 1024 * 1024
    else:
        # Free tier
        max_docs = kb.kb_free_max_docs
        max_bytes = kb.kb_free_max_storage_mb * 1024 * 1024

    # Check document count
    if current_docs >= max_docs:
        raise KBQuotaExceededError(
            f"Document limit reached ({current_docs}/{max_docs}). "
            f"Upgrade to {'Pro' if tier == 'starter' else 'Starter'} for more.",
            tier=tier,
            upgrade_message=(
                f"Your {tier} plan allows {max_docs} documents. "
                f"Upgrade to upload more."
            ),
        )

    # Check storage
    if (current_bytes + additional_bytes) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        current_mb = current_bytes / (1024 * 1024)
        raise KBQuotaExceededError(
            f"Storage limit reached ({current_mb:.1f}MB/{max_mb}MB). "
            f"Upgrade for more storage.",
            tier=tier,
            upgrade_message=(
                f"Your {tier} plan allows {max_mb}MB of storage. "
                f"Upgrade to upload more documents."
            ),
        )
