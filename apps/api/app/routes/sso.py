"""
SSO (Single Sign-On) API Endpoints.

This module provides REST endpoints for SSO authentication:
- SAML 2.0: SP metadata, ACS, SLO
- OIDC: Authorization, callback
- SSO status and session management

Security Considerations:
- All SAML responses are validated for signatures
- OIDC tokens are validated for signature, issuer, audience, and expiration
- Replay protection is implemented via assertion/token tracking
- Sessions are managed with secure tokens and timeouts
- All sensitive operations are logged for audit
"""

from __future__ import annotations
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import time as _time
from urllib.parse import urlparse as _urlparse


from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import verify_api_key
from src.auth.sso.persistence import (
    count_active_user_sessions as db_count_active_user_sessions,
    delete_auth_session as db_delete_auth_session,
    delete_user_session as db_delete_user_session,
    get_auth_session as db_get_auth_session,
    get_user_session as db_get_user_session,
    load_sso_config as db_load_sso_config,
    store_auth_session as db_store_auth_session,
    store_user_session as db_store_user_session,
)
from src.auth.sso.oidc_service import OIDCService, OIDCServiceError
from src.auth.sso.providers import (
    OIDCProvider,
    SAMLProvider,
    SSOAuthenticationError,
    SSOConfigurationError,
    SSOProviderFactory,
    SSOReplayError,
    SSOValidationError,
)
from src.auth.sso.saml_service import SAMLService, SAMLServiceError
from src.types.sso import (
    OIDCConfiguration,
    SAMLConfiguration,
    SSOConfiguration,
    SSOConnectionStatus,
    SSOProviderType,
    SSOSession,
    SSOStatusResponse,
    SSOUser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sso", tags=["sso"])

# Session storage (in production, use Redis or database)
# This is a simple in-memory store for demonstration
_sso_auth_sessions: Dict[str, Dict[str, Any]] = {}
_sso_user_sessions: Dict[str, SSOSession] = {}

# Session configuration
SSO_AUTH_SESSION_TIMEOUT = timedelta(minutes=10)  # Auth flow timeout
SSO_USER_SESSION_TIMEOUT = timedelta(hours=8)  # User session timeout

_SSO_SESSION_PREFIX = "sso:auth:"
_SSO_USER_PREFIX = "sso:user:"
_MAX_MEMORY_SESSIONS = 500


def _sanitize_local_redirect_path(url: Optional[str]) -> str:
    if not url:
        return "/"
    cleaned = url.strip()
    if not cleaned.startswith("/") or cleaned.startswith("//") or "\\" in cleaned:
        return "/"
    parsed = _urlparse(cleaned)
    if parsed.scheme or parsed.netloc:
        return "/"
    return cleaned


def _validate_provider_redirect_url(url: str, expected_url: str) -> str:
    parsed = _urlparse(url.strip())
    expected_candidate = expected_url.strip() if isinstance(expected_url, str) else ""
    expected = _urlparse(expected_candidate) if expected_candidate else None

    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Invalid identity provider redirect URL",
                "error_code": "SSO_INVALID_REDIRECT_URL",
            },
        )

    if expected is None or not expected.netloc:
        return parsed.geturl()

    if (
        parsed.scheme.lower() != expected.scheme.lower()
        or parsed.netloc.lower() != expected.netloc.lower()
    ):
        logger.warning(
            "Blocked SSO redirect to unexpected host: expected %s, got %s",
            expected.netloc,
            parsed.netloc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Identity provider redirect validation failed",
                "error_code": "SSO_REDIRECT_VALIDATION_FAILED",
            },
        )

    return parsed.geturl()


async def _get_redis():
    """Get Redis client if available."""
    try:
        from src.storage.redis_client import redis_client
        client = await redis_client.get_client()
        return client
    except Exception:
        return None


def _to_sso_session(value: Any) -> Optional[SSOSession]:
    if isinstance(value, SSOSession):
        return value
    if isinstance(value, dict):
        try:
            return SSOSession.model_validate(value)
        except Exception:
            return None
    return None


async def _load_sso_config(organization_id: str) -> Optional[SSOConfiguration]:
    """Load SSO config from in-memory cache first, then Postgres."""
    config = _get_sso_config(organization_id)
    if config is not None:
        return config

    db_config = await db_load_sso_config(organization_id)
    if db_config is None:
        return None

    # Prime shared in-memory cache used by sso_admin + tests.
    from app.routes.sso_admin import _sso_configurations

    _sso_configurations[organization_id] = db_config
    return db_config


async def _store_auth_session(session_id: str, data: dict, ttl_seconds: int = 600) -> None:
    payload = dict(data)
    payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    redis = await _get_redis()
    if redis:
        import json as _json
        try:
            await redis.setex(
                f"{_SSO_SESSION_PREFIX}{session_id}",
                ttl_seconds,
                _json.dumps(payload, default=str),
            )
        except Exception:
            pass

    await db_store_auth_session(session_id, payload, ttl_seconds)

    # Always keep a copy in the in-memory cache so that reads can fall back
    # to it when Redis/DB are unavailable, and so that session data is
    # accessible for timeout enforcement and cleanup.
    if len(_sso_auth_sessions) >= _MAX_MEMORY_SESSIONS:
        oldest = next(iter(_sso_auth_sessions))
        del _sso_auth_sessions[oldest]
    _sso_auth_sessions[session_id] = payload


async def _get_auth_session(session_id: str) -> dict | None:
    if not session_id:
        return None

    # Check in-memory cache first (always populated by _store_auth_session).
    data = _sso_auth_sessions.get(session_id)

    # Fall back to Redis if not in memory.
    if data is None:
        redis = await _get_redis()
        if redis:
            import json as _json
            try:
                raw = await redis.get(f"{_SSO_SESSION_PREFIX}{session_id}")
                data = _json.loads(raw) if raw else None
            except Exception:
                data = None

    # Fall back to database.
    if data is None:
        data = await db_get_auth_session(session_id)

    if not data:
        return None

    created_at_raw = data.get("created_at")
    if not created_at_raw:
        return data

    try:
        created_at = datetime.fromisoformat(created_at_raw)
    except (TypeError, ValueError):
        await _delete_auth_session(session_id)
        return None

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) - created_at > SSO_AUTH_SESSION_TIMEOUT:
        await _delete_auth_session(session_id)
        return None

    return data


async def _delete_auth_session(session_id: str) -> None:
    redis = await _get_redis()
    if redis:
        try:
            await redis.delete(f"{_SSO_SESSION_PREFIX}{session_id}")
        except Exception:
            pass
    await db_delete_auth_session(session_id)
    _sso_auth_sessions.pop(session_id, None)


async def _delete_user_session(session_id: str) -> None:
    redis = await _get_redis()
    if redis:
        try:
            await redis.delete(f"{_SSO_USER_PREFIX}{session_id}")
        except Exception:
            pass
    await db_delete_user_session(session_id)
    _sso_user_sessions.pop(session_id, None)


async def _store_user_session(session_id: str, session: "SSOSession", ttl_seconds: int = 86400) -> None:
    redis = await _get_redis()
    if redis:
        import json as _json
        try:
            await redis.setex(
                f"{_SSO_USER_PREFIX}{session_id}",
                ttl_seconds,
                _json.dumps(session.model_dump(mode="json", exclude_none=True), default=str),
            )
        except Exception:
            pass

    await db_store_user_session(session_id, session, ttl_seconds)

    # Always keep a copy in the in-memory cache so that reads can fall back
    # to it when Redis/DB are unavailable, and so that session data is
    # accessible for expiry checks and cleanup.
    if len(_sso_user_sessions) >= _MAX_MEMORY_SESSIONS:
        oldest = next(iter(_sso_user_sessions))
        del _sso_user_sessions[oldest]
    _sso_user_sessions[session_id] = session


async def _get_user_session(session_id: str):
    redis = await _get_redis()
    data = None
    if redis:
        import json as _json
        try:
            raw = await redis.get(f"{_SSO_USER_PREFIX}{session_id}")
            data = _json.loads(raw) if raw else None
        except Exception:
            data = None

    if data is not None:
        session = _to_sso_session(data)
        if session is not None:
            return session

    db_session = await db_get_user_session(session_id)
    if db_session is not None:
        return db_session

    fallback = _sso_user_sessions.get(session_id)
    return _to_sso_session(fallback) or fallback


# =============================================================================
# Helper Functions
# =============================================================================


def _get_sso_config(organization_id: str) -> Optional[SSOConfiguration]:
    """
    Get SSO configuration for an organization.

    This implementation uses an in-memory store. In production, this should
    be replaced with a database fetch (e.g., from PostgreSQL, MongoDB, etc.).

    Security Note: SSO configurations contain sensitive data and should be
    stored encrypted at rest in production.
    """
    # Import from sso_admin to share the same storage
    from app.routes.sso_admin import _sso_configurations
    return _sso_configurations.get(organization_id)


async def _create_user_session(
    organization_id: str,
    sso_user: SSOUser,
    provider_type: SSOProviderType,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    saml_session_index: Optional[str] = None,
    saml_name_id: Optional[str] = None,
    saml_name_id_format: Optional[str] = None,
) -> str:
    """Create a user session after successful SSO authentication."""
    session_token = secrets.token_urlsafe(32)
    session_id = hashlib.sha256(session_token.encode()).hexdigest()

    now = datetime.now(timezone.utc)
    session = SSOSession(
        id=session_id,
        organization_id=organization_id,
        user_id=sso_user.email,  # Using email as user_id for simplicity
        sso_user=sso_user,
        provider_type=provider_type,
        created_at=now,
        expires_at=now + SSO_USER_SESSION_TIMEOUT,
        last_activity_at=now,
        ip_address=ip_address,
        user_agent=user_agent,
        saml_session_index=saml_session_index,
        saml_name_id=saml_name_id,
        saml_name_id_format=saml_name_id_format,
    )

    await _store_user_session(session_id, session)
    logger.info(
        f"Created SSO session for user {sso_user.email} in org {organization_id}"
    )

    return session_token


def _get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request information for python3-saml."""
    # Determine if HTTPS
    https = request.url.scheme == "https"
    if request.headers.get("x-forwarded-proto") == "https":
        https = True

    # Get host
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))

    # Get port
    port = 443 if https else 80
    if ":" in host:
        host, port_str = host.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            pass

    return {
        "https": "on" if https else "off",
        "http_host": host,
        "server_port": port,
        "script_name": str(request.url.path),
        "get_data": dict(request.query_params),
        "post_data": {},  # Will be populated for POST requests
    }


# =============================================================================
# SAML Endpoints
# =============================================================================


@router.get(
    "/saml/metadata/{organization_id}",
    response_class=Response,
    summary="Get SAML SP Metadata",
    description="Generate and return Service Provider (SP) metadata XML for SAML configuration.",
)
async def get_saml_metadata(
    organization_id: str,
) -> Response:
    """
    Get SAML Service Provider metadata XML.

    This endpoint returns the SP metadata that should be provided to the
    Identity Provider (IdP) during SAML configuration.
    """
    # Get SSO configuration
    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.saml_config:
        # Return a template metadata based on environment configuration
        sp_entity_id = os.environ.get(
            "SAML_SP_ENTITY_ID",
            f"https://api.example.com/sso/saml/{organization_id}",
        )
        sp_acs_url = os.environ.get(
            "SAML_SP_ACS_URL",
            f"https://api.example.com/sso/saml/acs/{organization_id}",
        )

        # Generate basic metadata template
        metadata = f"""<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{sp_entity_id}">
    <md:SPSSODescriptor AuthnRequestsSigned="true"
                        WantAssertionsSigned="true"
                        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                     Location="{sp_acs_url}"
                                     index="0"
                                     isDefault="true"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

        return Response(
            content=metadata,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="sp-metadata-{organization_id}.xml"'
            },
        )

    # Generate metadata from configuration
    saml_service = SAMLService(sso_config.saml_config, organization_id)
    metadata = saml_service.generate_sp_metadata()

    return Response(
        content=metadata,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="sp-metadata-{organization_id}.xml"'
        },
    )


@router.get(
    "/saml/login/{organization_id}",
    summary="Initiate SAML Login",
    description="Start the SAML authentication flow by redirecting to the IdP.",
)
async def saml_login(
    organization_id: str,
    request: Request,
    relay_state: Optional[str] = Query(None, description="URL to redirect after login"),
) -> RedirectResponse:
    """
    Initiate SAML authentication.

    Redirects the user to the Identity Provider (IdP) for authentication.
    """
    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.saml_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SSO not configured for this organization",
                "error_code": "SSO_NOT_CONFIGURED",
            },
        )

    if not sso_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "SSO is not enabled for this organization",
                "error_code": "SSO_DISABLED",
            },
        )

    try:
        # Create SAML provider
        provider = SAMLProvider(organization_id, sso_config)

        # Get request data for python3-saml
        request_data = _get_request_info(request)

        # Initiate authentication
        safe_relay_state = _sanitize_local_redirect_path(relay_state)
        redirect_url, session_data = await provider.initiate_authentication(
            relay_state=safe_relay_state,
            request_data=request_data,
        )
        redirect_url = _validate_provider_redirect_url(
            redirect_url,
            provider.saml_config.idp.sso_url,
        )

        # Save session data for callback validation
        session_id = secrets.token_urlsafe(16)
        session_data["organization_id"] = organization_id
        await _store_auth_session(session_id, session_data)

        # Set session cookie and redirect
        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        response.set_cookie(
            key="sso_auth_session",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(SSO_AUTH_SESSION_TIMEOUT.total_seconds()),
        )

        logger.info(
            f"SAML login initiated for org {organization_id}, "
            f"relay_state: {safe_relay_state or '/'}"
        )

        return response

    except SSOConfigurationError as e:
        logger.error(f"SAML configuration error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": e.error_code},
        )


@router.post(
    "/saml/acs/{organization_id}",
    summary="SAML Assertion Consumer Service",
    description="Handle SAML Response from the Identity Provider.",
)
async def saml_acs(
    organization_id: str,
    request: Request,
) -> RedirectResponse:
    """
    SAML Assertion Consumer Service (ACS).

    Processes the SAML Response from the IdP and creates a user session.
    """
    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.saml_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SSO not configured for this organization",
                "error_code": "SSO_NOT_CONFIGURED",
            },
        )

    try:
        # Get form data
        form_data = await request.form()
        saml_response = form_data.get("SAMLResponse")
        relay_state = form_data.get("RelayState")

        if not saml_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Missing SAMLResponse",
                    "error_code": "SAML_MISSING_RESPONSE",
                },
            )

        # Get session data
        session_id = request.cookies.get("sso_auth_session")
        session_data = (await _get_auth_session(session_id)) if session_id else {}

        # Create SAML provider
        provider = SAMLProvider(organization_id, sso_config)

        # Build request data
        request_info = _get_request_info(request)
        request_info["post_data"] = {
            "SAMLResponse": saml_response,
            "RelayState": relay_state or "",
        }

        # Handle callback
        sso_user = await provider.handle_callback(
            callback_data={"request_data": request_info},
            session_data=session_data,
        )

        # Validate email domain if configured
        if sso_config.allowed_email_domains:
            email_domain = sso_user.email.split("@")[-1].lower()
            if email_domain not in [d.lower() for d in sso_config.allowed_email_domains]:
                logger.warning(
                    f"SSO login rejected: email domain {email_domain} not allowed "
                    f"for org {organization_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": f"Email domain {email_domain} is not allowed",
                        "error_code": "SSO_DOMAIN_NOT_ALLOWED",
                    },
                )

        # Create user session
        session_token = await _create_user_session(
            organization_id=organization_id,
            sso_user=sso_user,
            provider_type=SSOProviderType.SAML,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            saml_session_index=session_data.get("session_index"),
            saml_name_id=sso_user.provider_user_id,
        )

        # Clean up auth session
        if session_id:
            await _delete_auth_session(session_id)

        # Determine redirect URL from the validated server-side session only.
        redirect_url = _sanitize_local_redirect_path(
            session_data.get("relay_state") if session_data else None
        )

        # Create response with session token
        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        response.set_cookie(
            key="sso_session",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(SSO_USER_SESSION_TIMEOUT.total_seconds()),
        )
        response.delete_cookie("sso_auth_session")

        logger.info(
            f"SAML login successful for user {sso_user.email} in org {organization_id}"
        )

        return response

    except SSOAuthenticationError as e:
        logger.error(f"SAML authentication error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": str(e), "error_code": e.error_code},
        )
    except SSOValidationError as e:
        logger.error(f"SAML validation error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "error_code": e.error_code},
        )
    except SSOReplayError as e:
        logger.warning(f"SAML replay attack detected for org {organization_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "error_code": e.error_code},
        )


@router.get(
    "/saml/slo/{organization_id}",
    summary="SAML Single Logout",
    description="Handle SAML Single Logout (SLO) request or response.",
)
async def saml_slo(
    organization_id: str,
    request: Request,
) -> RedirectResponse:
    """
    SAML Single Logout (SLO).

    Handles both IdP-initiated logout requests and logout responses.
    """
    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.saml_config:
        # No SSO configured, just redirect to home but always clear local cookies.
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("sso_session")
        response.delete_cookie("sso_auth_session")
        return response

    # Get current session
    session_token = request.cookies.get("sso_session")
    if session_token:
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()
        session = await _get_user_session(session_hash)

        if session:
            await _delete_user_session(session_hash)
            user_email = session.sso_user.email if hasattr(session, 'sso_user') else session.get('sso_user', {}).get('email', 'unknown')
            logger.info(
                f"SAML logout for user {user_email} in org {organization_id}"
            )

    # Create response
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sso_session")
    response.delete_cookie("sso_auth_session")

    return response


# =============================================================================
# OIDC Endpoints
# =============================================================================


@router.get(
    "/oidc/authorize/{organization_id}",
    summary="Initiate OIDC Authorization",
    description="Start the OIDC authorization code flow.",
)
async def oidc_authorize(
    organization_id: str,
    request: Request,
    redirect_uri: Optional[str] = Query(None, description="URL to redirect after login"),
    login_hint: Optional[str] = Query(None, description="Pre-fill email field"),
) -> RedirectResponse:
    """
    Initiate OIDC authorization.

    Redirects the user to the OIDC provider for authentication.
    """
    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.oidc_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SSO not configured for this organization",
                "error_code": "SSO_NOT_CONFIGURED",
            },
        )

    if not sso_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "SSO is not enabled for this organization",
                "error_code": "SSO_DISABLED",
            },
        )

    try:
        # Create OIDC provider
        provider = OIDCProvider(organization_id, sso_config)

        # Initiate authentication
        safe_redirect_uri = _sanitize_local_redirect_path(redirect_uri)
        auth_url, session_data = await provider.initiate_authentication(
            relay_state=safe_redirect_uri,
            login_hint=login_hint,
        )
        auth_url = _validate_provider_redirect_url(
            auth_url,
            provider.oidc_config.provider.authorization_endpoint or "",
        )

        # Save session data for callback validation
        session_id = secrets.token_urlsafe(16)
        session_data["organization_id"] = organization_id
        await _store_auth_session(session_id, session_data)

        # Set session cookie and redirect
        response = RedirectResponse(
            url=auth_url,
            status_code=status.HTTP_302_FOUND,
        )
        response.set_cookie(
            key="sso_auth_session",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(SSO_AUTH_SESSION_TIMEOUT.total_seconds()),
        )

        logger.info(
            f"OIDC authorization initiated for org {organization_id}, "
            f"redirect_uri: {safe_redirect_uri or '/'}"
        )

        return response

    except SSOConfigurationError as e:
        logger.error(f"OIDC configuration error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": e.error_code},
        )


@router.get(
    "/oidc/callback/{organization_id}",
    summary="OIDC Callback",
    description="Handle OIDC authorization callback.",
)
async def oidc_callback(
    organization_id: str,
    request: Request,
    code: Optional[str] = Query(None, description="Authorization code"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error code"),
    error_description: Optional[str] = Query(None, description="Error description"),
) -> RedirectResponse:
    """
    OIDC Authorization Callback.

    Handles the callback from the OIDC provider after authentication.
    """
    # Check for error response
    if error:
        logger.error(
            f"OIDC error callback for org {organization_id}: {error} - {error_description}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": error_description or error,
                "error_code": f"OIDC_{error.upper()}",
            },
        )

    sso_config = await _load_sso_config(organization_id)

    if not sso_config or not sso_config.oidc_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SSO not configured for this organization",
                "error_code": "SSO_NOT_CONFIGURED",
            },
        )

    try:
        # Get session data
        session_id = request.cookies.get("sso_auth_session")
        session_data = (await _get_auth_session(session_id)) if session_id else {}

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid or expired authentication session",
                    "error_code": "OIDC_SESSION_EXPIRED",
                },
            )

        # Create OIDC provider
        provider = OIDCProvider(organization_id, sso_config)

        # Handle callback
        sso_user = await provider.handle_callback(
            callback_data={
                "code": code,
                "state": state,
            },
            session_data=session_data,
        )

        # Validate email domain if configured
        if sso_config.allowed_email_domains:
            email_domain = sso_user.email.split("@")[-1].lower()
            if email_domain not in [d.lower() for d in sso_config.allowed_email_domains]:
                logger.warning(
                    f"SSO login rejected: email domain {email_domain} not allowed "
                    f"for org {organization_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": f"Email domain {email_domain} is not allowed",
                        "error_code": "SSO_DOMAIN_NOT_ALLOWED",
                    },
                )

        # Validate email verification if required
        if sso_config.oidc_config.require_email_verified and not sso_user.email_verified:
            logger.warning(
                f"SSO login rejected: email not verified for {sso_user.email} "
                f"in org {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Email address has not been verified",
                    "error_code": "SSO_EMAIL_NOT_VERIFIED",
                },
            )

        # Create user session
        session_token = await _create_user_session(
            organization_id=organization_id,
            sso_user=sso_user,
            provider_type=SSOProviderType.OIDC,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Clean up auth session
        if session_id:
            await _delete_auth_session(session_id)

        # Determine redirect URL from the validated server-side session only.
        redirect_url = _sanitize_local_redirect_path(
            session_data.get("relay_state") if session_data else None
        )

        # Create response with session token
        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        response.set_cookie(
            key="sso_session",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(SSO_USER_SESSION_TIMEOUT.total_seconds()),
        )
        response.delete_cookie("sso_auth_session")

        logger.info(
            f"OIDC login successful for user {sso_user.email} in org {organization_id}"
        )

        return response

    except SSOAuthenticationError as e:
        logger.error(f"OIDC authentication error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": str(e), "error_code": e.error_code},
        )
    except SSOValidationError as e:
        logger.error(f"OIDC validation error for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "error_code": e.error_code},
        )
    except SSOReplayError as e:
        logger.warning(f"OIDC replay attack detected for org {organization_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "error_code": e.error_code},
        )


# =============================================================================
# SSO Status and Session Endpoints
# =============================================================================


@router.get(
    "/status/{organization_id}",
    response_model=SSOStatusResponse,
    summary="Get SSO Status",
    description="Get SSO configuration status for an organization.",
)
async def get_sso_status(
    organization_id: str,
) -> SSOStatusResponse:
    """
    Get SSO status for an organization.

    Returns whether SSO is configured and enabled, along with current status.
    """
    sso_config = await _load_sso_config(organization_id)

    if not sso_config:
        return SSOStatusResponse(
            enabled=False,
            provider_type=None,
            status=None,
            enforce_sso=False,
            last_successful_auth=None,
            last_error=None,
            certificate_expiry=None,
            active_sessions_count=0,
        )

    # Count active sessions (DB first, in-memory fallback).
    active_sessions = await db_count_active_user_sessions(organization_id)
    if active_sessions is None:
        now = datetime.now(timezone.utc)
        active_sessions = sum(
            1
            for s in _sso_user_sessions.values()
            if s.organization_id == organization_id and s.expires_at > now
        )

    # Get certificate expiry for SAML
    cert_expiry = None
    if sso_config.saml_config:
        cert_expiry = sso_config.saml_config.idp.certificate_expiry

    return SSOStatusResponse(
        enabled=sso_config.enabled,
        provider_type=sso_config.provider_type,
        status=sso_config.status,
        enforce_sso=sso_config.enforce_sso,
        last_successful_auth=sso_config.last_successful_auth,
        last_error=sso_config.last_error,
        certificate_expiry=cert_expiry,
        active_sessions_count=active_sessions,
    )


@router.post(
    "/logout",
    summary="SSO Logout",
    description="Log out from SSO session.",
)
async def sso_logout(
    request: Request,
) -> Dict[str, Any]:
    """
    Log out from SSO session.

    Terminates the current SSO session and optionally redirects to IdP logout.
    """
    session_token = request.cookies.get("sso_session")

    if not session_token:
        return {"success": True, "message": "No active session"}

    # Find and remove session
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()
    session = await _get_user_session(session_hash)

    if session:
        await _delete_user_session(session_hash)
        user_email = session.sso_user.email if hasattr(session, 'sso_user') else session.get('sso_user', {}).get('email', 'unknown')
        org_id = session.organization_id if hasattr(session, 'organization_id') else session.get('organization_id', 'unknown')
        logger.info(
            f"SSO logout for user {user_email} "
            f"in org {org_id}"
        )

        # Check if we need to redirect to IdP for SLO
        sso_config = await _load_sso_config(org_id)
        if sso_config:
            if (
                sso_config.provider_type == SSOProviderType.SAML
                and sso_config.saml_config
                and sso_config.saml_config.idp.slo_url
            ):
                return {
                    "success": True,
                    "message": "Logged out",
                    "slo_redirect": f"/sso/saml/slo/{org_id}",
                }

    return {"success": True, "message": "Logged out"}


@router.get(
    "/session",
    summary="Get Current SSO Session",
    description="Get information about the current SSO session.",
)
async def get_sso_session(
    request: Request,
) -> Dict[str, Any]:
    """
    Get current SSO session information.

    Returns session details if a valid session exists.
    """
    session_token = request.cookies.get("sso_session")

    if not session_token:
        return {"authenticated": False}

    session_hash = hashlib.sha256(session_token.encode()).hexdigest()
    session = await _get_user_session(session_hash)

    if not session:
        return {"authenticated": False, "reason": "Session expired or not found"}

    expires_at = session.expires_at if hasattr(session, 'expires_at') else datetime.fromisoformat(session.get('expires_at', ''))
    if expires_at < datetime.now(timezone.utc):
        return {"authenticated": False, "reason": "Session expired or not found"}

    sso_user = session.sso_user if hasattr(session, 'sso_user') else session.get('sso_user', {})
    if hasattr(sso_user, 'email'):
        user_data = {
            "email": sso_user.email,
            "display_name": sso_user.display_name,
            "first_name": sso_user.first_name,
            "last_name": sso_user.last_name,
            "groups": sso_user.groups,
        }
    else:
        user_data = {
            "email": sso_user.get("email"),
            "display_name": sso_user.get("display_name"),
            "first_name": sso_user.get("first_name"),
            "last_name": sso_user.get("last_name"),
            "groups": sso_user.get("groups", []),
        }

    org_id = session.organization_id if hasattr(session, 'organization_id') else session.get('organization_id')
    provider_type = session.provider_type.value if hasattr(session, 'provider_type') else session.get('provider_type')
    created_at = session.created_at.isoformat() if hasattr(session, 'created_at') else session.get('created_at')

    return {
        "authenticated": True,
        "user": user_data,
        "organization_id": org_id,
        "provider_type": provider_type,
        "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at),
        "created_at": created_at,
    }
