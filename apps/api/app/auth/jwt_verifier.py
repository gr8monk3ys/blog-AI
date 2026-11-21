"""
Bearer JWT verification for user sessions.

The web app (Better Auth with its JWT plugin) mints short-lived tokens at
`GET /api/auth/token` and publishes the public keys at `GET /api/auth/jwks`.
The browser sends the token as `Authorization: Bearer <jwt>`; this module
verifies signature, expiry, issuer and audience. The user id is the `sub` claim.

Configuration (all three required for Bearer auth):
- AUTH_JWKS_URL: e.g. https://blog-ai.vivancedata.com/api/auth/jwks
- AUTH_JWT_ISSUER: expected `iss` (Better Auth: its BETTER_AUTH_URL)
- AUTH_JWT_AUDIENCE: expected `aud` (Better Auth: its BETTER_AUTH_URL)
"""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
from jwt import PyJWKClient

# Better Auth's JWT plugin default (Ed25519); lib/auth.ts keeps it.
ALGORITHMS = ["EdDSA"]


def _settings() -> tuple[str, str, str]:
    """(jwks_url, issuer, audience); all three required."""
    settings = {
        "AUTH_JWKS_URL": os.environ.get("AUTH_JWKS_URL", "").strip(),
        "AUTH_JWT_ISSUER": os.environ.get("AUTH_JWT_ISSUER", "").strip(),
        "AUTH_JWT_AUDIENCE": os.environ.get("AUTH_JWT_AUDIENCE", "").strip(),
    }
    missing = [name for name, value in settings.items() if not value]
    if missing:
        raise ValueError(
            f"{', '.join(missing)} not configured (required for Bearer JWT auth)"
        )
    return (
        settings["AUTH_JWKS_URL"],
        settings["AUTH_JWT_ISSUER"],
        settings["AUTH_JWT_AUDIENCE"],
    )


def is_jwt_auth_configured() -> bool:
    try:
        _settings()
    except ValueError:
        return False
    return True


_jwks_cache: dict[str, tuple[PyJWKClient, float]] = {}
_JWKS_CACHE_TTL = 3600  # 1 hour


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    now = time.time()
    if jwks_url in _jwks_cache:
        client, cached_at = _jwks_cache[jwks_url]
        if now - cached_at < _JWKS_CACHE_TTL:
            return client
    client = PyJWKClient(jwks_url)
    _jwks_cache[jwks_url] = (client, now)
    # Evict expired entries
    expired = [k for k, (_, t) in _jwks_cache.items() if now - t >= _JWKS_CACHE_TTL]
    for k in expired:
        del _jwks_cache[k]
    return client


def verify_session_token(token: str) -> dict[str, Any]:
    """
    Verify a session JWT and return its decoded claims.

    Raises jwt.PyJWTError subclasses on invalid tokens and ValueError when
    the verifier is not configured.
    """
    jwks_url, issuer, audience = _settings()

    signing_key = _get_jwks_client(jwks_url).get_signing_key_from_jwt(token)

    return jwt.decode(
        token,
        signing_key.key,
        algorithms=ALGORITHMS,
        issuer=issuer,
        audience=audience,
        options={"require": ["exp", "iat", "sub"]},
    )
