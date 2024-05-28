"""
SSO (Single Sign-On) Type Definitions.

This module defines all data models for enterprise SSO integration,
supporting both SAML 2.0 and OpenID Connect (OIDC) protocols.

Security Considerations:
- All sensitive data (private keys, client secrets) should be stored encrypted
- Session tokens should have limited lifetime and be rotated
- Assertion/token replay protection is mandatory
- All IdP communications should use TLS 1.2+
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator


# =============================================================================
# Enums
# =============================================================================


class SSOProviderType(str, Enum):
    """Supported SSO provider types."""

    SAML = "saml"
    OIDC = "oidc"


class SSOConnectionStatus(str, Enum):
    """SSO connection status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_CONFIGURATION = "pending_configuration"
    CONFIGURATION_ERROR = "configuration_error"
    CERTIFICATE_EXPIRING = "certificate_expiring"
    CERTIFICATE_EXPIRED = "certificate_expired"


class SAMLNameIDFormat(str, Enum):
    """SAML NameID formats."""

    EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"
    UNSPECIFIED = "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"


class SAMLBindingType(str, Enum):
    """SAML binding types."""

    HTTP_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    HTTP_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"


class OIDCResponseType(str, Enum):
    """OIDC response types."""

    CODE = "code"
    ID_TOKEN = "id_token"
    TOKEN = "token"


class OIDCGrantType(str, Enum):
    """OIDC grant types."""

    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"


# =============================================================================
# SAML Configuration Models
# =============================================================================


class SAMLIdentityProviderConfig(BaseModel):
    """
    SAML Identity Provider (IdP) configuration.

    Security:
    - entity_id must be validated against IdP metadata
    - Certificates must be verified for proper chain and expiration
    - SSO URLs must use HTTPS
    """

    entity_id: str = Field(
        ...,
        description="IdP Entity ID (issuer)",
        min_length=1,
        max_length=2048,
    )
    sso_url: str = Field(
        ...,
        description="IdP Single Sign-On URL",
        pattern=r"^https://",
    )
    slo_url: Optional[str] = Field(
        None,
        description="IdP Single Logout URL (optional)",
        pattern=r"^https://",
    )
    certificate: str = Field(
        ...,
        description="IdP X.509 certificate (PEM format) for signature validation",
        min_length=100,
    )
    certificate_fingerprint: Optional[str] = Field(
        None,
        description="SHA-256 fingerprint of the certificate",
    )
    certificate_expiry: Optional[datetime] = Field(
        None,
        description="Certificate expiration date",
    )
    binding_type: SAMLBindingType = Field(
        default=SAMLBindingType.HTTP_POST,
        description="Preferred SAML binding type",
    )

    @field_validator("certificate")
    @classmethod
    def validate_certificate_format(cls, v: str) -> str:
        """Ensure certificate is in PEM format."""
        v = v.strip()
        if not v.startswith("-----BEGIN CERTIFICATE-----"):
            raise ValueError("Certificate must be in PEM format")
        if not v.endswith("-----END CERTIFICATE-----"):
            raise ValueError("Certificate must be in PEM format")
        return v


class SAMLServiceProviderConfig(BaseModel):
    """
    SAML Service Provider (SP) configuration.

    This represents our application's SAML configuration.
    """

    entity_id: str = Field(
        ...,
        description="SP Entity ID (our application identifier)",
    )
    acs_url: str = Field(
        ...,
        description="Assertion Consumer Service URL",
        pattern=r"^https?://",
    )
    slo_url: Optional[str] = Field(
        None,
        description="Single Logout URL",
        pattern=r"^https?://",
    )
    metadata_url: Optional[str] = Field(
        None,
        description="SP Metadata URL",
    )
    name_id_format: SAMLNameIDFormat = Field(
        default=SAMLNameIDFormat.EMAIL,
        description="Preferred NameID format",
    )
    authn_requests_signed: bool = Field(
        default=True,
        description="Whether AuthnRequests should be signed",
    )
    want_assertions_signed: bool = Field(
        default=True,
        description="Whether we require signed assertions",
    )
    want_assertions_encrypted: bool = Field(
        default=False,
        description="Whether we require encrypted assertions",
    )


class SAMLAttributeMapping(BaseModel):
    """
    Mapping between SAML assertion attributes and user attributes.

    Security:
    - All attribute values should be sanitized before use
    - Group membership should be validated against allowed values
    """

    email_attribute: str = Field(
        default="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        description="SAML attribute containing user email",
    )
    first_name_attribute: str = Field(
        default="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
        description="SAML attribute containing first name",
    )
    last_name_attribute: str = Field(
        default="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
        description="SAML attribute containing last name",
    )
    display_name_attribute: Optional[str] = Field(
        default="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        description="SAML attribute containing display name",
    )
    groups_attribute: Optional[str] = Field(
        default="http://schemas.microsoft.com/ws/2008/06/identity/claims/groups",
        description="SAML attribute containing group memberships",
    )
    custom_attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional custom attribute mappings",
    )


class SAMLConfiguration(BaseModel):
    """
    Complete SAML configuration for an organization.

    Security:
    - Private key should never be logged or exposed in API responses
    - Certificates should be validated for proper chain of trust
    """

    idp: SAMLIdentityProviderConfig
    sp: SAMLServiceProviderConfig
    attribute_mapping: SAMLAttributeMapping = Field(default_factory=SAMLAttributeMapping)

    # Security settings
    signature_algorithm: str = Field(
        default="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        description="XML signature algorithm",
    )
    digest_algorithm: str = Field(
        default="http://www.w3.org/2001/04/xmlenc#sha256",
        description="XML digest algorithm",
    )

    # Validation settings
    allow_clock_skew_seconds: int = Field(
        default=120,
        ge=0,
        le=600,
        description="Allowed clock skew for assertion validation",
    )
    assertion_lifetime_seconds: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Maximum assertion lifetime",
    )

    # Debug settings (should be disabled in production)
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode (logs SAML assertions - NEVER in production)",
    )


# =============================================================================
# OIDC Configuration Models
# =============================================================================


class OIDCProviderConfig(BaseModel):
    """
    OIDC Provider (IdP/OP) configuration.

    Security:
    - Discovery URL should use HTTPS
    - JWKS should be cached and refreshed securely
    - Client secret must be stored encrypted
    """

    issuer: str = Field(
        ...,
        description="OIDC Issuer URL",
        pattern=r"^https://",
    )
    discovery_url: Optional[str] = Field(
        None,
        description="OIDC Discovery URL (.well-known/openid-configuration)",
        pattern=r"^https://",
    )
    authorization_endpoint: Optional[str] = Field(
        None,
        description="Authorization endpoint (auto-discovered if discovery_url set)",
    )
    token_endpoint: Optional[str] = Field(
        None,
        description="Token endpoint (auto-discovered if discovery_url set)",
    )
    userinfo_endpoint: Optional[str] = Field(
        None,
        description="UserInfo endpoint (auto-discovered if discovery_url set)",
    )
    jwks_uri: Optional[str] = Field(
        None,
        description="JWKS URI (auto-discovered if discovery_url set)",
    )
    end_session_endpoint: Optional[str] = Field(
        None,
        description="End session endpoint for logout",
    )


class OIDCClientConfig(BaseModel):
    """
    OIDC Client configuration (our application).

    Security:
    - client_secret must be stored encrypted at rest
    - redirect_uri must be validated against registered URIs
    """

    client_id: str = Field(
        ...,
        description="OIDC Client ID",
        min_length=1,
    )
    client_secret: SecretStr = Field(
        ...,
        description="OIDC Client Secret",
    )
    redirect_uri: str = Field(
        ...,
        description="Callback URL after authentication",
        pattern=r"^https?://",
    )
    post_logout_redirect_uri: Optional[str] = Field(
        None,
        description="URL to redirect after logout",
    )
    scopes: List[str] = Field(
        default=["openid", "email", "profile"],
        description="OIDC scopes to request",
    )
    response_type: OIDCResponseType = Field(
        default=OIDCResponseType.CODE,
        description="OIDC response type",
    )


class OIDCClaimMapping(BaseModel):
    """
    Mapping between OIDC claims and user attributes.

    Standard claims are used by default but can be overridden
    for non-standard IdP implementations.
    """

    email_claim: str = Field(
        default="email",
        description="Claim containing user email",
    )
    email_verified_claim: str = Field(
        default="email_verified",
        description="Claim indicating email verification status",
    )
    name_claim: str = Field(
        default="name",
        description="Claim containing full name",
    )
    given_name_claim: str = Field(
        default="given_name",
        description="Claim containing first name",
    )
    family_name_claim: str = Field(
        default="family_name",
        description="Claim containing last name",
    )
    picture_claim: str = Field(
        default="picture",
        description="Claim containing profile picture URL",
    )
    groups_claim: Optional[str] = Field(
        default="groups",
        description="Claim containing group memberships",
    )
    custom_claims: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional custom claim mappings",
    )


class OIDCConfiguration(BaseModel):
    """
    Complete OIDC configuration for an organization.

    Security:
    - Token validation must verify signature, issuer, audience, and expiration
    - Nonce must be validated to prevent replay attacks
    - State parameter must be used to prevent CSRF
    """

    provider: OIDCProviderConfig
    client: OIDCClientConfig
    claim_mapping: OIDCClaimMapping = Field(default_factory=OIDCClaimMapping)

    # Token validation settings
    validate_nonce: bool = Field(
        default=True,
        description="Validate nonce in ID token (required for implicit flow)",
    )
    allow_clock_skew_seconds: int = Field(
        default=120,
        ge=0,
        le=600,
        description="Allowed clock skew for token validation",
    )
    require_email_verified: bool = Field(
        default=True,
        description="Require email_verified claim to be true",
    )

    # PKCE settings (recommended for authorization code flow)
    use_pkce: bool = Field(
        default=True,
        description="Use PKCE for authorization code flow",
    )
    pkce_method: str = Field(
        default="S256",
        description="PKCE code challenge method",
    )


# =============================================================================
# SSO Session and User Models
# =============================================================================


class SSOUser(BaseModel):
    """
    User information extracted from SSO assertion/token.

    This is the normalized user data regardless of SSO provider.
    """

    provider_user_id: str = Field(
        ...,
        description="User ID from the identity provider",
    )
    email: str = Field(
        ...,
        description="User email address",
    )
    email_verified: bool = Field(
        default=False,
        description="Whether email has been verified by IdP",
    )
    first_name: Optional[str] = Field(
        None,
        description="User's first name",
    )
    last_name: Optional[str] = Field(
        None,
        description="User's last name",
    )
    display_name: Optional[str] = Field(
        None,
        description="User's display name",
    )
    picture_url: Optional[str] = Field(
        None,
        description="URL to user's profile picture",
    )
    groups: List[str] = Field(
        default_factory=list,
        description="Group memberships from IdP",
    )
    raw_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw attributes/claims from IdP",
    )
    provider_type: SSOProviderType = Field(
        ...,
        description="Type of SSO provider",
    )


class SSOSession(BaseModel):
    """
    SSO session information.

    Security:
    - Session tokens should be stored securely (httpOnly cookies)
    - Sessions should have limited lifetime
    - Session ID should be cryptographically random
    """

    id: str = Field(
        ...,
        description="Unique session identifier",
    )
    organization_id: str = Field(
        ...,
        description="Organization this session belongs to",
    )
    user_id: str = Field(
        ...,
        description="Internal user ID",
    )
    sso_user: SSOUser = Field(
        ...,
        description="SSO user information",
    )
    provider_type: SSOProviderType = Field(
        ...,
        description="SSO provider type used for authentication",
    )
    provider_session_id: Optional[str] = Field(
        None,
        description="Session ID from identity provider (for SLO)",
    )
    created_at: datetime = Field(
        ...,
        description="Session creation timestamp",
    )
    expires_at: datetime = Field(
        ...,
        description="Session expiration timestamp",
    )
    last_activity_at: datetime = Field(
        ...,
        description="Last activity timestamp",
    )
    ip_address: Optional[str] = Field(
        None,
        description="IP address of the session",
    )
    user_agent: Optional[str] = Field(
        None,
        description="User agent of the session",
    )

    # SAML-specific fields
    saml_session_index: Optional[str] = Field(
        None,
        description="SAML SessionIndex for SLO",
    )
    saml_name_id: Optional[str] = Field(
        None,
        description="SAML NameID for SLO",
    )
    saml_name_id_format: Optional[str] = Field(
        None,
        description="SAML NameID format",
    )

    # OIDC-specific fields
    oidc_access_token_hash: Optional[str] = Field(
        None,
        description="Hash of OIDC access token (for revocation)",
    )
    oidc_refresh_token_hash: Optional[str] = Field(
        None,
        description="Hash of OIDC refresh token",
    )
    oidc_id_token_hash: Optional[str] = Field(
        None,
        description="Hash of OIDC ID token",
    )


# =============================================================================
# SSO Configuration Models
# =============================================================================


class SSOConfiguration(BaseModel):
    """
    Organization SSO configuration.

    This is the main configuration model stored per organization.
    """

    id: str = Field(
        ...,
        description="Configuration ID",
    )
    organization_id: str = Field(
        ...,
        description="Organization this configuration belongs to",
    )
    provider_type: SSOProviderType = Field(
        ...,
        description="SSO provider type",
    )
    enabled: bool = Field(
        default=False,
        description="Whether SSO is enabled for this organization",
    )
    enforce_sso: bool = Field(
        default=False,
        description="Require SSO for all users (no password login)",
    )
    status: SSOConnectionStatus = Field(
        default=SSOConnectionStatus.PENDING_CONFIGURATION,
        description="Current configuration status",
    )

    # Provider-specific configuration
    saml_config: Optional[SAMLConfiguration] = Field(
        None,
        description="SAML configuration (if provider_type is SAML)",
    )
    oidc_config: Optional[OIDCConfiguration] = Field(
        None,
        description="OIDC configuration (if provider_type is OIDC)",
    )

    # Domain restrictions
    allowed_email_domains: List[str] = Field(
        default_factory=list,
        description="Allowed email domains for SSO users",
    )
    auto_provision_users: bool = Field(
        default=True,
        description="Automatically create users on first SSO login",
    )
    default_role: str = Field(
        default="viewer",
        description="Default role for auto-provisioned users",
    )

    # Group mapping for role assignment
    group_role_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of IdP groups to organization roles",
    )

    # Metadata
    created_at: datetime = Field(
        ...,
        description="Configuration creation timestamp",
    )
    updated_at: datetime = Field(
        ...,
        description="Configuration last update timestamp",
    )
    created_by: str = Field(
        ...,
        description="User who created the configuration",
    )
    last_successful_auth: Optional[datetime] = Field(
        None,
        description="Last successful SSO authentication",
    )
    last_error: Optional[str] = Field(
        None,
        description="Last error message (if any)",
    )
    last_error_at: Optional[datetime] = Field(
        None,
        description="Timestamp of last error",
    )

    @field_validator("allowed_email_domains")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        """Validate and normalize email domains."""
        normalized = []
        for domain in v:
            domain = domain.lower().strip()
            if domain.startswith("@"):
                domain = domain[1:]
            if domain:
                normalized.append(domain)
        return normalized


# =============================================================================
# API Request/Response Models
# =============================================================================


class SSOConfigureRequest(BaseModel):
    """Request to configure SSO for an organization."""

    provider_type: SSOProviderType
    saml_config: Optional[SAMLConfiguration] = None
    oidc_config: Optional[OIDCConfiguration] = None
    allowed_email_domains: List[str] = Field(default_factory=list)
    auto_provision_users: bool = True
    default_role: str = "viewer"
    group_role_mapping: Dict[str, str] = Field(default_factory=dict)
    enforce_sso: bool = False


class SSOConfigureResponse(BaseModel):
    """Response after configuring SSO."""

    success: bool
    configuration: Optional[SSOConfiguration] = None
    sp_metadata_url: Optional[str] = None
    sp_entity_id: Optional[str] = None
    sp_acs_url: Optional[str] = None
    error: Optional[str] = None


class SSOStatusResponse(BaseModel):
    """SSO status for an organization."""

    enabled: bool
    provider_type: Optional[SSOProviderType] = None
    status: Optional[SSOConnectionStatus] = None
    enforce_sso: bool = False
    last_successful_auth: Optional[datetime] = None
    last_error: Optional[str] = None
    certificate_expiry: Optional[datetime] = None
    active_sessions_count: int = 0


class SSOTestRequest(BaseModel):
    """Request to test SSO configuration."""

    validate_certificate: bool = True
    validate_endpoints: bool = True
    test_attribute_mapping: bool = True


class SSOTestResponse(BaseModel):
    """Response from SSO configuration test."""

    success: bool
    checks: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]


class SAMLAuthnRequest(BaseModel):
    """SAML Authentication Request data."""

    id: str
    issue_instant: datetime
    destination: str
    assertion_consumer_service_url: str
    issuer: str
    name_id_policy_format: str
    relay_state: Optional[str] = None


class SAMLAssertion(BaseModel):
    """Parsed SAML Assertion data."""

    id: str
    issuer: str
    subject_name_id: str
    subject_name_id_format: str
    session_index: Optional[str] = None
    authn_instant: datetime
    not_before: datetime
    not_on_or_after: datetime
    audience: str
    attributes: Dict[str, List[str]]
    signature_valid: bool


class OIDCAuthorizationRequest(BaseModel):
    """OIDC Authorization Request data."""

    state: str
    nonce: str
    code_verifier: Optional[str] = None  # For PKCE
    code_challenge: Optional[str] = None  # For PKCE
    redirect_uri: str
    scopes: List[str]
    created_at: datetime


class OIDCTokenResponse(BaseModel):
    """OIDC Token Response data."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: str
    scope: Optional[str] = None


class OIDCIDToken(BaseModel):
    """Parsed OIDC ID Token claims."""

    iss: str
    sub: str
    aud: str
    exp: int
    iat: int
    nonce: Optional[str] = None
    auth_time: Optional[int] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    groups: Optional[List[str]] = None
    raw_claims: Dict[str, Any] = Field(default_factory=dict)
