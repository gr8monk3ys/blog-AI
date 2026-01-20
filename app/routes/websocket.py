"""
WebSocket endpoints for real-time communication.
"""

import json
import logging
import re
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models import WebSocketMessage
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time conversation updates.

    Args:
        websocket: The WebSocket connection.
        conversation_id: The conversation identifier.
    """
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

            # Add message to conversation (with persistence)
            conversations.append(conversation_id, message)

            # Broadcast message to all connected clients
            await manager.send_message({"type": "message", **message}, conversation_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(
            f"WebSocket error for conversation {conversation_id}: {str(e)}",
            exc_info=True,
        )
        manager.disconnect(websocket, conversation_id)
