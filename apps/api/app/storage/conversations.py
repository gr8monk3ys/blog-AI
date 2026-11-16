"""
Conversation storage for persistence across restarts.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.db import fetchrow as db_fetchrow
from src.db import is_database_configured

logger = logging.getLogger(__name__)


def _validate_id(conversation_id: str) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", conversation_id):
        raise ValueError("Invalid conversation id")


class ConversationStore:
    """
    File-based conversation storage for persistence across restarts (the
    local-dev fallback for PostgresConversationStore when DATABASE_URL is not set).

    Conversations are stored as JSON files in a configurable directory.

    Ownership tracking: Each conversation has an associated owner_id that must
    match the requesting user for access to be granted.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the conversation store.

        Args:
            storage_dir: Directory for storing conversation files.
                        Defaults to CONVERSATION_STORAGE_DIR env var or ./data/conversations
        """
        self.storage_dir = Path(
            storage_dir
            or os.environ.get("CONVERSATION_STORAGE_DIR", "./data/conversations")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Dict[str, Any]]] = {}  # In-memory cache
        self._ownership: Dict[str, str] = {}  # conversation_id -> owner_user_id
        self._load_ownership()
        logger.info(f"Conversation storage initialized at: {self.storage_dir}")

    def _get_ownership_file(self) -> Path:
        """Get the path to the ownership metadata file."""
        return self.storage_dir / "_ownership.json"

    def _load_ownership(self) -> None:
        """Load ownership metadata from disk."""
        ownership_file = self._get_ownership_file()
        if ownership_file.exists():
            try:
                with open(ownership_file, "r") as f:
                    self._ownership = json.load(f)
                logger.info(f"Loaded ownership for {len(self._ownership)} conversations")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading ownership metadata: {e}")
                self._ownership = {}
        else:
            self._ownership = {}

    def _save_ownership(self) -> None:
        """Save ownership metadata to disk."""
        ownership_file = self._get_ownership_file()
        try:
            with open(ownership_file, "w") as f:
                json.dump(self._ownership, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving ownership metadata: {e}")

    def set_owner(self, conversation_id: str, user_id: str) -> None:
        """
        Set the owner of a conversation.

        Args:
            conversation_id: The conversation identifier.
            user_id: The user ID who owns this conversation.
        """
        self._ownership[conversation_id] = user_id
        self._save_ownership()

    def get_owner(self, conversation_id: str) -> Optional[str]:
        """
        Get the owner of a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            The owner's user ID, or None if no owner is set.
        """
        return self._ownership.get(conversation_id)

    async def verify_ownership(self, conversation_id: str, user_id: str) -> bool:
        """
        Verify that a user owns a conversation.

        Conversations without an ownership record are denied: allowing them
        would let any authenticated user read or append to a conversation
        whose owner record is missing (IDOR on guessable IDs). On first
        access the requesting user does not implicitly claim it either —
        ownership is only set explicitly at creation time.

        Args:
            conversation_id: The conversation identifier.
            user_id: The user ID to verify.

        Returns:
            True if the owner matches, or if the conversation does not exist
            yet (clients pick their own IDs, so a first GET/append may arrive
            before ownership is recorded and there is nothing to protect).
        """
        owner = self.get_owner(conversation_id)
        if owner is None:
            conversation_exists = (
                conversation_id in self._cache
                or self._get_file_path(conversation_id).exists()
            )
            return not conversation_exists
        return owner == user_id

    def _get_file_path(self, conversation_id: str) -> Path:
        """
        Get the file path for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            Path to the conversation JSON file.
        """
        # Sanitize conversation_id to prevent path traversal, then verify the
        # resolved path stays inside the storage directory.
        _validate_id(conversation_id)
        base = os.path.realpath(self.storage_dir)
        path = os.path.realpath(os.path.join(base, f"{conversation_id}.json"))
        if not path.startswith(base + os.sep):
            raise ValueError("Invalid conversation id")
        return Path(path)

    async def get(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get a conversation by ID, loading from disk if not cached.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            List of messages in the conversation.
        """
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        file_path = self._get_file_path(conversation_id)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    self._cache[conversation_id] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading conversation {conversation_id}: {e}")
                self._cache[conversation_id] = []
        else:
            self._cache[conversation_id] = []

        return self._cache[conversation_id]

    async def append(
        self,
        conversation_id: str,
        message: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Append a message to a conversation and persist to disk.

        If this is a new conversation and user_id is provided, sets ownership.

        Args:
            conversation_id: The conversation identifier.
            message: The message to append.
            user_id: The user ID creating/appending to the conversation.

        Raises:
            PermissionError: The conversation exists and belongs to someone else.
        """
        if not await self.verify_ownership(conversation_id, user_id):
            raise PermissionError("Not authorized for this conversation")

        is_new = conversation_id not in self._cache and not self._get_file_path(conversation_id).exists()

        if conversation_id not in self._cache:
            await self.get(conversation_id)  # Load from disk if exists

        self._cache[conversation_id].append(message)
        self._save(conversation_id)

        # Set ownership for new conversations
        if is_new and user_id:
            self.set_owner(conversation_id, user_id)

    def _save(self, conversation_id: str) -> None:
        """
        Save a conversation to disk.

        Args:
            conversation_id: The conversation identifier.
        """
        file_path = self._get_file_path(conversation_id)
        try:
            with open(file_path, "w") as f:
                json.dump(self._cache[conversation_id], f, indent=2)
        except IOError as e:
            logger.error(f"Error saving conversation {conversation_id}: {e}")

    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            True if deleted, False if conversation didn't exist.
        """
        file_path = self._get_file_path(conversation_id)
        deleted = False

        if conversation_id in self._cache:
            del self._cache[conversation_id]
            deleted = True

        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
            except IOError as e:
                logger.error(f"Error deleting conversation {conversation_id}: {e}")

        return deleted


class PostgresConversationStore:
    """
    Conversations in the Postgres `conversations` table, used when DATABASE_URL
    is set. Same interface and ownership rules as ConversationStore.
    """

    async def get(self, conversation_id: str) -> list[dict[str, Any]]:
        _validate_id(conversation_id)
        row = await db_fetchrow(
            "SELECT messages FROM conversations WHERE id = $1", conversation_id
        )
        return json.loads(row["messages"]) if row else []

    async def append(
        self,
        conversation_id: str,
        message: dict[str, Any],
        user_id: str | None = None,
    ) -> None:
        """
        Append a message; the first message creates the row and its owner.

        Raises:
            PermissionError: The conversation exists and belongs to someone else.
        """
        _validate_id(conversation_id)
        row = await db_fetchrow(
            """
            INSERT INTO conversations (id, owner_id, messages)
            VALUES ($1, $3, jsonb_build_array($2::jsonb))
            ON CONFLICT (id) DO UPDATE
            SET messages = conversations.messages || jsonb_build_array($2::jsonb),
                updated_at = NOW()
            WHERE conversations.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id
            RETURNING id
            """,
            conversation_id,
            json.dumps(message),
            user_id,
        )
        if row is None:
            raise PermissionError("Not authorized for this conversation")

    async def verify_ownership(self, conversation_id: str, user_id: str) -> bool:
        """True for the owner, or for an id that has no conversation yet."""
        _validate_id(conversation_id)
        row = await db_fetchrow(
            "SELECT owner_id FROM conversations WHERE id = $1", conversation_id
        )
        if row is None:
            return True
        return row["owner_id"] is not None and row["owner_id"] == user_id

    async def delete(self, conversation_id: str) -> bool:
        _validate_id(conversation_id)
        row = await db_fetchrow(
            "DELETE FROM conversations WHERE id = $1 RETURNING id", conversation_id
        )
        return row is not None


# Postgres when DATABASE_URL is set (Vercel's disk does not survive a cold
# start); JSON files are the local-dev fallback.
conversations = (
    PostgresConversationStore() if is_database_configured() else ConversationStore()
)
