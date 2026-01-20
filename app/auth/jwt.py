"""
JWT token utilities for authentication.

Uses a simple JWT implementation without external dependencies.
For production with more requirements, consider using python-jose or PyJWT.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Secret key for signing JWTs - MUST be set in production
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production-" + os.urandom(16).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRATION_DAYS", "7"))


@dataclass
class TokenPayload:
    """JWT token payload."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    type: str  # Token type: "access" or "refresh"


class JWTError(Exception):
    """Exception raised for JWT errors."""

    pass


def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    """Base64url decode with padding restoration."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _sign(message: str, secret: str) -> str:
    """Create HMAC-SHA256 signature."""
    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(signature)


def create_token(user_id: str, token_type: str = "access") -> str:
    """
    Create a JWT token.

    Args:
        user_id: The user ID to include in the token.
        token_type: Either "access" or "refresh".

    Returns:
        The encoded JWT token string.
    """
    now = int(time.time())

    if token_type == "refresh":
        exp = now + (JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60)
    else:
        exp = now + (JWT_EXPIRATION_HOURS * 60 * 60)

    # Header
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_encoded = _base64url_encode(json.dumps(header).encode("utf-8"))

    # Payload
    payload = {
        "sub": user_id,
        "exp": exp,
        "iat": now,
        "type": token_type,
    }
    payload_encoded = _base64url_encode(json.dumps(payload).encode("utf-8"))

    # Signature
    message = f"{header_encoded}.{payload_encoded}"
    signature = _sign(message, JWT_SECRET)

    return f"{message}.{signature}"


def decode_token(token: str) -> TokenPayload:
    """
    Decode and verify a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise JWTError("Invalid token format")

        header_encoded, payload_encoded, signature = parts

        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = _sign(message, JWT_SECRET)

        if not hmac.compare_digest(signature, expected_signature):
            raise JWTError("Invalid token signature")

        # Decode payload
        payload_json = _base64url_decode(payload_encoded)
        payload = json.loads(payload_json)

        # Check expiration
        if payload.get("exp", 0) < int(time.time()):
            raise JWTError("Token has expired")

        return TokenPayload(
            sub=payload["sub"],
            exp=payload["exp"],
            iat=payload["iat"],
            type=payload.get("type", "access"),
        )
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise JWTError(f"Invalid token: {e}")


def create_token_pair(user_id: str) -> Dict[str, str]:
    """
    Create an access/refresh token pair.

    Args:
        user_id: The user ID.

    Returns:
        Dictionary with "access_token" and "refresh_token".
    """
    return {
        "access_token": create_token(user_id, "access"),
        "refresh_token": create_token(user_id, "refresh"),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    }


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Create a new access token from a refresh token.

    Args:
        refresh_token: The refresh token.

    Returns:
        Dictionary with new "access_token".

    Raises:
        JWTError: If the refresh token is invalid.
    """
    payload = decode_token(refresh_token)

    if payload.type != "refresh":
        raise JWTError("Invalid token type for refresh")

    return {
        "access_token": create_token(payload.sub, "access"),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    }
