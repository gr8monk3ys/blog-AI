"""
Conversation endpoints.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import verify_api_key
from ..storage import conversations

router = APIRouter(tags=["conversations"])


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str, user_id: str = Depends(verify_api_key)
):
    """
    Get conversation history by ID.

    Args:
        conversation_id: The conversation identifier.
        user_id: The authenticated user ID.

    Returns:
        The conversation messages.
    """
    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    return {"conversation": conversations.get(conversation_id)}
