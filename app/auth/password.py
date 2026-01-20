"""
Password hashing utilities using bcrypt.
"""

import hashlib
import hmac
import os
import secrets
from typing import Tuple


# Use PBKDF2 for password hashing (no external dependencies)
# In production, consider using bcrypt or argon2
HASH_ITERATIONS = 100000
SALT_LENGTH = 32


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256.

    Args:
        password: The plain-text password to hash.

    Returns:
        A string containing the salt and hash, separated by ':'.
    """
    salt = secrets.token_hex(SALT_LENGTH)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS,
    )
    return f"{salt}:{pw_hash.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: The plain-text password to verify.
        hashed: The stored hash string (salt:hash format).

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        salt, stored_hash = hashed.split(":")
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            HASH_ITERATIONS,
        )
        return hmac.compare_digest(pw_hash.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False


def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key and its hash.

    Returns:
        A tuple of (plain_key, hashed_key).
    """
    plain_key = secrets.token_urlsafe(32)
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, hashed_key
