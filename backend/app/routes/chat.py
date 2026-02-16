"""Chat-based content assistant API routes.

Provides endpoints for conversational content creation, including
synchronous message handling, SSE streaming, and conversation management.

Authorization:
    All endpoints require an authenticated user (Clerk session JWT via
    ``Authorization: Bearer ...`` or API key via ``X-API-Key``).
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Set

import bleach
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from src.chat.chat_engine import (
    ChatContext,
    ChatEngine,
    ChatMessage,
    ChatResponse,
    MessageRole,
)
from src.chat.conversation_store import ConversationStore, create_conversation_store
from src.config import get_settings
from src.text_generation.core import (
    GenerationOptions,
    TextGenerationError,
    create_provider_from_env,
)
from src.text_generation.streaming import StreamEventType, stream_text

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Assistant"])

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------

ALLOWED_PROVIDERS: Set[str] = {"openai", "anthropic", "gemini"}
ALLOWED_CONTENT_TYPES: Set[str] = {
    "blog", "email", "social", "article", "newsletter",
    "landing_page", "product_description", "ad_copy", "script",
    "whitepaper", "case_study", "press_release", "other",
}
ALLOWED_HTML_TAGS: Set[str] = {
    "p", "br", "b", "i", "u", "strong", "em", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "code", "pre",
}

# Conversation ID format: alphanumeric, hyphens, underscores (max 64 chars)
CONVERSATION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# ---------------------------------------------------------------------------
# Module-level singletons (initialized lazily)
# ---------------------------------------------------------------------------

_conversation_store: Optional[ConversationStore] = None
_chat_engine: Optional[ChatEngine] = None


def _get_conversation_store() -> ConversationStore:
    global _conversation_store
    if _conversation_store is None:
        settings = get_settings()
        redis_url = settings.redis.redis_url if settings.is_redis_configured else None
        _conversation_store = create_conversation_store(redis_url)
    return _conversation_store


def _get_chat_engine() -> ChatEngine:
    global _chat_engine
    if _chat_engine is None:
        _chat_engine = ChatEngine()
    return _chat_engine


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ChatContextRequest(BaseModel):
    """Optional context to attach to the conversation."""

    brand_voice_id: Optional[str] = Field(
        default=None, max_length=64, description="Brand voice profile ID to apply"
    )
    knowledge_base_id: Optional[str] = Field(
        default=None, max_length=64, description="Knowledge base ID for factual grounding"
    )
    working_content: Optional[str] = Field(
        default=None, max_length=100000, description="Current content being worked on"
    )
    content_type: Optional[str] = Field(
        default=None, max_length=30, description="Type of content (blog, email, social, etc.)"
    )

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Invalid content_type. Must be one of: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )
        return v

    @field_validator("working_content")
    @classmethod
    def sanitize_working_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = bleach.clean(v, tags=ALLOWED_HTML_TAGS, strip=True, strip_comments=True)
        return v


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    message: str = Field(
        ..., min_length=1, max_length=10000, description="The user message"
    )
    conversation_id: str = Field(
        ..., min_length=1, max_length=64, description="Unique conversation identifier"
    )
    context: Optional[ChatContextRequest] = Field(
        default=None, description="Optional conversation context"
    )
    provider: Optional[str] = Field(
        default=None, max_length=20, description="LLM provider (openai, anthropic, gemini)"
    )

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return bleach.clean(v, tags=set(), strip=True, strip_comments=True)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        v = v.strip()
        if not CONVERSATION_ID_PATTERN.match(v):
            raise ValueError(
                "conversation_id must be 1-64 characters, alphanumeric with hyphens and underscores"
            )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_PROVIDERS:
            raise ValueError(f"Invalid provider. Must be one of: {', '.join(sorted(ALLOWED_PROVIDERS))}")
        return v


class ChatMessageResponse(BaseModel):
    """Response body for a chat message."""

    success: bool = True
    message: str
    updated_content: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    conversation_id: str
    message_count: int
    preview: str
    content_type: Optional[str] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


class ConversationHistoryResponse(BaseModel):
    """Response body for conversation history."""

    success: bool = True
    conversation_id: str
    messages: List[Dict[str, Any]]
    working_content: Optional[str] = None
    content_type: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response body for listing conversations."""

    success: bool = True
    conversations: List[ConversationSummary]


# ---------------------------------------------------------------------------
# Helper: resolve brand voice summary
# ---------------------------------------------------------------------------


async def _resolve_brand_voice(brand_voice_id: Optional[str], user_id: str) -> Optional[str]:
    """Attempt to load a brand voice summary for prompt injection."""
    if not brand_voice_id:
        return None
    try:
        from src.brand.storage import get_brand_voice_storage

        storage = get_brand_voice_storage()
        fingerprint = await storage.get_fingerprint(user_id, brand_voice_id)
        if fingerprint and fingerprint.voice_summary:
            return fingerprint.voice_summary
    except Exception as exc:
        logger.warning("Failed to load brand voice %s: %s", brand_voice_id, exc)
    return None


# ---------------------------------------------------------------------------
# Helper: resolve knowledge context
# ---------------------------------------------------------------------------


async def _resolve_knowledge_context(
    knowledge_base_id: Optional[str],
    query: str,
    user_id: str,
) -> Optional[str]:
    """Attempt to retrieve relevant knowledge base context."""
    if not knowledge_base_id:
        return None
    try:
        import os

        if os.environ.get("ENABLE_KNOWLEDGE_BASE", "false").lower() != "true":
            return None
        from src.knowledge.knowledge_service import KnowledgeService

        service = KnowledgeService.from_env()
        await service.initialize()
        result = await service.search(query=query, user_id=user_id, top_k=3)
        if result and result.results:
            chunks = [r.content for r in result.results[:3]]
            return "\n\n---\n\n".join(chunks)
    except Exception as exc:
        logger.warning("Failed to load knowledge context: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Send a chat message",
    description=(
        "Send a message to the content assistant and receive a response. "
        "Supports content generation, editing, scoring, and more."
    ),
    responses={
        200: {"description": "Chat response"},
        400: {"description": "Invalid request"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit or quota exceeded"},
    },
)
async def send_message(
    request: ChatMessageRequest,
    user_id: str = Depends(require_quota),
) -> ChatMessageResponse:
    """Process a chat message and return the assistant's response."""
    store = _get_conversation_store()
    engine = _get_chat_engine()

    # Load or create conversation context
    context = await store.get_context(request.conversation_id)
    if context is None:
        context = ChatContext()

    # Merge request context overrides
    if request.context:
        if request.context.brand_voice_id is not None:
            context.brand_voice_id = request.context.brand_voice_id
        if request.context.knowledge_base_id is not None:
            context.knowledge_base_id = request.context.knowledge_base_id
        if request.context.working_content is not None:
            context.working_content = request.context.working_content
        if request.context.content_type is not None:
            context.content_type = request.context.content_type

    # Resolve brand voice and knowledge context
    brand_voice_summary = await _resolve_brand_voice(context.brand_voice_id, user_id)
    knowledge_context = await _resolve_knowledge_context(
        context.knowledge_base_id, request.message, user_id,
    )

    # Process the message
    try:
        response: ChatResponse = await engine.process_message(
            user_message=request.message,
            context=context,
            provider_type=request.provider,
            brand_voice_summary=brand_voice_summary,
            knowledge_context=knowledge_context,
        )
    except TextGenerationError as exc:
        logger.error("Chat generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Content generation service temporarily unavailable. Please try again.",
        )

    # Persist updated context
    await store.save_context(request.conversation_id, context)

    # Track usage
    await increment_usage_for_operation(
        user_id=user_id,
        operation_type="chat",
        tokens_used=len(response.message) // 4,  # rough estimate
        metadata={
            "conversation_id": request.conversation_id,
            "intent": response.metadata.get("intent", "unknown"),
        },
    )

    return ChatMessageResponse(
        success=True,
        message=response.message,
        updated_content=response.updated_content,
        suggestions=response.suggestions,
        metadata=response.metadata,
        conversation_id=request.conversation_id,
    )


@router.post(
    "/message/stream",
    summary="Send a chat message with streaming response",
    description=(
        "Send a message and receive the response as a Server-Sent Events stream. "
        "Each event contains a token or metadata update."
    ),
    responses={
        200: {
            "description": "SSE stream started",
            "content": {"text/event-stream": {}},
        },
        400: {"description": "Invalid request"},
        401: {"description": "Authentication required"},
    },
)
async def send_message_stream(
    request: ChatMessageRequest,
    user_id: str = Depends(require_quota),
) -> StreamingResponse:
    """Process a chat message and stream the response via SSE."""
    store = _get_conversation_store()
    engine = _get_chat_engine()

    # Load or create context
    context = await store.get_context(request.conversation_id)
    if context is None:
        context = ChatContext()

    if request.context:
        if request.context.brand_voice_id is not None:
            context.brand_voice_id = request.context.brand_voice_id
        if request.context.knowledge_base_id is not None:
            context.knowledge_base_id = request.context.knowledge_base_id
        if request.context.working_content is not None:
            context.working_content = request.context.working_content
        if request.context.content_type is not None:
            context.content_type = request.context.content_type

    brand_voice_summary = await _resolve_brand_voice(context.brand_voice_id, user_id)
    knowledge_context = await _resolve_knowledge_context(
        context.knowledge_base_id, request.message, user_id,
    )

    # Record the user message in context
    context.add_message(MessageRole.USER, request.message)

    # Build the prompt for streaming
    system_prompt = engine.build_system_prompt(context, brand_voice_summary, knowledge_context)
    prompt = engine._build_conversation_prompt(system_prompt, context)

    provider_type = request.provider or engine._provider_type
    provider = create_provider_from_env(provider_type)
    options = GenerationOptions(temperature=0.7, max_tokens=4000, top_p=0.95)

    async def generate_sse_events():
        accumulated = ""
        try:
            intent = engine.detect_intent(request.message)
            yield f"event: metadata\ndata: {json.dumps({'intent': intent.value})}\n\n"

            async for event in stream_text(prompt, provider, options):
                if event.type == StreamEventType.TOKEN:
                    accumulated += event.content
                    yield f"event: token\ndata: {json.dumps({'content': event.content})}\n\n"
                elif event.type == StreamEventType.END:
                    # Record the full assistant response
                    context.add_message(
                        MessageRole.ASSISTANT,
                        accumulated,
                        metadata={"intent": intent.value, "streamed": True},
                    )
                    # Update working content for generation/edit intents
                    if intent.value in ("generate", "edit", "refine", "shorten", "expand", "change_tone", "translate"):
                        context.working_content = accumulated

                    await store.save_context(request.conversation_id, context)

                    suggestions = engine._generate_suggestions(
                        "generate" if intent.value == "generate" else "edit"
                    )
                    yield f"event: complete\ndata: {json.dumps({'suggestions': suggestions})}\n\n"
                elif event.type == StreamEventType.ERROR:
                    yield f"event: error\ndata: {json.dumps({'error': sanitize_error_message(event.error or 'Unknown error')})}\n\n"

        except TextGenerationError as exc:
            logger.error("Streaming chat error: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': 'Generation failed. Please try again.'})}\n\n"
        except Exception as exc:
            logger.error("Unexpected streaming error: %s", exc, exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': 'An unexpected error occurred.'})}\n\n"

    return StreamingResponse(
        generate_sse_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history",
    description="Retrieve the full message history for a conversation.",
    responses={
        200: {"description": "Conversation history"},
        404: {"description": "Conversation not found"},
    },
)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(verify_api_key),
) -> ConversationHistoryResponse:
    """Return the full conversation history."""
    if not CONVERSATION_ID_PATTERN.match(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    store = _get_conversation_store()
    context = await store.get_context(conversation_id)

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = [
        {
            "role": msg.role.value,
            "content": msg.content,
            "metadata": msg.metadata,
        }
        for msg in context.messages
    ]

    return ConversationHistoryResponse(
        success=True,
        conversation_id=conversation_id,
        messages=messages,
        working_content=context.working_content,
        content_type=context.content_type,
    )


@router.delete(
    "/conversations/{conversation_id}",
    summary="Clear a conversation",
    description="Delete all messages and context for a conversation.",
    responses={
        200: {"description": "Conversation cleared"},
        404: {"description": "Conversation not found"},
    },
)
async def clear_conversation(
    conversation_id: str,
    user_id: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Delete a conversation and all its data."""
    if not CONVERSATION_ID_PATTERN.match(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    store = _get_conversation_store()
    deleted = await store.clear_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return {"success": True, "message": "Conversation cleared"}


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="List all conversations for the authenticated user.",
    responses={
        200: {"description": "Conversation list"},
    },
)
async def list_conversations(
    user_id: str = Depends(verify_api_key),
) -> ConversationListResponse:
    """Return a summary list of the user's conversations."""
    store = _get_conversation_store()
    raw = await store.list_conversations(user_id)

    conversations = [
        ConversationSummary(
            conversation_id=c["conversation_id"],
            message_count=c["message_count"],
            preview=c.get("preview", ""),
            content_type=c.get("content_type"),
            created_at=c.get("created_at"),
            updated_at=c.get("updated_at"),
        )
        for c in raw
    ]

    return ConversationListResponse(success=True, conversations=conversations)
