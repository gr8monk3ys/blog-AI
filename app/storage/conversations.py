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
        logger.info(f"Conversation storage initialized at: {self.storage_dir}")

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

    def append(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Append a message to a conversation and persist to disk.

        Args:
            conversation_id: The conversation identifier.
            message: The message to append.
        """
        if conversation_id not in self._cache:
            self.get(conversation_id)  # Load from disk if exists

        self._cache[conversation_id].append(message)
        self._save(conversation_id)

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
