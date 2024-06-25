"""
Streaming service for bridging LLM streaming to WebSocket.

This service manages streaming text generation and delivers tokens
to connected WebSocket clients in real-time.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from src.text_generation import (
    GenerationOptions,
    StreamEvent,
    StreamEventType,
    StreamingError,
    create_provider_from_env,
    stream_text,
)
from src.types.providers import LLMProvider, ProviderType

from ..websocket import manager

logger = logging.getLogger(__name__)


class StreamStatus(str, Enum):
    """Status of a streaming session."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class StreamSession:
    """Represents an active streaming session."""

    session_id: str
    conversation_id: str
    user_id: str
    prompt: str
    provider_type: ProviderType
    options: GenerationOptions
    status: StreamStatus = StreamStatus.PENDING
    accumulated_content: str = ""
    token_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    def cancel(self) -> None:
        """Signal cancellation of this streaming session."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check if this session has been cancelled."""
        return self._cancel_event.is_set()


class StreamingService:
    """
    Service for managing streaming text generation sessions.

    Handles the lifecycle of streaming sessions, including:
    - Starting new streams
    - Delivering tokens via WebSocket
    - Cancelling streams
    - Tracking session state
    """

    def __init__(self):
        """Initialize the streaming service."""
        self._sessions: Dict[str, StreamSession] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._session_lock = asyncio.Lock()
        # Callbacks for stream events
        self._on_token_callbacks: List[Callable[[str, StreamSession, str], None]] = []
        self._on_complete_callbacks: List[Callable[[str, StreamSession], None]] = []
        self._on_error_callbacks: List[Callable[[str, StreamSession, str], None]] = []

    async def start_stream(
        self,
        conversation_id: str,
        user_id: str,
        prompt: str,
        provider_type: ProviderType = "openai",
        options: Optional[GenerationOptions] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StreamSession:
        """
        Start a new streaming text generation session.

        Args:
            conversation_id: The conversation this stream belongs to.
            user_id: The user who initiated the stream.
            prompt: The prompt to generate text from.
            provider_type: The LLM provider to use.
            options: Generation options.
            session_id: Optional custom session ID.
            metadata: Optional metadata to attach to the session.

        Returns:
            The created StreamSession.

        Raises:
            StreamingError: If unable to start the stream.
        """
        session_id = session_id or str(uuid.uuid4())
        options = options or GenerationOptions()

        session = StreamSession(
            session_id=session_id,
            conversation_id=conversation_id,
            user_id=user_id,
            prompt=prompt,
            provider_type=provider_type,
            options=options,
            metadata=metadata or {},
        )

        async with self._session_lock:
            self._sessions[session_id] = session

        # Start the streaming task
        task = asyncio.create_task(
            self._run_stream(session),
            name=f"stream-{session_id}",
        )
        self._active_tasks[session_id] = task

        # Add cleanup callback
        task.add_done_callback(
            lambda t: asyncio.create_task(self._cleanup_task(session_id))
        )

        logger.info(
            f"Started streaming session {session_id} for conversation {conversation_id}"
        )

        return session

    async def _run_stream(self, session: StreamSession) -> None:
        """
        Run the actual streaming generation.

        Args:
            session: The streaming session to run.
        """
        session.status = StreamStatus.STREAMING
        session.started_at = datetime.utcnow()

        # Notify clients that streaming is starting
        await self._send_websocket_event(
            session.conversation_id,
            {
                "type": "stream_start",
                "session_id": session.session_id,
                "timestamp": session.started_at.isoformat(),
                "metadata": {
                    "provider": session.provider_type,
                },
            },
        )

        try:
            provider = create_provider_from_env(session.provider_type)

            async for event in stream_text(
                prompt=session.prompt,
                provider=provider,
                options=session.options,
            ):
                # Check for cancellation
                if session.is_cancelled():
                    session.status = StreamStatus.CANCELLED
                    await self._send_websocket_event(
                        session.conversation_id,
                        {
                            "type": "stream_cancelled",
                            "session_id": session.session_id,
                            "content": session.accumulated_content,
                            "token_count": session.token_count,
                        },
                    )
                    return

                if event.type == StreamEventType.TOKEN:
                    session.accumulated_content += event.content
                    session.token_count += 1

                    # Send token to WebSocket clients
                    await self._send_websocket_event(
                        session.conversation_id,
                        {
                            "type": "stream_token",
                            "session_id": session.session_id,
                            "content": event.content,
                            "token_index": session.token_count,
                        },
                    )

                    # Trigger callbacks
                    for callback in self._on_token_callbacks:
                        try:
                            callback(session.session_id, session, event.content)
                        except Exception as e:
                            logger.warning(f"Token callback error: {e}")

                elif event.type == StreamEventType.END:
                    session.status = StreamStatus.COMPLETED
                    session.completed_at = datetime.utcnow()

                    if event.metadata:
                        session.metadata.update(event.metadata)

                    await self._send_websocket_event(
                        session.conversation_id,
                        {
                            "type": "stream_complete",
                            "session_id": session.session_id,
                            "content": session.accumulated_content,
                            "token_count": session.token_count,
                            "metadata": session.metadata,
                            "duration_ms": int(
                                (session.completed_at - session.started_at).total_seconds()
                                * 1000
                            )
                            if session.started_at
                            else None,
                        },
                    )

                    # Trigger callbacks
                    for callback in self._on_complete_callbacks:
                        try:
                            callback(session.session_id, session)
                        except Exception as e:
                            logger.warning(f"Complete callback error: {e}")

                elif event.type == StreamEventType.ERROR:
                    session.status = StreamStatus.ERROR
                    session.error = event.error
                    session.completed_at = datetime.utcnow()

                    await self._send_websocket_event(
                        session.conversation_id,
                        {
                            "type": "stream_error",
                            "session_id": session.session_id,
                            "error": event.error,
                            "partial_content": session.accumulated_content,
                        },
                    )

                    # Trigger callbacks
                    for callback in self._on_error_callbacks:
                        try:
                            callback(session.session_id, session, event.error or "")
                        except Exception as e:
                            logger.warning(f"Error callback error: {e}")

        except asyncio.CancelledError:
            session.status = StreamStatus.CANCELLED
            logger.info(f"Stream {session.session_id} was cancelled")
            raise
        except StreamingError as e:
            session.status = StreamStatus.ERROR
            session.error = str(e)
            session.completed_at = datetime.utcnow()

            await self._send_websocket_event(
                session.conversation_id,
                {
                    "type": "stream_error",
                    "session_id": session.session_id,
                    "error": str(e),
                    "partial_content": e.partial_content,
                    "is_recoverable": e.is_recoverable,
                },
            )
        except Exception as e:
            session.status = StreamStatus.ERROR
            session.error = str(e)
            session.completed_at = datetime.utcnow()
            logger.error(f"Unexpected error in stream {session.session_id}: {e}")

            await self._send_websocket_event(
                session.conversation_id,
                {
                    "type": "stream_error",
                    "session_id": session.session_id,
                    "error": "An unexpected error occurred",
                    "partial_content": session.accumulated_content,
                },
            )

    async def _send_websocket_event(
        self,
        conversation_id: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Send an event to all WebSocket clients in a conversation.

        Args:
            conversation_id: The conversation to send to.
            message: The message to send.
        """
        try:
            await manager.send_message(message, conversation_id)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    async def _cleanup_task(self, session_id: str) -> None:
        """
        Clean up resources after a streaming task completes.

        Args:
            session_id: The session ID to clean up.
        """
        async with self._session_lock:
            if session_id in self._active_tasks:
                del self._active_tasks[session_id]

    async def cancel_stream(self, session_id: str) -> bool:
        """
        Cancel an active streaming session.

        Args:
            session_id: The session to cancel.

        Returns:
            True if the session was cancelled, False if not found or already complete.
        """
        async with self._session_lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            if session.status not in (StreamStatus.PENDING, StreamStatus.STREAMING):
                return False

            session.cancel()

            # Also cancel the asyncio task
            task = self._active_tasks.get(session_id)
            if task and not task.done():
                task.cancel()

            return True

    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """
        Get a streaming session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def get_sessions_for_conversation(
        self,
        conversation_id: str,
    ) -> List[StreamSession]:
        """
        Get all streaming sessions for a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            List of sessions for the conversation.
        """
        return [
            session
            for session in self._sessions.values()
            if session.conversation_id == conversation_id
        ]

    def get_active_sessions(self) -> List[StreamSession]:
        """
        Get all active (streaming) sessions.

        Returns:
            List of currently streaming sessions.
        """
        return [
            session
            for session in self._sessions.values()
            if session.status == StreamStatus.STREAMING
        ]

    async def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Remove old completed/cancelled sessions from memory.

        Args:
            max_age_seconds: Maximum age of sessions to keep.

        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.utcnow()
        to_remove: List[str] = []

        async with self._session_lock:
            for session_id, session in self._sessions.items():
                if session.status in (
                    StreamStatus.COMPLETED,
                    StreamStatus.CANCELLED,
                    StreamStatus.ERROR,
                ):
                    age = (now - session.created_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(session_id)

            for session_id in to_remove:
                del self._sessions[session_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old streaming sessions")

        return len(to_remove)

    def on_token(
        self,
        callback: Callable[[str, StreamSession, str], None],
    ) -> None:
        """
        Register a callback to be called for each token.

        Args:
            callback: Function taking (session_id, session, token).
        """
        self._on_token_callbacks.append(callback)

    def on_complete(
        self,
        callback: Callable[[str, StreamSession], None],
    ) -> None:
        """
        Register a callback to be called when streaming completes.

        Args:
            callback: Function taking (session_id, session).
        """
        self._on_complete_callbacks.append(callback)

    def on_error(
        self,
        callback: Callable[[str, StreamSession, str], None],
    ) -> None:
        """
        Register a callback to be called on errors.

        Args:
            callback: Function taking (session_id, session, error_message).
        """
        self._on_error_callbacks.append(callback)


# Global streaming service instance
_streaming_service: Optional[StreamingService] = None


def get_streaming_service() -> StreamingService:
    """
    Get the global streaming service instance.

    Returns:
        The global StreamingService instance.
    """
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service
