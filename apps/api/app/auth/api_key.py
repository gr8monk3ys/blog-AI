"""
API Key authentication and storage.

Security Notes:
- API keys are hashed using bcrypt with automatic salting
- Legacy SHA-256 hashes are detected but are no longer accepted for auth
- Bcrypt verification uses constant-time comparison internally
"""

import json
import logging
import os
import secrets
from pathlib import Path
from typing import Annotated, Dict, Optional

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Bcrypt hash prefix for identifying hash type
BCRYPT_PREFIX = "$2"
# SHA-256 hashes are 64 hex characters
SHA256_HASH_LENGTH = 64

# API Key header configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyStore:
    """
    File-based API key storage with secure hashing.

    API keys are stored as bcrypt hashes with automatic salting for security.
    The plain-text key is only returned once when created and cannot be
    retrieved later. This is a stepping stone to Redis/database storage
    in production.

    Security features:
    - Bcrypt hashing with automatic salt generation (cost factor 12)
    - Legacy SHA-256 hash detection so insecure keys can be rotated
    - Constant-time verification via bcrypt.checkpw
    """

    # Bcrypt cost factor (work factor) - 12 is a good balance of security and performance
    BCRYPT_ROUNDS = 12

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
        self._legacy_hash_users: set = set()  # Track users with legacy hashes
        self._load()
        logger.info(f"API key storage initialized at: {self.storage_path}")

    def _hash_key(self, api_key: str) -> str:
        """
        Hash an API key using bcrypt with automatic salt generation.

        Args:
            api_key: The plain-text API key to hash.

        Returns:
            The bcrypt hash as a string (includes salt automatically).
        """
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        return bcrypt.hashpw(api_key.encode("utf-8"), salt).decode("utf-8")

    def _is_legacy_hash(self, stored_hash: str) -> bool:
        """
        Determine if a stored hash is a legacy SHA-256 hash.

        Bcrypt hashes start with "$2a$", "$2b$", or "$2y$" prefix.
        SHA-256 hashes are 64-character hex strings.

        Args:
            stored_hash: The hash to check.

        Returns:
            True if this is a legacy SHA-256 hash, False if bcrypt.
        """
        # Bcrypt hashes always start with $2
        if stored_hash.startswith(BCRYPT_PREFIX):
            return False
        # SHA-256 produces 64 hex characters
        if len(stored_hash) == SHA256_HASH_LENGTH:
            try:
                int(stored_hash, 16)  # Verify it's valid hex
                return True
            except ValueError:
                pass
        return False

    def _verify_bcrypt(self, api_key: str, stored_hash: str) -> bool:
        """
        Verify an API key against a bcrypt hash using constant-time comparison.

        Args:
            api_key: The plain-text API key to verify.
            stored_hash: The bcrypt hash to verify against.

        Returns:
            True if the key matches, False otherwise.
        """
        try:
            return bcrypt.checkpw(api_key.encode("utf-8"), stored_hash.encode("utf-8"))
        except (ValueError, TypeError) as e:
            logger.warning(f"Bcrypt verification error: {e}")
            return False

    def _load(self) -> None:
        """Load API keys from disk and identify legacy hashes."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self._cache = json.load(f)

                # Identify users with legacy SHA-256 hashes
                legacy_count = 0
                for user_id, stored_hash in self._cache.items():
                    if self._is_legacy_hash(stored_hash):
                        self._legacy_hash_users.add(user_id)
                        legacy_count += 1

                logger.info(f"Loaded {len(self._cache)} API keys from storage")
                if legacy_count > 0:
                    logger.warning(
                        f"Found {legacy_count} API key(s) using legacy SHA-256 hashing. "
                        "These keys are disabled until they are rotated to bcrypt."
                    )
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

        Only bcrypt hashes are accepted. Legacy SHA-256 hashes are
        intentionally rejected and require key rotation.

        Args:
            api_key: The API key to verify.

        Returns:
            The user_id if valid, None otherwise.
        """
        for user_id, stored_hash in self._cache.items():
            if self._is_legacy_hash(stored_hash):
                continue

            # Bcrypt hash - bcrypt.checkpw uses constant-time comparison
            if self._verify_bcrypt(api_key, stored_hash):
                return user_id
        return None

    def upgrade_legacy_hash(self, user_id: str, api_key: str) -> bool:
        """
        Legacy SHA-256 hashes are no longer upgraded in-place.

        Args:
            user_id: The user identifier.
            api_key: Unused. Retained for API compatibility.

        Returns:
            Always False. Legacy keys must be rotated out-of-band.
        """
        _ = api_key
        if user_id in self._legacy_hash_users:
            logger.warning(
                "Legacy API key hashes must be rotated by revoking and recreating the key."
            )
        return False

    def has_legacy_hash(self, user_id: str) -> bool:
        """
        Check if a user's API key uses legacy SHA-256 hashing.

        Args:
            user_id: The user identifier.

        Returns:
            True if the user has a legacy hash, False otherwise.
        """
        return user_id in self._legacy_hash_users

    def get_legacy_hash_users(self) -> list:
        """
        Get a list of users with legacy SHA-256 hashes.

        Returns:
            List of user IDs with legacy hashes.
        """
        return list(self._legacy_hash_users)

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


def _is_production() -> bool:
    """
    Check if the application is running in a production environment.

    Returns:
        True if production indicators are detected, False otherwise.
    """
    if os.environ.get("SENTRY_ENVIRONMENT", "").lower() == "production":
        return True
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        return True
    return False


# Track if dev API key warning has been logged
_dev_api_key_warning_logged = False


async def verify_api_key(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    api_key: Optional[str] = Depends(API_KEY_HEADER),
) -> str:
    """
    Verify API key and return user_id.

    Supports Clerk JWT tokens (via Authorization header), development API keys
    (via DEV_API_KEY env var, non-production only), and regular API keys
    (via X-API-Key header).

    Args:
        authorization: Optional Authorization header (Bearer JWT from Clerk).
        api_key: The API key from the X-API-Key header.

    Returns:
        The user_id associated with the API key.

    Raises:
        HTTPException: If API key is missing or invalid.
    """
    global _dev_api_key_warning_logged

    # 1) Prefer Clerk JWTs (cloud SaaS).
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token"
            )

        try:
            from .clerk_jwt import is_clerk_jwt_configured, verify_clerk_session_token

            if not is_clerk_jwt_configured():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Bearer auth is not configured",
                )

            claims = verify_clerk_session_token(token)
            user_id = claims.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token (missing sub claim)",
                )
            return str(user_id)
        except HTTPException:
            raise
        except Exception as e:
            # Avoid leaking details; log for operators.
            logger.warning("JWT auth failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
            )

    # 2) Development API key - requires a key but uses a simple static value
    # SECURITY: Only works when DEV_API_KEY env var is set AND not in production
    dev_api_key_value = os.environ.get("DEV_API_KEY", "")
    if dev_api_key_value and api_key:
        if _is_production():
            logger.error(
                "DEV_API_KEY is set but BLOCKED because the application is running "
                "in production (SENTRY_ENVIRONMENT=production or ENVIRONMENT=production). "
                "Remove DEV_API_KEY from your environment."
            )
            # Fall through to require real authentication
        elif api_key == dev_api_key_value:
            if not _dev_api_key_warning_logged:
                logger.warning(
                    "DEV_API_KEY authentication is active. "
                    "Do not use this in production."
                )
                _dev_api_key_warning_logged = True
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
