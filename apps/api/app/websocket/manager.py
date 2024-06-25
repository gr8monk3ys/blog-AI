"""
WebSocket connection manager for real-time communication.

Supports streaming text generation with token-by-token delivery.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    websocket: WebSocket
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    subscribed_streams: Set[str] = field(default_factory=set)
    message_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports multiple connections per conversation for broadcasting messages
    to all connected clients. Enhanced with streaming support for token-by-token
    delivery of LLM responses.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._connection_info: Dict[str, Dict[WebSocket, ConnectionInfo]] = {}
        self._stream_subscriptions: Dict[str, Set[str]] = {}  # stream_id -> conversation_ids
        self._message_queue: Dict[str, asyncio.Queue] = {}
        self._batch_lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register.
            conversation_id: The conversation identifier.
            user_id: Optional user ID for the connection.
        """
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
            self._connection_info[conversation_id] = {}
        self.active_connections[conversation_id].append(websocket)

        # Store connection info
        self._connection_info[conversation_id][websocket] = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
        )

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

            # Clean up connection info
            if conversation_id in self._connection_info:
                conn_info = self._connection_info[conversation_id].pop(websocket, None)
                if conn_info:
                    # Unsubscribe from any streams
                    for stream_id in conn_info.subscribed_streams:
                        self._unsubscribe_from_stream(stream_id, conversation_id)

            # Clean up empty conversation lists
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
                if conversation_id in self._connection_info:
                    del self._connection_info[conversation_id]

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

    async def subscribe_to_stream(
        self,
        stream_id: str,
        conversation_id: str,
        websocket: Optional[WebSocket] = None,
    ) -> None:
        """
        Subscribe a conversation (or specific connection) to a stream.

        Args:
            stream_id: The stream identifier to subscribe to.
            conversation_id: The conversation to subscribe.
            websocket: Optional specific WebSocket to subscribe.
        """
        if stream_id not in self._stream_subscriptions:
            self._stream_subscriptions[stream_id] = set()
        self._stream_subscriptions[stream_id].add(conversation_id)

        # Track subscription in connection info if websocket specified
        if websocket and conversation_id in self._connection_info:
            conn_info = self._connection_info[conversation_id].get(websocket)
            if conn_info:
                conn_info.subscribed_streams.add(stream_id)

        logger.debug(f"Conversation {conversation_id} subscribed to stream {stream_id}")

    def _unsubscribe_from_stream(
        self,
        stream_id: str,
        conversation_id: str,
    ) -> None:
        """
        Internal method to unsubscribe from a stream.

        Args:
            stream_id: The stream identifier.
            conversation_id: The conversation to unsubscribe.
        """
        if stream_id in self._stream_subscriptions:
            self._stream_subscriptions[stream_id].discard(conversation_id)
            if not self._stream_subscriptions[stream_id]:
                del self._stream_subscriptions[stream_id]

    async def unsubscribe_from_stream(
        self,
        stream_id: str,
        conversation_id: str,
    ) -> None:
        """
        Unsubscribe a conversation from a stream.

        Args:
            stream_id: The stream identifier.
            conversation_id: The conversation to unsubscribe.
        """
        self._unsubscribe_from_stream(stream_id, conversation_id)

        # Remove from connection info
        if conversation_id in self._connection_info:
            for conn_info in self._connection_info[conversation_id].values():
                conn_info.subscribed_streams.discard(stream_id)

        logger.debug(
            f"Conversation {conversation_id} unsubscribed from stream {stream_id}"
        )

    async def send_stream_token(
        self,
        stream_id: str,
        token: str,
        token_index: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a streaming token to all subscribed connections.

        Args:
            stream_id: The stream identifier.
            token: The token content.
            token_index: The index of this token in the stream.
            metadata: Optional additional metadata.
        """
        if stream_id not in self._stream_subscriptions:
            return

        message = {
            "type": "stream_token",
            "stream_id": stream_id,
            "content": token,
            "token_index": token_index,
        }
        if metadata:
            message["metadata"] = metadata

        for conversation_id in self._stream_subscriptions[stream_id]:
            await self.send_message(message, conversation_id)

    async def send_stream_event(
        self,
        stream_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a stream lifecycle event to all subscribed connections.

        Args:
            stream_id: The stream identifier.
            event_type: The type of event (start, end, error, etc.).
            data: Optional event data.
        """
        if stream_id not in self._stream_subscriptions:
            return

        message = {
            "type": f"stream_{event_type}",
            "stream_id": stream_id,
        }
        if data:
            message.update(data)

        for conversation_id in self._stream_subscriptions[stream_id]:
            await self.send_message(message, conversation_id)

    async def send_batched_tokens(
        self,
        stream_id: str,
        tokens: List[str],
        start_index: int,
    ) -> None:
        """
        Send multiple tokens in a single message for efficiency.

        Useful for high-frequency token delivery to reduce WebSocket overhead.

        Args:
            stream_id: The stream identifier.
            tokens: List of token strings.
            start_index: The starting token index.
        """
        if stream_id not in self._stream_subscriptions:
            return

        message = {
            "type": "stream_tokens_batch",
            "stream_id": stream_id,
            "tokens": tokens,
            "start_index": start_index,
            "count": len(tokens),
        }

        for conversation_id in self._stream_subscriptions[stream_id]:
            await self.send_message(message, conversation_id)

    def get_stream_subscribers(self, stream_id: str) -> Set[str]:
        """
        Get all conversation IDs subscribed to a stream.

        Args:
            stream_id: The stream identifier.

        Returns:
            Set of conversation IDs.
        """
        return self._stream_subscriptions.get(stream_id, set()).copy()

    def get_connection_info(
        self,
        conversation_id: str,
        websocket: WebSocket,
    ) -> Optional[ConnectionInfo]:
        """
        Get connection info for a specific WebSocket.

        Args:
            conversation_id: The conversation identifier.
            websocket: The WebSocket connection.

        Returns:
            ConnectionInfo if found, None otherwise.
        """
        if conversation_id in self._connection_info:
            return self._connection_info[conversation_id].get(websocket)
        return None

    def update_activity(self, conversation_id: str, websocket: WebSocket) -> None:
        """
        Update the last activity timestamp for a connection.

        Args:
            conversation_id: The conversation identifier.
            websocket: The WebSocket connection.
        """
        conn_info = self.get_connection_info(conversation_id, websocket)
        if conn_info:
            conn_info.last_activity = datetime.utcnow()
            conn_info.message_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the connection manager.

        Returns:
            Dictionary with connection statistics.
        """
        total_connections = self.get_total_connections()
        total_conversations = len(self.active_connections)
        total_streams = len(self._stream_subscriptions)
        total_subscriptions = sum(
            len(subs) for subs in self._stream_subscriptions.values()
        )

        return {
            "total_connections": total_connections,
            "total_conversations": total_conversations,
            "active_streams": total_streams,
            "stream_subscriptions": total_subscriptions,
            "connections_by_conversation": {
                conv_id: len(conns)
                for conv_id, conns in self.active_connections.items()
            },
        }


# Initialize connection manager singleton
manager = ConnectionManager()
