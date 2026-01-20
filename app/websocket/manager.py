"""
WebSocket connection manager for real-time communication.
"""

import logging
from typing import Any, Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports multiple connections per conversation for broadcasting messages
    to all connected clients.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register.
            conversation_id: The conversation identifier.
        """
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        logger.debug(f"WebSocket connected for conversation: {conversation_id}")

    def disconnect(self, websocket: WebSocket, conversation_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove.
            conversation_id: The conversation identifier.
        """
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            # Clean up empty conversation lists
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        logger.debug(f"WebSocket disconnected for conversation: {conversation_id}")

    async def send_message(
        self, message: Dict[str, Any], conversation_id: str
    ) -> None:
        """
        Send a message to all connections in a conversation.

        Args:
            message: The message to send.
            conversation_id: The conversation identifier.
        """
        if conversation_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, conversation_id)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast.
        """
        for conversation_id in list(self.active_connections.keys()):
            await self.send_message(message, conversation_id)

    def get_connection_count(self, conversation_id: str) -> int:
        """
        Get the number of active connections for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            Number of active connections.
        """
        return len(self.active_connections.get(conversation_id, []))

    def get_total_connections(self) -> int:
        """
        Get the total number of active connections.

        Returns:
            Total number of active connections across all conversations.
        """
        return sum(len(conns) for conns in self.active_connections.values())


# Initialize connection manager singleton
manager = ConnectionManager()
