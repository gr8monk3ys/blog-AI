"""
Clerk JWT verification helpers.

The frontend (Next.js) authenticates users with Clerk and sends the session
token as `Authorization: Bearer <jwt>`. The backend verifies the token using
Clerk JWKS.

Configuration:
- CLERK_JWKS_URL (required): JWKS URL for your Clerk instance.
  Example: https://<your-frontend-api>.clerk.accounts.dev/.well-known/jwks.json
- CLERK_JWT_ISSUER (recommended): expected `iss` claim.
- CLERK_JWT_AUDIENCE (optional): expected `aud` claim (many Clerk tokens omit aud).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWKClient


def get_clerk_jwks_url() -> str:
    jwks_url = os.environ.get("CLERK_JWKS_URL", "").strip()
    if not jwks_url:
        raise ValueError("CLERK_JWKS_URL is not configured (required for Clerk JWT auth)")
    return jwks_url.rstrip("/")


def get_clerk_jwt_issuer() -> Optional[str]:
    issuer = os.environ.get("CLERK_JWT_ISSUER", "").strip()
    return issuer.rstrip("/") if issuer else None


def get_clerk_jwt_audience() -> Optional[str]:
    raw = os.environ.get("CLERK_JWT_AUDIENCE", "").strip()
    if not raw or raw.lower() in ("none", "null", "disabled"):
        return None
    return raw


def is_clerk_jwt_configured() -> bool:
    return bool(os.environ.get("CLERK_JWKS_URL"))


@lru_cache(maxsize=4)
def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def verify_clerk_session_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk session token (JWT) and return decoded claims.

    Raises jwt.PyJWTError subclasses on invalid tokens.
    """
    jwks_url = get_clerk_jwks_url()
    issuer = get_clerk_jwt_issuer()
    audience = get_clerk_jwt_audience()

    jwks_client = _get_jwks_client(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    # Try to narrow algorithms from the header when possible.
    alg = None
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
    except Exception:
        pass

    options = {
        "verify_aud": audience is not None,
        "verify_iss": issuer is not None,
    }

    kwargs: Dict[str, Any] = {"options": options}
    if issuer is not None:
        kwargs["issuer"] = issuer
    if audience is not None:
        kwargs["audience"] = audience

    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[alg] if alg else ["RS256"],
        **kwargs,
    )

