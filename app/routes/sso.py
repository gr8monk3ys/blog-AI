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

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import verify_api_key
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


# =============================================================================
# Helper Functions
# =============================================================================


def _get_sso_config(organization_id: str) -> Optional[SSOConfiguration]:
    """
    Get SSO configuration for an organization.

    In production, this would fetch from the database.
    """
    # TODO: Implement database fetch
    # For now, return None to indicate no SSO configured
    return None


def _save_auth_session(session_id: str, data: Dict[str, Any]) -> None:
    """Save authentication session data."""
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    _sso_auth_sessions[session_id] = data
    logger.debug(f"Saved auth session: {session_id[:20]}...")


def _get_auth_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get and validate authentication session data."""
    data = _sso_auth_sessions.get(session_id)
    if not data:
        return None

    # Check timeout
    created_at = datetime.fromisoformat(data.get("created_at", ""))
    if datetime.now(timezone.utc) - created_at > SSO_AUTH_SESSION_TIMEOUT:
        del _sso_auth_sessions[session_id]
        return None

    return data


def _delete_auth_session(session_id: str) -> None:
    """Delete authentication session data."""
    _sso_auth_sessions.pop(session_id, None)


def _create_user_session(
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

    _sso_user_sessions[session_id] = session
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
    sso_config = _get_sso_config(organization_id)

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
    sso_config = _get_sso_config(organization_id)

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
        redirect_url, session_data = await provider.initiate_authentication(
            relay_state=relay_state,
            request_data=request_data,
        )

        # Save session data for callback validation
        session_id = secrets.token_urlsafe(16)
        session_data["organization_id"] = organization_id
        _save_auth_session(session_id, session_data)

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
            f"relay_state: {relay_state or 'none'}"
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
    sso_config = _get_sso_config(organization_id)

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
        session_data = _get_auth_session(session_id) if session_id else {}

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
        session_token = _create_user_session(
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
            _delete_auth_session(session_id)

        # Determine redirect URL
        redirect_url = relay_state or "/"

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
    sso_config = _get_sso_config(organization_id)

    if not sso_config or not sso_config.saml_config:
        # No SSO configured, just redirect to home
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    # Get current session
    session_token = request.cookies.get("sso_session")
    if session_token:
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()
        session = _sso_user_sessions.pop(session_hash, None)

        if session:
            logger.info(
                f"SAML logout for user {session.sso_user.email} in org {organization_id}"
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
    sso_config = _get_sso_config(organization_id)

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
        auth_url, session_data = await provider.initiate_authentication(
            relay_state=redirect_uri,
            login_hint=login_hint,
        )

        # Save session data for callback validation
        session_id = secrets.token_urlsafe(16)
        session_data["organization_id"] = organization_id
        _save_auth_session(session_id, session_data)

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
            f"redirect_uri: {redirect_uri or 'default'}"
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

    sso_config = _get_sso_config(organization_id)

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
        session_data = _get_auth_session(session_id) if session_id else {}

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
        session_token = _create_user_session(
            organization_id=organization_id,
            sso_user=sso_user,
            provider_type=SSOProviderType.OIDC,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Clean up auth session
        if session_id:
            _delete_auth_session(session_id)

        # Determine redirect URL
        redirect_url = session_data.get("relay_state") or "/"

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
    sso_config = _get_sso_config(organization_id)

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

    # Count active sessions for this organization
    active_sessions = sum(
        1
        for s in _sso_user_sessions.values()
        if s.organization_id == organization_id
        and s.expires_at > datetime.now(timezone.utc)
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
    session = _sso_user_sessions.pop(session_hash, None)

    if session:
        logger.info(
            f"SSO logout for user {session.sso_user.email} "
            f"in org {session.organization_id}"
        )

        # Check if we need to redirect to IdP for SLO
        sso_config = _get_sso_config(session.organization_id)
        if sso_config:
            if (
                sso_config.provider_type == SSOProviderType.SAML
                and sso_config.saml_config
                and sso_config.saml_config.idp.slo_url
            ):
                return {
                    "success": True,
                    "message": "Logged out",
                    "slo_redirect": f"/sso/saml/slo/{session.organization_id}",
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
    session = _sso_user_sessions.get(session_hash)

    if not session or session.expires_at < datetime.now(timezone.utc):
        return {"authenticated": False, "reason": "Session expired or not found"}

    return {
        "authenticated": True,
        "user": {
            "email": session.sso_user.email,
            "display_name": session.sso_user.display_name,
            "first_name": session.sso_user.first_name,
            "last_name": session.sso_user.last_name,
            "groups": session.sso_user.groups,
        },
        "organization_id": session.organization_id,
        "provider_type": session.provider_type.value,
        "expires_at": session.expires_at.isoformat(),
        "created_at": session.created_at.isoformat(),
    }
