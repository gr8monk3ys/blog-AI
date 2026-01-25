"""
WebSocket endpoints for real-time communication.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..auth.api_key import api_key_store
from ..models import WebSocketMessage
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)


def _is_dev_mode_active() -> bool:
    """Check if DEV_MODE is active and safe to use."""
    dev_mode_requested = os.environ.get("DEV_MODE", "false").lower() == "true"
    if not dev_mode_requested:
        return False

    # Check production indicators (same as api_key.py)
    if os.environ.get("SENTRY_ENVIRONMENT", "").lower() == "production":
        return False
    if os.environ.get("HTTPS_REDIRECT_ENABLED", "false").lower() == "true":
        return False
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if stripe_key.startswith("sk_live_"):
        return False
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")
    if allowed_origins:
        for origin in allowed_origins.split(","):
            origin = origin.strip().lower()
            if origin and "localhost" not in origin and "127.0.0.1" not in origin:
                return False
    return True


async def authenticate_websocket(
    websocket: WebSocket,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Authenticate a WebSocket connection.

    Args:
        websocket: The WebSocket connection to authenticate
        api_key: API key from query parameter

    Returns:
        user_id if authenticated, None otherwise
    """
    # Check DEV_MODE first
    if _is_dev_mode_active():
        return "dev_user"

    if not api_key:
        await websocket.close(code=4001, reason="Missing API key")
        return None

    user_id = api_key_store.verify_key(api_key)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid API key")
        return None

    return user_id

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    api_key: Optional[str] = Query(None, alias="api_key"),
):
    """
    WebSocket endpoint for real-time conversation updates.

    Args:
        websocket: The WebSocket connection.
        conversation_id: The conversation identifier.
        api_key: API key for authentication (query parameter).
    """
    # Authenticate the WebSocket connection
    user_id = await authenticate_websocket(websocket, api_key)
    if not user_id:
        return  # Connection already closed in authenticate_websocket

    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        await websocket.close(code=4000, reason="Invalid conversation ID format")
        return

    await manager.connect(websocket, conversation_id)
    logger.info(f"WebSocket connected for conversation: {conversation_id}")

    try:
        while True:
            data = await websocket.receive_text()

            # Parse and validate message
            try:
                raw_message = json.loads(data)
                # Validate message structure
                message = WebSocketMessage(**raw_message).model_dump()
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received on WebSocket: {conversation_id}")
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON format"}
                )
                continue
            except ValueError as e:
                logger.warning(f"Invalid message format on WebSocket: {str(e)}")
                await websocket.send_json({"type": "error", "detail": str(e)})
                continue

            # Add timestamp if not present
            if not message.get("timestamp"):
                message["timestamp"] = datetime.now().isoformat()

            # Add message to conversation (with persistence and ownership)
            conversations.append(conversation_id, message, user_id=user_id)

            # Broadcast message to all connected clients
            await manager.send_message({"type": "message", **message}, conversation_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
        manager.disconnect(websocket, conversation_id)
    except ConnectionResetError as e:
        logger.warning(f"WebSocket connection reset for {conversation_id}: {str(e)}")
        manager.disconnect(websocket, conversation_id)
    except TimeoutError as e:
        logger.warning(f"WebSocket timeout for {conversation_id}: {str(e)}")
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(
            f"Unexpected WebSocket error for conversation {conversation_id}: {str(e)}",
            exc_info=True,
        )
        manager.disconnect(websocket, conversation_id)
