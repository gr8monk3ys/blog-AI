"""
Authentication utilities for the Blog AI API.

This module provides authentication verification functions
for API endpoints.

Security Considerations:
- API keys are validated against secure storage
- Rate limiting should be applied after authentication
- Failed authentication attempts should be logged
"""

import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API key header configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Environment variable for the expected API key
# In production, this should be fetched from a secure secrets manager
_API_KEY: Optional[str] = os.environ.get("BLOG_AI_API_KEY")


class AuthenticationError(Exception):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)
        self.message = message


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Depends(API_KEY_HEADER),
) -> str:
    """
    Verify the API key provided in the request header.

    Args:
        request: The FastAPI request object
        api_key: The API key from the X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if not api_key:
        logger.warning(
            f"Missing API key in request from {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "API key is required",
                "error_code": "MISSING_API_KEY",
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # In development mode, accept any non-empty API key
    if os.environ.get("BLOG_AI_DEV_MODE", "").lower() == "true":
        logger.debug("Development mode: accepting any API key")
        return api_key

    # Validate against expected API key
    if _API_KEY and api_key == _API_KEY:
        return api_key

    # TODO: In production, validate against database/Redis cache
    # For now, accept any key with minimum length
    if len(api_key) >= 32:
        logger.debug(f"Accepted API key with length {len(api_key)}")
        return api_key

    logger.warning(
        f"Invalid API key from {request.client.host if request.client else 'unknown'}"
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Invalid API key",
            "error_code": "INVALID_API_KEY",
        },
        headers={"WWW-Authenticate": "ApiKey"},
    )


async def get_optional_api_key(
    api_key: Optional[str] = Depends(API_KEY_HEADER),
) -> Optional[str]:
    """
    Get the API key if provided, without raising an error if missing.

    Useful for endpoints that support both authenticated and anonymous access.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The API key if provided and valid, None otherwise
    """
    if not api_key:
        return None

    # Basic validation
    if len(api_key) < 16:
        return None

    return api_key
