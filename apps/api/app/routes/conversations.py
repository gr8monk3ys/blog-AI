"""
Conversation endpoints.

Authorization:
- All endpoints require organization membership
- Read operations require content.view permission
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from src.organizations import AuthorizationContext

from ..dependencies.organization import get_optional_organization_context
from ..storage import conversations

router = APIRouter(tags=["conversations"])


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Get conversation history by ID.

    Args:
        conversation_id: The conversation identifier.

    Returns:
        The conversation messages.

    Authorization:
        Requires authentication (API key or Bearer token).
        If X-Organization-ID is provided, scope will be organization-specific
        only when the user is a member of that organization.
    """
    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    # Scope to org only if the user is actually a member; otherwise fall back to user scope.
    scope_id = (
        auth_ctx.organization_id
        if auth_ctx.organization_id and auth_ctx.is_org_member
        else auth_ctx.user_id
    )

    # Verify ownership (multi-tenant isolation)
    if not conversations.verify_ownership(conversation_id, scope_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this conversation",
        )

    return {"conversation": conversations.get(conversation_id)}
