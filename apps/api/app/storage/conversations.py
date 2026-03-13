"""
Conversation storage for persistence across restarts.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    File-based conversation storage for persistence across restarts.

    Conversations are stored as JSON files in a configurable directory.
    This is a stepping stone to Redis/database storage in production.

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

    def verify_ownership(self, conversation_id: str, user_id: str) -> bool:
        """
        Verify that a user owns a conversation.

        For backwards compatibility, conversations without an owner are accessible
        to any authenticated user (legacy conversations).

        Args:
            conversation_id: The conversation identifier.
            user_id: The user ID to verify.

        Returns:
            True if the user owns the conversation or no owner is set (legacy).
        """
        owner = self.get_owner(conversation_id)
        if owner is None:
            # Legacy conversation without ownership - allow access
            # In production, consider migrating legacy data
            return True
        return owner == user_id

    def _get_file_path(self, conversation_id: str) -> Path:
        """
        Get the file path for a conversation.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            Path to the conversation JSON file.
        """
        # Sanitize conversation_id to prevent path traversal
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", conversation_id)
        return self.storage_dir / f"{safe_id}.json"

    def get(self, conversation_id: str) -> List[Dict[str, Any]]:
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

    def append(
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
        """
        is_new = conversation_id not in self._cache and not self._get_file_path(conversation_id).exists()

        if conversation_id not in self._cache:
            self.get(conversation_id)  # Load from disk if exists

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

    def delete(self, conversation_id: str) -> bool:
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

    def __contains__(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        if conversation_id in self._cache:
            return True
        return self._get_file_path(conversation_id).exists()

    def __getitem__(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get a conversation by ID (dict-like access)."""
        return self.get(conversation_id)

    def __setitem__(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set a conversation (dict-like access)."""
        self._cache[conversation_id] = messages
        self._save(conversation_id)


# Initialize conversation storage singleton
conversations = ConversationStore()
