"""
Streaming API endpoints for real-time text generation.

Provides endpoints to start, monitor, and cancel streaming text generation
sessions that deliver tokens via WebSocket.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from src.text_generation import GenerationOptions, StreamEventType, stream_text
from src.text_generation.core import create_provider_from_env

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota
from ..models import (
    StreamCancelRequest,
    StreamCancelResponse,
    StreamingGenerationRequest,
    StreamSessionResponse,
    StreamStartResponse,
    StreamStatsResponse,
)
from ..services import get_streaming_service
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


@router.post(
    "/generate",
    response_model=StreamStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start streaming text generation",
    description="""
Start a streaming text generation session.

Tokens will be delivered via WebSocket to the specified conversation.
Connect to the WebSocket endpoint before calling this to receive tokens.

**WebSocket Events:**
- `stream_start`: Streaming has begun
- `stream_token`: A new token is available
- `stream_complete`: Streaming finished successfully
- `stream_error`: An error occurred
- `stream_cancelled`: Stream was cancelled

**Quota Usage**: Each streaming generation counts toward your monthly limit.
    """,
    responses={
        202: {"description": "Streaming started successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Missing or invalid API key"},
        429: {"description": "Rate limit or quota exceeded"},
    },
)
async def start_streaming_generation(
    request: StreamingGenerationRequest,
    user_id: str = Depends(require_quota),
):
    """
    Start a streaming text generation session.

    Args:
        request: The streaming generation request parameters.
        user_id: The authenticated user ID.

    Returns:
        Information about the started streaming session.
    """
    logger.info(
        f"Streaming generation requested by user: {user_id}, "
        f"conversation: {request.conversation_id}"
    )

    try:
        streaming_service = get_streaming_service()

        # Create generation options
        options = GenerationOptions(
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
        )

        # Start the streaming session
        session = await streaming_service.start_stream(
            conversation_id=request.conversation_id,
            user_id=user_id,
            prompt=request.prompt,
            provider_type=request.provider,
            options=options,
            session_id=request.session_id,
            metadata=request.metadata,
        )

        # Track usage asynchronously (estimated tokens)
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type="streaming",
            tokens_used=request.max_tokens,
            metadata={"session_id": session.session_id, "provider": request.provider},
        )

        return StreamStartResponse(
            success=True,
            session_id=session.session_id,
            conversation_id=session.conversation_id,
            message="Streaming started. Connect to WebSocket to receive tokens.",
        )

    except ValueError as e:
        logger.warning(f"Validation error in streaming request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Error starting stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start streaming. Please try again.",
        )


@router.post(
    "/cancel",
    response_model=StreamCancelResponse,
    summary="Cancel a streaming session",
    description="Cancel an active streaming text generation session.",
    responses={
        200: {"description": "Stream cancelled successfully"},
        404: {"description": "Stream session not found"},
        409: {"description": "Stream already completed or cancelled"},
    },
)
async def cancel_streaming_session(
    request: StreamCancelRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Cancel an active streaming session.

    Args:
        request: The cancellation request with session ID.
        user_id: The authenticated user ID.

    Returns:
        Confirmation of cancellation.
    """
    streaming_service = get_streaming_service()

    # Verify the session exists and belongs to the user
    session = streaming_service.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream session not found",
        )

    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this stream",
        )

    # Attempt to cancel
    cancelled = await streaming_service.cancel_stream(request.session_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stream already completed or cancelled",
        )

    logger.info(f"Stream {request.session_id} cancelled by user {user_id}")

    return StreamCancelResponse(
        success=True,
        session_id=request.session_id,
        message="Stream cancelled successfully",
    )


@router.get(
    "/session/{session_id}",
    response_model=StreamSessionResponse,
    summary="Get streaming session status",
    description="Get the current status and content of a streaming session.",
    responses={
        200: {"description": "Session information retrieved"},
        404: {"description": "Session not found"},
    },
)
async def get_session_status(
    session_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get the status of a streaming session.

    Args:
        session_id: The session ID to look up.
        user_id: The authenticated user ID.

    Returns:
        Current session information.
    """
    streaming_service = get_streaming_service()

    session = streaming_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream session not found",
        )

    # Verify ownership
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this stream",
        )

    return StreamSessionResponse(
        session_id=session.session_id,
        conversation_id=session.conversation_id,
        status=session.status.value,
        token_count=session.token_count,
        accumulated_content=session.accumulated_content,
        created_at=session.created_at.isoformat(),
        started_at=session.started_at.isoformat() if session.started_at else None,
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        error=session.error,
        metadata=session.metadata,
    )


@router.get(
    "/active",
    response_model=StreamStatsResponse,
    summary="Get active streaming sessions",
    description="Get all active streaming sessions for the current user.",
    responses={
        200: {"description": "Active sessions retrieved"},
    },
)
async def get_active_sessions(
    user_id: str = Depends(verify_api_key),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
):
    """
    Get all active streaming sessions.

    Args:
        user_id: The authenticated user ID.
        conversation_id: Optional conversation ID to filter by.

    Returns:
        List of active streaming sessions.
    """
    streaming_service = get_streaming_service()

    if conversation_id:
        sessions = streaming_service.get_sessions_for_conversation(conversation_id)
    else:
        sessions = streaming_service.get_active_sessions()

    # Filter to user's sessions only
    user_sessions = [s for s in sessions if s.user_id == user_id]

    return StreamStatsResponse(
        active_sessions=len(user_sessions),
        total_connections=manager.get_total_connections(),
        sessions=[
            StreamSessionResponse(
                session_id=s.session_id,
                conversation_id=s.conversation_id,
                status=s.status.value,
                token_count=s.token_count,
                accumulated_content=s.accumulated_content[:500],  # Truncate for list
                created_at=s.created_at.isoformat(),
                started_at=s.started_at.isoformat() if s.started_at else None,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                error=s.error,
                metadata=s.metadata,
            )
            for s in user_sessions
        ],
    )


@router.get(
    "/sse/{conversation_id}",
    summary="Server-Sent Events stream",
    description="""
Alternative to WebSocket: receive streaming tokens via Server-Sent Events (SSE).

This endpoint provides a fallback for clients that cannot use WebSocket.
Each event contains a JSON payload with the token data.

**Event Types:**
- `token`: New token available
- `complete`: Stream finished
- `error`: An error occurred
    """,
    responses={
        200: {
            "description": "SSE stream started",
            "content": {"text/event-stream": {}},
        },
    },
)
async def stream_via_sse(
    conversation_id: str,
    prompt: str = Query(..., description="The prompt to generate from"),
    provider: str = Query("openai", description="LLM provider"),
    max_tokens: int = Query(4000, ge=1, le=32000),
    temperature: float = Query(0.7, ge=0.0, le=2.0),
    api_key: str = Query(..., alias="api_key", description="API key for authentication"),
):
    """
    Stream text generation via Server-Sent Events.

    This is an alternative to WebSocket for environments where WebSocket
    is not available.

    Args:
        conversation_id: The conversation ID for tracking.
        prompt: The prompt to generate from.
        provider: The LLM provider to use.
        max_tokens: Maximum tokens to generate.
        temperature: Generation temperature.
        api_key: API key for authentication.

    Returns:
        Server-Sent Events stream.
    """
    # Verify API key (simplified check for SSE)
    from ..auth.api_key import api_key_store

    user_id = api_key_store.verify_key(api_key)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    async def generate_events():
        """Generate SSE events from the stream."""
        try:
            llm_provider = create_provider_from_env(provider)
            options = GenerationOptions(
                temperature=temperature,
                max_tokens=max_tokens,
            )

            async for event in stream_text(prompt, llm_provider, options):
                if event.type == StreamEventType.TOKEN:
                    yield f"event: token\ndata: {event.content}\n\n"
                elif event.type == StreamEventType.END:
                    yield f"event: complete\ndata: done\n\n"
                elif event.type == StreamEventType.ERROR:
                    yield f"event: error\ndata: {event.error}\n\n"

        except Exception as e:
            logger.error(f"SSE streaming error: {e}", exc_info=True)
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
