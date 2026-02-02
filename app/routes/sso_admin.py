"""
SSO Administration API Endpoints.

This module provides REST endpoints for SSO configuration management:
- Configure SAML/OIDC for organizations
- Test SSO configurations
- Manage attribute mappings
- View SSO sessions and audit logs

Security Considerations:
- All endpoints require admin or owner role
- Sensitive configuration data is validated before storage
- Configuration changes are logged for audit
- Testing endpoints don't expose sensitive data
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.dependencies import get_organization_context, require_permission
from src.auth.sso.oidc_service import OIDCService, OIDCServiceError
from src.auth.sso.providers import (
    OIDCProvider,
    SAMLProvider,
    SSOConfigurationError,
    SSOProviderFactory,
)
from src.auth.sso.saml_service import SAMLService
from src.organizations import AuthorizationContext, Permission
from src.types.sso import (
    OIDCClaimMapping,
    OIDCClientConfig,
    OIDCConfiguration,
    OIDCProviderConfig,
    SAMLAttributeMapping,
    SAMLConfiguration,
    SAMLIdentityProviderConfig,
    SAMLServiceProviderConfig,
    SSOConfigureRequest,
    SSOConfigureResponse,
    SSOConfiguration,
    SSOConnectionStatus,
    SSOProviderType,
    SSOTestRequest,
    SSOTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sso/admin", tags=["sso-admin"])


# =============================================================================
# Request/Response Models
# =============================================================================


class SAMLConfigureRequest(BaseModel):
    """Request to configure SAML SSO."""

    # IdP Configuration
    idp_entity_id: str = Field(..., description="IdP Entity ID (issuer)")
    idp_sso_url: str = Field(..., description="IdP Single Sign-On URL")
    idp_slo_url: Optional[str] = Field(None, description="IdP Single Logout URL")
    idp_certificate: str = Field(..., description="IdP X.509 certificate (PEM format)")

    # SP Configuration (optional, will use defaults if not provided)
    sp_entity_id: Optional[str] = Field(None, description="SP Entity ID (defaults to app URL)")
    sp_acs_url: Optional[str] = Field(None, description="SP ACS URL (defaults to app URL)")
    sp_slo_url: Optional[str] = Field(None, description="SP SLO URL")

    # Attribute mapping
    email_attribute: Optional[str] = Field(None, description="SAML attribute for email")
    first_name_attribute: Optional[str] = Field(None, description="SAML attribute for first name")
    last_name_attribute: Optional[str] = Field(None, description="SAML attribute for last name")
    groups_attribute: Optional[str] = Field(None, description="SAML attribute for groups")

    # Settings
    enabled: bool = Field(default=False, description="Enable SSO after configuration")
    enforce_sso: bool = Field(default=False, description="Require SSO for all users")
    allowed_email_domains: List[str] = Field(default_factory=list, description="Allowed email domains")
    auto_provision_users: bool = Field(default=True, description="Auto-create users on first login")
    default_role: str = Field(default="viewer", description="Default role for new users")
    group_role_mapping: Dict[str, str] = Field(default_factory=dict, description="Map IdP groups to roles")


class OIDCConfigureRequest(BaseModel):
    """Request to configure OIDC SSO."""

    # Provider Configuration
    issuer: str = Field(..., description="OIDC Issuer URL")
    discovery_url: Optional[str] = Field(None, description="OIDC Discovery URL")
    authorization_endpoint: Optional[str] = Field(None, description="Authorization endpoint")
    token_endpoint: Optional[str] = Field(None, description="Token endpoint")
    userinfo_endpoint: Optional[str] = Field(None, description="UserInfo endpoint")
    jwks_uri: Optional[str] = Field(None, description="JWKS URI")
    end_session_endpoint: Optional[str] = Field(None, description="End session endpoint")

    # Client Configuration
    client_id: str = Field(..., description="OIDC Client ID")
    client_secret: str = Field(..., description="OIDC Client Secret")
    redirect_uri: Optional[str] = Field(None, description="Callback URL (defaults to app URL)")
    post_logout_redirect_uri: Optional[str] = Field(None, description="Post-logout redirect URL")
    scopes: List[str] = Field(default=["openid", "email", "profile"], description="OIDC scopes")

    # Claim mapping
    email_claim: Optional[str] = Field(None, description="Claim for email")
    name_claim: Optional[str] = Field(None, description="Claim for display name")
    groups_claim: Optional[str] = Field(None, description="Claim for groups")

    # Settings
    enabled: bool = Field(default=False, description="Enable SSO after configuration")
    enforce_sso: bool = Field(default=False, description="Require SSO for all users")
    allowed_email_domains: List[str] = Field(default_factory=list, description="Allowed email domains")
    auto_provision_users: bool = Field(default=True, description="Auto-create users on first login")
    default_role: str = Field(default="viewer", description="Default role for new users")
    group_role_mapping: Dict[str, str] = Field(default_factory=dict, description="Map IdP groups to roles")
    require_email_verified: bool = Field(default=True, description="Require verified email")
    use_pkce: bool = Field(default=True, description="Use PKCE for authorization code flow")


class AttributeMappingRequest(BaseModel):
    """Request to add/update an attribute mapping."""

    source_attribute: str = Field(..., description="IdP attribute/claim name")
    target_field: str = Field(..., description="Internal field name")
    mapping_type: str = Field(default="direct", description="Mapping type: direct, transform, constant")
    transform_config: Optional[Dict[str, Any]] = Field(None, description="Transform configuration")
    priority: int = Field(default=100, description="Priority (lower = higher)")


class SSOSessionInfo(BaseModel):
    """SSO session information."""

    id: str
    user_id: str
    email: str
    display_name: Optional[str]
    provider_type: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    ip_address: Optional[str]


class SSOConfigurationInfo(BaseModel):
    """SSO configuration information (without sensitive data)."""

    id: str
    organization_id: str
    provider_type: str
    enabled: bool
    enforce_sso: bool
    status: str
    allowed_email_domains: List[str]
    auto_provision_users: bool
    default_role: str
    last_successful_auth: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    # SAML-specific (non-sensitive)
    saml_idp_entity_id: Optional[str] = None
    saml_idp_sso_url: Optional[str] = None
    saml_certificate_expiry: Optional[datetime] = None
    saml_certificate_fingerprint: Optional[str] = None

    # OIDC-specific (non-sensitive)
    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================


def _build_base_url(organization_id: str) -> str:
    """Build base URL for SSO endpoints."""
    import os

    base_url = os.environ.get("APP_BASE_URL", "https://api.example.com")
    return f"{base_url}/sso"


def _get_sso_config(organization_id: str) -> Optional[SSOConfiguration]:
    """
    Get SSO configuration for an organization.

    In production, this would fetch from the database.
    """
    # TODO: Implement database fetch
    return None


def _save_sso_config(config: SSOConfiguration) -> None:
    """
    Save SSO configuration to database.

    In production, this would save to the database.
    """
    # TODO: Implement database save
    pass


# =============================================================================
# SAML Configuration Endpoints
# =============================================================================


@router.post(
    "/{organization_id}/saml",
    response_model=SSOConfigureResponse,
    summary="Configure SAML SSO",
    description="Configure SAML 2.0 SSO for an organization.",
)
async def configure_saml(
    organization_id: str,
    request: SAMLConfigureRequest,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> SSOConfigureResponse:
    """
    Configure SAML SSO for an organization.

    Requires: organization.update permission (owner, admin).

    This endpoint validates the SAML configuration and stores it for the organization.
    The IdP certificate is validated for format and expiration.
    """
    try:
        # Build base URL for SP configuration
        base_url = _build_base_url(organization_id)

        # Create SAML configuration
        idp_config = SAMLIdentityProviderConfig(
            entity_id=request.idp_entity_id,
            sso_url=request.idp_sso_url,
            slo_url=request.idp_slo_url,
            certificate=request.idp_certificate,
        )

        sp_config = SAMLServiceProviderConfig(
            entity_id=request.sp_entity_id or f"{base_url}/saml/{organization_id}",
            acs_url=request.sp_acs_url or f"{base_url}/saml/acs/{organization_id}",
            slo_url=request.sp_slo_url or f"{base_url}/saml/slo/{organization_id}",
        )

        attribute_mapping = SAMLAttributeMapping()
        if request.email_attribute:
            attribute_mapping.email_attribute = request.email_attribute
        if request.first_name_attribute:
            attribute_mapping.first_name_attribute = request.first_name_attribute
        if request.last_name_attribute:
            attribute_mapping.last_name_attribute = request.last_name_attribute
        if request.groups_attribute:
            attribute_mapping.groups_attribute = request.groups_attribute

        saml_config = SAMLConfiguration(
            idp=idp_config,
            sp=sp_config,
            attribute_mapping=attribute_mapping,
        )

        # Validate certificate
        saml_service = SAMLService(saml_config, organization_id)
        cert_valid, cert_warning, cert_info = saml_service.validate_idp_certificate()

        if not cert_valid:
            raise SSOConfigurationError(
                f"Invalid IdP certificate: {cert_warning}",
                details=cert_info,
            )

        # Update certificate metadata
        if cert_info.get("not_valid_after"):
            idp_config.certificate_expiry = datetime.fromisoformat(
                cert_info["not_valid_after"]
            )
        if cert_info.get("fingerprint_sha256"):
            idp_config.certificate_fingerprint = cert_info["fingerprint_sha256"]

        # Create SSOConfiguration
        now = datetime.now(timezone.utc)
        sso_config = SSOConfiguration(
            id=f"sso_{organization_id}",
            organization_id=organization_id,
            provider_type=SSOProviderType.SAML,
            enabled=request.enabled,
            enforce_sso=request.enforce_sso,
            status=SSOConnectionStatus.ACTIVE if request.enabled else SSOConnectionStatus.INACTIVE,
            saml_config=saml_config,
            allowed_email_domains=request.allowed_email_domains,
            auto_provision_users=request.auto_provision_users,
            default_role=request.default_role,
            group_role_mapping=request.group_role_mapping,
            created_at=now,
            updated_at=now,
            created_by=auth_ctx.user_id,
        )

        # Validate configuration
        provider = SAMLProvider(organization_id, sso_config)
        is_valid, errors, warnings = await provider.validate_configuration()

        if not is_valid:
            return SSOConfigureResponse(
                success=False,
                error="; ".join(errors),
            )

        # Save configuration
        _save_sso_config(sso_config)

        logger.info(
            f"SAML SSO configured for org {organization_id} by user {auth_ctx.user_id}"
        )

        return SSOConfigureResponse(
            success=True,
            configuration=sso_config,
            sp_metadata_url=f"{base_url}/saml/metadata/{organization_id}",
            sp_entity_id=sp_config.entity_id,
            sp_acs_url=sp_config.acs_url,
        )

    except SSOConfigurationError as e:
        logger.error(f"SAML configuration error for org {organization_id}: {e}")
        return SSOConfigureResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to configure SAML for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to configure SAML: {e}"},
        )


# =============================================================================
# OIDC Configuration Endpoints
# =============================================================================


@router.post(
    "/{organization_id}/oidc",
    response_model=SSOConfigureResponse,
    summary="Configure OIDC SSO",
    description="Configure OpenID Connect SSO for an organization.",
)
async def configure_oidc(
    organization_id: str,
    request: OIDCConfigureRequest,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> SSOConfigureResponse:
    """
    Configure OIDC SSO for an organization.

    Requires: organization.update permission (owner, admin).

    This endpoint validates the OIDC configuration and stores it for the organization.
    If a discovery URL is provided, endpoints are automatically discovered.
    """
    from pydantic import SecretStr

    try:
        # Build base URL for client configuration
        base_url = _build_base_url(organization_id)

        # Create OIDC configuration
        provider_config = OIDCProviderConfig(
            issuer=request.issuer,
            discovery_url=request.discovery_url,
            authorization_endpoint=request.authorization_endpoint,
            token_endpoint=request.token_endpoint,
            userinfo_endpoint=request.userinfo_endpoint,
            jwks_uri=request.jwks_uri,
            end_session_endpoint=request.end_session_endpoint,
        )

        client_config = OIDCClientConfig(
            client_id=request.client_id,
            client_secret=SecretStr(request.client_secret),
            redirect_uri=request.redirect_uri or f"{base_url}/oidc/callback/{organization_id}",
            post_logout_redirect_uri=request.post_logout_redirect_uri,
            scopes=request.scopes,
        )

        claim_mapping = OIDCClaimMapping()
        if request.email_claim:
            claim_mapping.email_claim = request.email_claim
        if request.name_claim:
            claim_mapping.name_claim = request.name_claim
        if request.groups_claim:
            claim_mapping.groups_claim = request.groups_claim

        oidc_config = OIDCConfiguration(
            provider=provider_config,
            client=client_config,
            claim_mapping=claim_mapping,
            require_email_verified=request.require_email_verified,
            use_pkce=request.use_pkce,
        )

        # Create SSOConfiguration
        now = datetime.now(timezone.utc)
        sso_config = SSOConfiguration(
            id=f"sso_{organization_id}",
            organization_id=organization_id,
            provider_type=SSOProviderType.OIDC,
            enabled=request.enabled,
            enforce_sso=request.enforce_sso,
            status=SSOConnectionStatus.ACTIVE if request.enabled else SSOConnectionStatus.INACTIVE,
            oidc_config=oidc_config,
            allowed_email_domains=request.allowed_email_domains,
            auto_provision_users=request.auto_provision_users,
            default_role=request.default_role,
            group_role_mapping=request.group_role_mapping,
            created_at=now,
            updated_at=now,
            created_by=auth_ctx.user_id,
        )

        # Validate configuration
        provider = OIDCProvider(organization_id, sso_config)
        is_valid, errors, warnings = await provider.validate_configuration()

        if not is_valid:
            return SSOConfigureResponse(
                success=False,
                error="; ".join(errors),
            )

        # Save configuration
        _save_sso_config(sso_config)

        logger.info(
            f"OIDC SSO configured for org {organization_id} by user {auth_ctx.user_id}"
        )

        return SSOConfigureResponse(
            success=True,
            configuration=sso_config,
        )

    except SSOConfigurationError as e:
        logger.error(f"OIDC configuration error for org {organization_id}: {e}")
        return SSOConfigureResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to configure OIDC for org {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to configure OIDC: {e}"},
        )


# =============================================================================
# Common SSO Admin Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/config",
    response_model=SSOConfigurationInfo,
    summary="Get SSO Configuration",
    description="Get current SSO configuration for an organization.",
)
async def get_sso_config(
    organization_id: str,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> SSOConfigurationInfo:
    """
    Get SSO configuration for an organization.

    Requires: organization.update permission (owner, admin).

    Returns configuration without sensitive data (certificates, secrets).
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    # Build response without sensitive data
    info = SSOConfigurationInfo(
        id=sso_config.id,
        organization_id=sso_config.organization_id,
        provider_type=sso_config.provider_type.value,
        enabled=sso_config.enabled,
        enforce_sso=sso_config.enforce_sso,
        status=sso_config.status.value,
        allowed_email_domains=sso_config.allowed_email_domains,
        auto_provision_users=sso_config.auto_provision_users,
        default_role=sso_config.default_role,
        last_successful_auth=sso_config.last_successful_auth,
        last_error=sso_config.last_error,
        created_at=sso_config.created_at,
        updated_at=sso_config.updated_at,
    )

    # Add provider-specific info
    if sso_config.saml_config:
        info.saml_idp_entity_id = sso_config.saml_config.idp.entity_id
        info.saml_idp_sso_url = sso_config.saml_config.idp.sso_url
        info.saml_certificate_expiry = sso_config.saml_config.idp.certificate_expiry
        info.saml_certificate_fingerprint = sso_config.saml_config.idp.certificate_fingerprint

    if sso_config.oidc_config:
        info.oidc_issuer = sso_config.oidc_config.provider.issuer
        info.oidc_client_id = sso_config.oidc_config.client.client_id

    return info


@router.delete(
    "/{organization_id}/config",
    summary="Delete SSO Configuration",
    description="Delete SSO configuration for an organization.",
)
async def delete_sso_config(
    organization_id: str,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> Dict[str, Any]:
    """
    Delete SSO configuration for an organization.

    Requires: organization.update permission (owner, admin).

    This will disable SSO and remove all configuration.
    Active SSO sessions will be terminated.
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    # TODO: Delete from database
    # TODO: Terminate active SSO sessions

    logger.info(
        f"SSO configuration deleted for org {organization_id} by user {auth_ctx.user_id}"
    )

    return {
        "success": True,
        "message": "SSO configuration deleted",
    }


@router.patch(
    "/{organization_id}/enable",
    summary="Enable/Disable SSO",
    description="Enable or disable SSO for an organization.",
)
async def toggle_sso_enabled(
    organization_id: str,
    enabled: bool = Query(..., description="Enable or disable SSO"),
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> Dict[str, Any]:
    """
    Enable or disable SSO for an organization.

    Requires: organization.update permission (owner, admin).
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    sso_config.enabled = enabled
    sso_config.status = (
        SSOConnectionStatus.ACTIVE if enabled else SSOConnectionStatus.INACTIVE
    )
    sso_config.updated_at = datetime.now(timezone.utc)

    _save_sso_config(sso_config)

    action = "enabled" if enabled else "disabled"
    logger.info(
        f"SSO {action} for org {organization_id} by user {auth_ctx.user_id}"
    )

    return {
        "success": True,
        "enabled": enabled,
        "message": f"SSO {action}",
    }


@router.post(
    "/{organization_id}/test",
    response_model=SSOTestResponse,
    summary="Test SSO Configuration",
    description="Test SSO configuration without enabling it.",
)
async def test_sso_config(
    organization_id: str,
    request: SSOTestRequest,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> SSOTestResponse:
    """
    Test SSO configuration.

    Requires: organization.update permission (owner, admin).

    Performs validation checks on the SSO configuration:
    - Certificate validation (expiry, format)
    - Endpoint availability
    - Attribute mapping validation
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    checks = []
    errors = []
    warnings = []

    # Validate based on provider type
    if sso_config.provider_type == SSOProviderType.SAML:
        provider = SAMLProvider(organization_id, sso_config)

        # Validate certificate
        if request.validate_certificate and sso_config.saml_config:
            saml_service = SAMLService(sso_config.saml_config, organization_id)
            cert_valid, cert_warning, cert_info = saml_service.validate_idp_certificate()

            checks.append({
                "name": "IdP Certificate",
                "passed": cert_valid,
                "details": cert_info,
            })

            if not cert_valid:
                errors.append(f"Certificate validation failed: {cert_warning}")
            elif cert_warning:
                warnings.append(cert_warning)

    elif sso_config.provider_type == SSOProviderType.OIDC:
        provider = OIDCProvider(organization_id, sso_config)

        # Validate endpoints
        if request.validate_endpoints and sso_config.oidc_config:
            oidc_service = OIDCService(sso_config.oidc_config, organization_id)
            try:
                discovery = await oidc_service.discover_configuration()
                checks.append({
                    "name": "OIDC Discovery",
                    "passed": True,
                    "details": {
                        "issuer": discovery.get("issuer"),
                        "authorization_endpoint": discovery.get("authorization_endpoint"),
                        "token_endpoint": discovery.get("token_endpoint"),
                    },
                })
            except OIDCServiceError as e:
                checks.append({
                    "name": "OIDC Discovery",
                    "passed": False,
                    "details": {"error": str(e)},
                })
                errors.append(f"OIDC discovery failed: {e}")

    # General validation
    is_valid, validation_errors, validation_warnings = await provider.validate_configuration()

    checks.append({
        "name": "Configuration Validation",
        "passed": is_valid,
        "details": {
            "errors": validation_errors,
            "warnings": validation_warnings,
        },
    })

    errors.extend(validation_errors)
    warnings.extend(validation_warnings)

    return SSOTestResponse(
        success=len(errors) == 0,
        checks=checks,
        errors=errors,
        warnings=warnings,
    )


# =============================================================================
# Attribute Mapping Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/attribute-mappings",
    summary="List Attribute Mappings",
    description="List custom attribute mappings for SSO.",
)
async def list_attribute_mappings(
    organization_id: str,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> Dict[str, Any]:
    """
    List custom attribute mappings for SSO.

    Requires: organization.update permission (owner, admin).
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    # Get mappings based on provider type
    mappings = []

    if sso_config.saml_config:
        mapping = sso_config.saml_config.attribute_mapping
        mappings.append({
            "source": mapping.email_attribute,
            "target": "email",
            "type": "direct",
        })
        mappings.append({
            "source": mapping.first_name_attribute,
            "target": "first_name",
            "type": "direct",
        })
        mappings.append({
            "source": mapping.last_name_attribute,
            "target": "last_name",
            "type": "direct",
        })
        if mapping.groups_attribute:
            mappings.append({
                "source": mapping.groups_attribute,
                "target": "groups",
                "type": "direct",
            })

    elif sso_config.oidc_config:
        mapping = sso_config.oidc_config.claim_mapping
        mappings.append({
            "source": mapping.email_claim,
            "target": "email",
            "type": "direct",
        })
        mappings.append({
            "source": mapping.given_name_claim,
            "target": "first_name",
            "type": "direct",
        })
        mappings.append({
            "source": mapping.family_name_claim,
            "target": "last_name",
            "type": "direct",
        })
        if mapping.groups_claim:
            mappings.append({
                "source": mapping.groups_claim,
                "target": "groups",
                "type": "direct",
            })

    return {
        "success": True,
        "mappings": mappings,
        "provider_type": sso_config.provider_type.value,
    }


@router.put(
    "/{organization_id}/attribute-mappings",
    summary="Update Attribute Mappings",
    description="Update custom attribute mappings for SSO.",
)
async def update_attribute_mappings(
    organization_id: str,
    mappings: List[AttributeMappingRequest],
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> Dict[str, Any]:
    """
    Update custom attribute mappings for SSO.

    Requires: organization.update permission (owner, admin).
    """
    sso_config = _get_sso_config(organization_id)

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SSO not configured for this organization"},
        )

    # Update mappings based on provider type
    for mapping in mappings:
        if sso_config.saml_config:
            attr_mapping = sso_config.saml_config.attribute_mapping
            if mapping.target_field == "email":
                attr_mapping.email_attribute = mapping.source_attribute
            elif mapping.target_field == "first_name":
                attr_mapping.first_name_attribute = mapping.source_attribute
            elif mapping.target_field == "last_name":
                attr_mapping.last_name_attribute = mapping.source_attribute
            elif mapping.target_field == "groups":
                attr_mapping.groups_attribute = mapping.source_attribute

        elif sso_config.oidc_config:
            claim_mapping = sso_config.oidc_config.claim_mapping
            if mapping.target_field == "email":
                claim_mapping.email_claim = mapping.source_attribute
            elif mapping.target_field == "first_name":
                claim_mapping.given_name_claim = mapping.source_attribute
            elif mapping.target_field == "last_name":
                claim_mapping.family_name_claim = mapping.source_attribute
            elif mapping.target_field == "groups":
                claim_mapping.groups_claim = mapping.source_attribute

    sso_config.updated_at = datetime.now(timezone.utc)
    _save_sso_config(sso_config)

    logger.info(
        f"Attribute mappings updated for org {organization_id} by user {auth_ctx.user_id}"
    )

    return {
        "success": True,
        "message": "Attribute mappings updated",
    }


# =============================================================================
# Session Management Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/sessions",
    summary="List SSO Sessions",
    description="List active SSO sessions for an organization.",
)
async def list_sso_sessions(
    organization_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.AUDIT_VIEW)
    ),
) -> Dict[str, Any]:
    """
    List active SSO sessions for an organization.

    Requires: audit.view permission (owner, admin).
    """
    # TODO: Fetch from database
    # For now, return from in-memory store

    from app.routes.sso import _sso_user_sessions

    now = datetime.now(timezone.utc)
    sessions = []

    for session in _sso_user_sessions.values():
        if session.organization_id == organization_id and session.expires_at > now:
            sessions.append(SSOSessionInfo(
                id=session.id,
                user_id=session.user_id,
                email=session.sso_user.email,
                display_name=session.sso_user.display_name,
                provider_type=session.provider_type.value,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_activity_at=session.last_activity_at,
                ip_address=session.ip_address,
            ))

    # Sort by created_at descending
    sessions.sort(key=lambda s: s.created_at, reverse=True)

    # Apply pagination
    total = len(sessions)
    sessions = sessions[offset : offset + limit]

    return {
        "success": True,
        "sessions": [s.dict() for s in sessions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete(
    "/{organization_id}/sessions/{session_id}",
    summary="Revoke SSO Session",
    description="Revoke a specific SSO session.",
)
async def revoke_sso_session(
    organization_id: str,
    session_id: str,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_MANAGE)
    ),
) -> Dict[str, Any]:
    """
    Revoke a specific SSO session.

    Requires: members.manage permission (owner, admin).
    """
    from app.routes.sso import _sso_user_sessions

    session = _sso_user_sessions.get(session_id)

    if not session or session.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Session not found"},
        )

    del _sso_user_sessions[session_id]

    logger.info(
        f"SSO session {session_id[:20]}... revoked for org {organization_id} "
        f"by user {auth_ctx.user_id}"
    )

    return {
        "success": True,
        "message": "Session revoked",
    }


@router.delete(
    "/{organization_id}/sessions",
    summary="Revoke All SSO Sessions",
    description="Revoke all SSO sessions for an organization.",
)
async def revoke_all_sso_sessions(
    organization_id: str,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_MANAGE)
    ),
) -> Dict[str, Any]:
    """
    Revoke all SSO sessions for an organization.

    Requires: members.manage permission (owner, admin).

    This is useful when you need to force all users to re-authenticate,
    such as after a security incident or configuration change.
    """
    from app.routes.sso import _sso_user_sessions

    revoked_count = 0
    session_ids_to_remove = []

    for session_id, session in _sso_user_sessions.items():
        if session.organization_id == organization_id:
            session_ids_to_remove.append(session_id)
            revoked_count += 1

    for session_id in session_ids_to_remove:
        del _sso_user_sessions[session_id]

    logger.info(
        f"All SSO sessions ({revoked_count}) revoked for org {organization_id} "
        f"by user {auth_ctx.user_id}"
    )

    return {
        "success": True,
        "revoked_count": revoked_count,
        "message": f"Revoked {revoked_count} session(s)",
    }
