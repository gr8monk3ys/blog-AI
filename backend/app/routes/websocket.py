"""
WebSocket endpoints for real-time communication.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..auth.api_key import api_key_store
from ..error_handlers import sanitize_error_message
from ..models import WebSocketMessage
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)


def _is_dev_api_key_active() -> bool:
    """Check if DEV_API_KEY is configured and safe to use (non-production only)."""
    dev_api_key = os.environ.get("DEV_API_KEY")
    if not dev_api_key:
        return False

    # Block in production
    if os.environ.get("SENTRY_ENVIRONMENT", "").lower() == "production":
        return False
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        return False
    return True


async def authenticate_websocket(
    websocket: WebSocket,
) -> Optional[str]:
    """
    Authenticate a WebSocket connection using the first message.

    Security: API keys are received via the WebSocket message payload
    instead of query parameters, which avoids exposing credentials in
    server access logs, browser history, and intermediary proxy logs.

    Protocol:
        1. Server accepts the WebSocket connection.
        2. Client sends a JSON authentication message as the first frame:
           {"type": "auth", "api_key": "<key>"}
        3. Server validates the key and responds with:
           {"type": "auth_result", "success": true/false}
        4. On failure the connection is closed with code 4001.

    Returns:
        user_id if authenticated, None otherwise
    """
    # Accept the connection so the client can send the auth message
    await websocket.accept()

    # Check DEV_API_KEY first (non-production only)
    if _is_dev_api_key_active():
        return "dev_user"

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        auth_msg = json.loads(raw)

        if auth_msg.get("type") != "auth" or not auth_msg.get("api_key"):
            await websocket.send_json(
                {"type": "auth_result", "success": False, "detail": "Invalid auth message format"}
            )
            await websocket.close(code=4001, reason="Invalid auth message")
            return None

        api_key = auth_msg["api_key"]
        user_id = api_key_store.verify_key(api_key)

        if not user_id:
            await websocket.send_json(
                {"type": "auth_result", "success": False, "detail": "Invalid API key"}
            )
            await websocket.close(code=4001, reason="Invalid API key")
            return None

        await websocket.send_json({"type": "auth_result", "success": True})
        return user_id

    except asyncio.TimeoutError:
        await websocket.close(code=4001, reason="Authentication timeout")
        return None
    except (json.JSONDecodeError, KeyError):
        await websocket.close(code=4001, reason="Invalid auth message")
        return None

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
):
    """
    WebSocket endpoint for real-time conversation updates.

    Authentication is performed via the first WebSocket message:
    Client sends: {"type": "auth", "api_key": "<key>"}
    Server responds: {"type": "auth_result", "success": true/false}
    """
    # Authenticate the WebSocket connection (accepts and reads first message)
    user_id = await authenticate_websocket(websocket)
    if not user_id:
        return  # Connection already closed in authenticate_websocket

    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        await websocket.close(code=4000, reason="Invalid conversation ID format")
        return

    # WebSocket was already accepted during authentication.
    # Register with the connection manager without re-accepting.
    if conversation_id in manager.active_connections:
        existing_user_ids = [
            getattr(conn, '_user_id', None) 
            for conn in manager.active_connections[conversation_id]
        ]
        if existing_user_ids and user_id not in existing_user_ids and None not in existing_user_ids:
            await websocket.close(code=4003, reason="Not authorized for this conversation")
            return

    if conversation_id not in manager.active_connections:
        manager.active_connections[conversation_id] = []
    manager.active_connections[conversation_id].append(websocket)
    websocket._user_id = user_id
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
                await websocket.send_json({"type": "error", "detail": sanitize_error_message(str(e))})
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
