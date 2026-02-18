"""In-memory and Redis-backed conversation storage for the chat assistant.

Provides a simple abstraction for persisting chat messages per conversation
with automatic TTL-based cleanup.  Falls back to an in-memory dictionary
when Redis is not available.
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .chat_engine import ChatContext, ChatMessage, MessageRole

logger = logging.getLogger(__name__)

# Default conversation TTL: 24 hours
DEFAULT_CONVERSATION_TTL = 86400

# Maximum conversations to keep in-memory per the LRU eviction policy
MAX_IN_MEMORY_CONVERSATIONS = 500


class ConversationStore(ABC):
    """Abstract interface for conversation persistence."""

    @abstractmethod
    async def save_message(
        self,
        conversation_id: str,
        message: ChatMessage,
        user_id: Optional[str] = None,
    ) -> None:
        """Persist a single message to a conversation."""

    @abstractmethod
    async def get_messages(self, conversation_id: str) -> List[ChatMessage]:
        """Return all messages for a conversation in chronological order."""

    @abstractmethod
    async def get_context(self, conversation_id: str) -> Optional[ChatContext]:
        """Return the full ChatContext for a conversation, or None."""

    @abstractmethod
    async def save_context(self, conversation_id: str, context: ChatContext) -> None:
        """Persist the full ChatContext (including working_content, etc.)."""

    @abstractmethod
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Delete all data for a conversation. Returns True if it existed."""

    @abstractmethod
    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Return summary metadata for all conversations belonging to a user."""


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _message_to_dict(msg: ChatMessage) -> Dict[str, Any]:
    return {
        "role": msg.role.value,
        "content": msg.content,
        "metadata": msg.metadata,
    }


def _message_from_dict(data: Dict[str, Any]) -> ChatMessage:
    return ChatMessage(
        role=MessageRole(data["role"]),
        content=data["content"],
        metadata=data.get("metadata"),
    )


def _context_to_dict(ctx: ChatContext) -> Dict[str, Any]:
    return {
        "messages": [_message_to_dict(m) for m in ctx.messages],
        "brand_voice_id": ctx.brand_voice_id,
        "knowledge_base_id": ctx.knowledge_base_id,
        "working_content": ctx.working_content,
        "content_type": ctx.content_type,
    }


def _context_from_dict(data: Dict[str, Any]) -> ChatContext:
    return ChatContext(
        messages=[_message_from_dict(m) for m in data.get("messages", [])],
        brand_voice_id=data.get("brand_voice_id"),
        knowledge_base_id=data.get("knowledge_base_id"),
        working_content=data.get("working_content"),
        content_type=data.get("content_type"),
    )


# ---------------------------------------------------------------------------
# In-memory implementation (with LRU eviction and TTL)
# ---------------------------------------------------------------------------


class _ConversationEntry:
    """Container for a single conversation's data in memory."""

    __slots__ = ("context", "user_id", "created_at", "updated_at")

    def __init__(self, context: ChatContext, user_id: Optional[str] = None):
        self.context = context
        self.user_id = user_id
        self.created_at = time.time()
        self.updated_at = time.time()


class InMemoryConversationStore(ConversationStore):
    """Thread-safe, LRU-evicting, TTL-aware in-memory conversation store."""

    def __init__(
        self,
        max_conversations: int = MAX_IN_MEMORY_CONVERSATIONS,
        ttl_seconds: int = DEFAULT_CONVERSATION_TTL,
    ):
        self._store: OrderedDict[str, _ConversationEntry] = OrderedDict()
        self._max = max_conversations
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    # -- private helpers ---------------------------------------------------

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            cid for cid, entry in self._store.items()
            if now - entry.updated_at > self._ttl
        ]
        for cid in expired:
            del self._store[cid]

    def _touch(self, conversation_id: str) -> None:
        """Move conversation to end of LRU order and refresh timestamp."""
        if conversation_id in self._store:
            self._store.move_to_end(conversation_id)
            self._store[conversation_id].updated_at = time.time()

    def _ensure_capacity(self) -> None:
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    # -- public API --------------------------------------------------------

    async def save_message(
        self,
        conversation_id: str,
        message: ChatMessage,
        user_id: Optional[str] = None,
    ) -> None:
        with self._lock:
            self._evict_expired()
            entry = self._store.get(conversation_id)
            if entry is None:
                entry = _ConversationEntry(ChatContext(), user_id=user_id)
                self._store[conversation_id] = entry
            entry.context.messages.append(message)
            if user_id and not entry.user_id:
                entry.user_id = user_id
            self._touch(conversation_id)
            self._ensure_capacity()

    async def get_messages(self, conversation_id: str) -> List[ChatMessage]:
        with self._lock:
            entry = self._store.get(conversation_id)
            if entry is None:
                return []
            self._touch(conversation_id)
            return list(entry.context.messages)

    async def get_context(self, conversation_id: str) -> Optional[ChatContext]:
        with self._lock:
            entry = self._store.get(conversation_id)
            if entry is None:
                return None
            self._touch(conversation_id)
            return entry.context

    async def save_context(self, conversation_id: str, context: ChatContext) -> None:
        with self._lock:
            self._evict_expired()
            entry = self._store.get(conversation_id)
            if entry is None:
                entry = _ConversationEntry(context)
                self._store[conversation_id] = entry
            else:
                entry.context = context
            self._touch(conversation_id)
            self._ensure_capacity()

    async def clear_conversation(self, conversation_id: str) -> bool:
        with self._lock:
            if conversation_id in self._store:
                del self._store[conversation_id]
                return True
            return False

    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            self._evict_expired()
            results: List[Dict[str, Any]] = []
            for cid, entry in self._store.items():
                if entry.user_id == user_id:
                    first_msg = (
                        entry.context.messages[0].content[:100]
                        if entry.context.messages
                        else ""
                    )
                    results.append({
                        "conversation_id": cid,
                        "message_count": len(entry.context.messages),
                        "preview": first_msg,
                        "content_type": entry.context.content_type,
                        "created_at": entry.created_at,
                        "updated_at": entry.updated_at,
                    })
            return results


# ---------------------------------------------------------------------------
# Redis implementation
# ---------------------------------------------------------------------------


class RedisConversationStore(ConversationStore):
    """Redis-backed conversation store.

    Stores each conversation as a JSON blob under the key
    ``chat:conv:{conversation_id}`` with a configurable TTL.  A secondary
    sorted set ``chat:user:{user_id}`` maps user IDs to conversation IDs
    for listing.
    """

    KEY_PREFIX = "chat:conv:"
    USER_PREFIX = "chat:user:"

    def __init__(self, redis_url: str, ttl_seconds: int = DEFAULT_CONVERSATION_TTL):
        self._ttl = ttl_seconds
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            logger.info("Redis conversation store initialized")
        except ImportError:
            raise RuntimeError(
                "redis[asyncio] package is required for RedisConversationStore. "
                "Install with: pip install redis[asyncio]"
            )

    def _conv_key(self, conversation_id: str) -> str:
        return f"{self.KEY_PREFIX}{conversation_id}"

    def _user_key(self, user_id: str) -> str:
        return f"{self.USER_PREFIX}{user_id}"

    async def save_message(
        self,
        conversation_id: str,
        message: ChatMessage,
        user_id: Optional[str] = None,
    ) -> None:
        key = self._conv_key(conversation_id)
        raw = await self._redis.get(key)

        if raw:
            data = json.loads(raw)
            ctx = _context_from_dict(data["context"])
        else:
            ctx = ChatContext()
            data = {"user_id": user_id, "created_at": time.time()}

        ctx.messages.append(message)
        data["context"] = _context_to_dict(ctx)
        data["updated_at"] = time.time()

        await self._redis.set(key, json.dumps(data), ex=self._ttl)

        if user_id:
            await self._redis.zadd(
                self._user_key(user_id),
                {conversation_id: time.time()},
            )

    async def get_messages(self, conversation_id: str) -> List[ChatMessage]:
        raw = await self._redis.get(self._conv_key(conversation_id))
        if not raw:
            return []
        data = json.loads(raw)
        ctx = _context_from_dict(data.get("context", {}))
        return ctx.messages

    async def get_context(self, conversation_id: str) -> Optional[ChatContext]:
        raw = await self._redis.get(self._conv_key(conversation_id))
        if not raw:
            return None
        data = json.loads(raw)
        return _context_from_dict(data.get("context", {}))

    async def save_context(self, conversation_id: str, context: ChatContext) -> None:
        key = self._conv_key(conversation_id)
        raw = await self._redis.get(key)
        if raw:
            data = json.loads(raw)
        else:
            data = {"created_at": time.time()}

        data["context"] = _context_to_dict(context)
        data["updated_at"] = time.time()

        await self._redis.set(key, json.dumps(data), ex=self._ttl)

    async def clear_conversation(self, conversation_id: str) -> bool:
        key = self._conv_key(conversation_id)
        deleted = await self._redis.delete(key)
        return deleted > 0

    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        user_key = self._user_key(user_id)
        # Get conversation IDs sorted by most recent
        members = await self._redis.zrevrange(user_key, 0, 49, withscores=True)

        results: List[Dict[str, Any]] = []
        for conv_id, score in members:
            raw = await self._redis.get(self._conv_key(conv_id))
            if not raw:
                continue
            data = json.loads(raw)
            ctx_data = data.get("context", {})
            messages = ctx_data.get("messages", [])
            preview = messages[0]["content"][:100] if messages else ""
            results.append({
                "conversation_id": conv_id,
                "message_count": len(messages),
                "preview": preview,
                "content_type": ctx_data.get("content_type"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at", score),
            })

        return results


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_conversation_store(redis_url: Optional[str] = None) -> ConversationStore:
    """Create the appropriate conversation store.

    Uses Redis when ``redis_url`` is provided and the ``redis`` package is
    installed.  Falls back to the in-memory store otherwise.
    """
    if redis_url:
        try:
            return RedisConversationStore(redis_url)
        except RuntimeError:
            logger.warning("Redis package not available, falling back to in-memory store")
        except Exception as exc:
            logger.warning("Failed to initialize Redis store (%s), falling back to in-memory", exc)

    logger.info("Using in-memory conversation store")
    return InMemoryConversationStore()
