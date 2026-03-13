"""
SSO (Single Sign-On) Authentication Module.

This module provides enterprise SSO integration supporting:
- SAML 2.0 (Security Assertion Markup Language)
- OIDC (OpenID Connect)

Security Architecture:
- All assertions/tokens are validated for signature, expiration, and issuer
- Replay protection via nonce/assertion ID tracking
- Session management with configurable timeouts
- Audit logging for all SSO operations

Usage:
    from src.auth.sso import (
        SSOService,
        SAMLService,
        OIDCService,
        get_sso_service,
    )

    # Get the SSO service singleton
    sso_service = get_sso_service()

    # Configure SAML for an organization
    config = await sso_service.configure_saml(org_id, saml_config)

    # Handle SAML callback
    user = await sso_service.handle_saml_callback(org_id, saml_response)
"""

from src.auth.sso.oidc_service import OIDCService
from src.auth.sso.providers import (
    OIDCProvider,
    SAMLProvider,
    SSOProvider,
    SSOProviderFactory,
    get_provider_factory,
)
from src.auth.sso.saml_service import SAMLService

__all__ = [
    # Providers
    "SSOProvider",
    "SAMLProvider",
    "OIDCProvider",
    "SSOProviderFactory",
    "get_provider_factory",
    # Services
    "SAMLService",
    "OIDCService",
]
