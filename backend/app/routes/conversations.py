"""
Conversation endpoints.

Authorization:
- All endpoints require organization membership
- Read operations require content.view permission
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from src.organizations import AuthorizationContext

from ..auth import verify_api_key
from ..dependencies import require_content_access
from ..storage import conversations

router = APIRouter(tags=["conversations"])


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
):
    """
    Get conversation history by ID.

    Args:
        conversation_id: The conversation identifier.

    Returns:
        The conversation messages.

    Authorization: Requires content.view permission.
    """
    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    # Use organization_id for scoping if available, fallback to user_id
    scope_id = auth_ctx.organization_id or auth_ctx.user_id

    # Verify ownership (multi-tenant isolation)
    if not conversations.verify_ownership(conversation_id, scope_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this conversation",
        )

    return {"conversation": conversations.get(conversation_id)}
