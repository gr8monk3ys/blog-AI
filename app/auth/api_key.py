"""
API Key authentication and storage.
"""

import hashlib
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API Key header configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyStore:
    """
    File-based API key storage with secure hashing.

    API keys are stored as SHA-256 hashes for security. The plain-text key
    is only returned once when created and cannot be retrieved later.
    This is a stepping stone to Redis/database storage in production.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the API key store.

        Args:
            storage_path: Path to the JSON file for storing API keys.
                         Defaults to API_KEY_STORAGE_PATH env var or ./data/api_keys.json
        """
        self.storage_path = Path(
            storage_path
            or os.environ.get("API_KEY_STORAGE_PATH", "./data/api_keys.json")
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = {}  # user_id -> hashed_key
        self._load()
        logger.info(f"API key storage initialized at: {self.storage_path}")

    def _hash_key(self, api_key: str) -> str:
        """Hash an API key using SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _load(self) -> None:
        """Load API keys from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} API keys from storage")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading API keys: {e}")
                self._cache = {}
        else:
            self._cache = {}

    def _save(self) -> None:
        """Save API keys to disk."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving API keys: {e}")

    def create_key(self, user_id: str) -> str:
        """
        Create a new API key for a user.

        Args:
            user_id: The user identifier.

        Returns:
            The plain-text key (only returned once - cannot be retrieved later).
        """
        plain_key = secrets.token_urlsafe(32)
        hashed_key = self._hash_key(plain_key)
        self._cache[user_id] = hashed_key
        self._save()
        logger.info(f"Created new API key for user: {user_id}")
        return plain_key

    def get_or_create_key(self, user_id: str) -> Optional[str]:
        """
        Get existing key status or create a new key.

        Args:
            user_id: The user identifier.

        Returns:
            The plain-text key if newly created, None if user already has a key.
        """
        if user_id in self._cache:
            return None  # Key exists but cannot be retrieved
        return self.create_key(user_id)

    def verify_key(self, api_key: str) -> Optional[str]:
        """
        Verify an API key and return the associated user_id.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            api_key: The API key to verify.

        Returns:
            The user_id if valid, None otherwise.
        """
        hashed_input = self._hash_key(api_key)
        for user_id, stored_hash in self._cache.items():
            if secrets.compare_digest(stored_hash, hashed_input):
                return user_id
        return None

    def revoke_key(self, user_id: str) -> bool:
        """
        Revoke a user's API key.

        Args:
            user_id: The user identifier.

        Returns:
            True if key was revoked, False if user had no key.
        """
        if user_id in self._cache:
            del self._cache[user_id]
            self._save()
            logger.info(f"Revoked API key for user: {user_id}")
            return True
        return False

    def user_has_key(self, user_id: str) -> bool:
        """
        Check if a user has an API key.

        Args:
            user_id: The user identifier.

        Returns:
            True if user has a key, False otherwise.
        """
        return user_id in self._cache


# Initialize API key storage singleton
api_key_store = APIKeyStore()


def get_or_create_api_key(user_id: str) -> Optional[str]:
    """
    Generate or retrieve API key for a user.

    Args:
        user_id: The user identifier.

    Returns:
        The plain-text key if newly created, None if user already has a key.
    """
    return api_key_store.get_or_create_key(user_id)


async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> str:
    """
    Verify API key and return user_id. In dev mode, allows requests without key.

    Args:
        api_key: The API key from the request header.

    Returns:
        The user_id associated with the API key.

    Raises:
        HTTPException: If API key is missing or invalid (unless in dev mode).
    """
    # Development mode - allow requests without API key
    # SECURITY: Default is FALSE - must explicitly enable dev mode
    if os.environ.get("DEV_MODE", "false").lower() == "true":
        return "dev_user"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    # Verify API key using secure storage
    user_id = api_key_store.verify_key(api_key)
    if user_id:
        return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
    )
