"""
OpenID Connect (OIDC) Service Implementation.

This module provides comprehensive OIDC support including:
- Authorization code flow with PKCE
- ID token validation and verification
- UserInfo endpoint integration
- Token refresh handling
- Logout support

Security Considerations:
- All tokens must be validated for signature, issuer, audience, and expiration
- Nonce validation is mandatory for implicit/hybrid flows
- PKCE is recommended and enabled by default for authorization code flow
- State parameter prevents CSRF attacks
- Token storage uses secure hashing

Dependencies:
- authlib: pip install authlib
- httpx: pip install httpx
- cryptography: pip install cryptography
- pyjwt: pip install pyjwt
"""

import base64
import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.types.sso import (
    OIDCClaimMapping,
    OIDCConfiguration,
    OIDCIDToken,
    OIDCTokenResponse,
    SSOProviderType,
    SSOUser,
)

logger = logging.getLogger(__name__)


class OIDCServiceError(Exception):
    """OIDC Service specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "OIDC_ERROR"
        self.details = details or {}


class OIDCTokenValidationError(OIDCServiceError):
    """Token validation failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OIDC_TOKEN_VALIDATION_ERROR", details)


class OIDCDiscoveryError(OIDCServiceError):
    """OIDC discovery failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OIDC_DISCOVERY_ERROR", details)


class OIDCService:
    """
    OpenID Connect Service for handling OIDC authentication.

    This service provides methods for:
    - OIDC discovery
    - Authorization URL generation
    - Token exchange and validation
    - UserInfo retrieval
    - Token refresh
    """

    # JWKS cache settings
    JWKS_CACHE_DURATION = timedelta(hours=1)

    def __init__(self, config: OIDCConfiguration, organization_id: str):
        """
        Initialize the OIDC service.

        Args:
            config: OIDC configuration
            organization_id: Organization ID this service is for
        """
        self.config = config
        self.organization_id = organization_id
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._discovery_cache: Optional[Dict[str, Any]] = None

    async def discover_configuration(self) -> Dict[str, Any]:
        """
        Discover OIDC configuration from the discovery endpoint.

        Returns:
            OIDC discovery document
        """
        if self._discovery_cache:
            return self._discovery_cache

        discovery_url = self.config.provider.discovery_url
        if not discovery_url:
            # Build from issuer
            discovery_url = f"{self.config.provider.issuer.rstrip('/')}/.well-known/openid-configuration"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    discovery_url,
                    timeout=10.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
                self._discovery_cache = response.json()
                return self._discovery_cache

        except httpx.HTTPError as e:
            raise OIDCDiscoveryError(
                f"Failed to discover OIDC configuration: {e}",
                details={"discovery_url": discovery_url, "error": str(e)},
            )

    async def get_jwks(self, jwks_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch and cache the JWKS (JSON Web Key Set).

        Args:
            jwks_uri: Optional JWKS URI override

        Returns:
            JWKS document
        """
        # Check cache
        now = datetime.now(timezone.utc)
        if (
            self._jwks_cache
            and self._jwks_cache_time
            and now - self._jwks_cache_time < self.JWKS_CACHE_DURATION
        ):
            return self._jwks_cache

        # Determine JWKS URI
        uri = jwks_uri or self.config.provider.jwks_uri
        if not uri:
            # Try to get from discovery
            discovery = await self.discover_configuration()
            uri = discovery.get("jwks_uri")

        if not uri:
            raise OIDCServiceError(
                "JWKS URI not configured and not found in discovery",
                error_code="OIDC_NO_JWKS_URI",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(uri, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = now
                return self._jwks_cache

        except httpx.HTTPError as e:
            raise OIDCServiceError(
                f"Failed to fetch JWKS: {e}",
                details={"jwks_uri": uri, "error": str(e)},
            )

    @staticmethod
    def generate_pkce_pair() -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge pair.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate 64-byte random code verifier
        code_verifier = secrets.token_urlsafe(64)

        # Create S256 code challenge
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        return code_verifier, code_challenge

    @staticmethod
    def generate_state() -> str:
        """Generate a cryptographically secure state parameter."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce() -> str:
        """Generate a cryptographically secure nonce."""
        return secrets.token_urlsafe(32)

    @staticmethod
    async def validate_id_token(
        id_token: str,
        oidc_config: OIDCConfiguration,
        nonce: Optional[str] = None,
        jwks_uri: Optional[str] = None,
    ) -> OIDCIDToken:
        """
        Validate and decode an OIDC ID token.

        Security validations performed:
        - Signature verification using JWKS
        - Issuer validation
        - Audience validation
        - Expiration validation
        - Not-before validation
        - Nonce validation (if provided)

        Args:
            id_token: The ID token to validate
            oidc_config: OIDC configuration
            nonce: Expected nonce (required for implicit/hybrid flow)
            jwks_uri: Optional JWKS URI override

        Returns:
            Validated and decoded ID token claims

        Raises:
            OIDCTokenValidationError: If validation fails
        """
        import jwt
        from jwt import PyJWKClient

        try:
            # Get JWKS URI
            uri = jwks_uri or oidc_config.provider.jwks_uri
            if not uri:
                raise OIDCTokenValidationError(
                    "JWKS URI not configured",
                    details={"issuer": oidc_config.provider.issuer},
                )

            # Fetch signing key
            jwks_client = PyJWKClient(uri, cache_keys=True)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)

            # Decode and validate token
            # Note: PyJWT performs signature, exp, nbf, iat validation automatically
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
                audience=oidc_config.client.client_id,
                issuer=oidc_config.provider.issuer,
                leeway=oidc_config.allow_clock_skew_seconds,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["exp", "iat", "sub", "iss", "aud"],
                },
            )

            # Validate nonce if required
            if oidc_config.validate_nonce and nonce:
                token_nonce = claims.get("nonce")
                if token_nonce != nonce:
                    raise OIDCTokenValidationError(
                        "Nonce mismatch in ID token",
                        details={
                            "expected_nonce": nonce[:10] + "..." if nonce else None,
                            "received_nonce": (
                                token_nonce[:10] + "..." if token_nonce else None
                            ),
                        },
                    )

            # Parse into structured model
            return OIDCIDToken(
                iss=claims["iss"],
                sub=claims["sub"],
                aud=claims["aud"] if isinstance(claims["aud"], str) else claims["aud"][0],
                exp=claims["exp"],
                iat=claims["iat"],
                nonce=claims.get("nonce"),
                auth_time=claims.get("auth_time"),
                email=claims.get("email"),
                email_verified=claims.get("email_verified"),
                name=claims.get("name"),
                given_name=claims.get("given_name"),
                family_name=claims.get("family_name"),
                picture=claims.get("picture"),
                groups=claims.get("groups"),
                raw_claims=claims,
            )

        except jwt.ExpiredSignatureError:
            raise OIDCTokenValidationError(
                "ID token has expired",
                details={"token_prefix": id_token[:50] + "..."},
            )
        except jwt.InvalidAudienceError:
            raise OIDCTokenValidationError(
                "ID token audience mismatch",
                details={"expected_audience": oidc_config.client.client_id},
            )
        except jwt.InvalidIssuerError:
            raise OIDCTokenValidationError(
                "ID token issuer mismatch",
                details={"expected_issuer": oidc_config.provider.issuer},
            )
        except jwt.InvalidSignatureError:
            raise OIDCTokenValidationError(
                "ID token signature verification failed",
            )
        except jwt.PyJWTError as e:
            raise OIDCTokenValidationError(
                f"ID token validation failed: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            raise OIDCTokenValidationError(
                f"Failed to validate ID token: {e}",
                details={"error": str(e)},
            )

    @staticmethod
    def map_claims_to_user(
        id_token_claims: OIDCIDToken,
        userinfo: Optional[Dict[str, Any]] = None,
        claim_mapping: Optional[OIDCClaimMapping] = None,
    ) -> SSOUser:
        """
        Map OIDC claims to SSOUser.

        Claims from UserInfo endpoint take precedence over ID token claims
        when both are available.

        Args:
            id_token_claims: Validated ID token claims
            userinfo: Optional UserInfo response
            claim_mapping: Optional custom claim mapping

        Returns:
            SSOUser with mapped claims
        """
        mapping = claim_mapping or OIDCClaimMapping()
        userinfo = userinfo or {}

        # Helper to get claim value
        def get_claim(claim_name: str, default: Any = None) -> Any:
            """Get claim from userinfo first, then id_token."""
            # Try userinfo first
            if claim_name in userinfo:
                return userinfo[claim_name]
            # Fall back to id_token raw claims
            return id_token_claims.raw_claims.get(claim_name, default)

        # Extract email
        email = get_claim(mapping.email_claim)
        if not email:
            # Try common alternatives
            for alt in ["email", "preferred_username", "upn"]:
                email = get_claim(alt)
                if email and "@" in email:
                    break

        if not email:
            raise OIDCServiceError(
                "Email claim not found in OIDC response",
                error_code="OIDC_MISSING_EMAIL",
                details={
                    "available_claims": list(id_token_claims.raw_claims.keys()),
                    "userinfo_claims": list(userinfo.keys()) if userinfo else [],
                },
            )

        # Check email verification if required
        email_verified = get_claim(mapping.email_verified_claim, False)

        # Extract names
        first_name = get_claim(mapping.given_name_claim)
        last_name = get_claim(mapping.family_name_claim)
        display_name = get_claim(mapping.name_claim)

        # Build display name if not provided
        if not display_name and (first_name or last_name):
            parts = [p for p in [first_name, last_name] if p]
            display_name = " ".join(parts) if parts else None

        # Extract profile picture
        picture_url = get_claim(mapping.picture_claim)

        # Extract groups
        groups = []
        if mapping.groups_claim:
            groups_value = get_claim(mapping.groups_claim, [])
            if isinstance(groups_value, list):
                groups = groups_value
            elif isinstance(groups_value, str):
                groups = [groups_value]

        # Collect raw attributes
        raw_attributes: Dict[str, Any] = {
            "id_token_claims": id_token_claims.raw_claims,
        }
        if userinfo:
            raw_attributes["userinfo"] = userinfo

        # Process custom claims
        for custom_key, custom_claim in mapping.custom_claims.items():
            raw_attributes[custom_key] = get_claim(custom_claim)

        return SSOUser(
            provider_user_id=id_token_claims.sub,
            email=email.lower().strip(),
            email_verified=bool(email_verified),
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            picture_url=picture_url,
            groups=groups,
            raw_attributes=raw_attributes,
            provider_type=SSOProviderType.OIDC,
        )

    async def fetch_userinfo(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Fetch user information from the UserInfo endpoint.

        Args:
            access_token: OAuth2 access token

        Returns:
            UserInfo claims
        """
        userinfo_endpoint = self.config.provider.userinfo_endpoint
        if not userinfo_endpoint:
            # Try discovery
            discovery = await self.discover_configuration()
            userinfo_endpoint = discovery.get("userinfo_endpoint")

        if not userinfo_endpoint:
            raise OIDCServiceError(
                "UserInfo endpoint not configured",
                error_code="OIDC_NO_USERINFO_ENDPOINT",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            raise OIDCServiceError(
                f"Failed to fetch UserInfo: {e}",
                details={"userinfo_endpoint": userinfo_endpoint, "error": str(e)},
            )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> OIDCTokenResponse:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            New token response
        """
        token_endpoint = self.config.provider.token_endpoint
        if not token_endpoint:
            discovery = await self.discover_configuration()
            token_endpoint = discovery.get("token_endpoint")

        if not token_endpoint:
            raise OIDCServiceError(
                "Token endpoint not configured",
                error_code="OIDC_NO_TOKEN_ENDPOINT",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_endpoint,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.config.client.client_id,
                        "client_secret": self.config.client.client_secret.get_secret_value(),
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                return OIDCTokenResponse(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_in=data.get("expires_in", 3600),
                    refresh_token=data.get("refresh_token"),
                    id_token=data.get("id_token", ""),
                    scope=data.get("scope"),
                )

        except httpx.HTTPError as e:
            raise OIDCServiceError(
                f"Failed to refresh token: {e}",
                details={"error": str(e)},
            )

    def build_authorization_url(
        self,
        state: str,
        nonce: str,
        code_challenge: Optional[str] = None,
        login_hint: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Build the OIDC authorization URL.

        Args:
            state: CSRF protection state parameter
            nonce: Replay protection nonce
            code_challenge: PKCE code challenge (if using PKCE)
            login_hint: Optional login hint (pre-fill email)
            prompt: Optional prompt parameter (login, consent, none)

        Returns:
            Authorization URL
        """
        from urllib.parse import urlencode

        auth_endpoint = self.config.provider.authorization_endpoint
        if not auth_endpoint:
            raise OIDCServiceError(
                "Authorization endpoint not configured",
                error_code="OIDC_NO_AUTH_ENDPOINT",
            )

        params = {
            "client_id": self.config.client.client_id,
            "redirect_uri": self.config.client.redirect_uri,
            "response_type": self.config.client.response_type.value,
            "scope": " ".join(self.config.client.scopes),
            "state": state,
            "nonce": nonce,
        }

        if code_challenge and self.config.use_pkce:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = self.config.pkce_method

        if login_hint:
            params["login_hint"] = login_hint

        if prompt:
            params["prompt"] = prompt

        return f"{auth_endpoint}?{urlencode(params)}"

    def build_logout_url(
        self,
        id_token_hint: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[str]:
        """
        Build the OIDC logout URL.

        Args:
            id_token_hint: ID token to hint logout for specific session
            state: Optional state for logout callback

        Returns:
            Logout URL or None if not configured
        """
        from urllib.parse import urlencode

        logout_endpoint = self.config.provider.end_session_endpoint
        if not logout_endpoint:
            return None

        params = {}

        if self.config.client.post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = self.config.client.post_logout_redirect_uri

        if id_token_hint:
            params["id_token_hint"] = id_token_hint

        if state:
            params["state"] = state

        if params:
            return f"{logout_endpoint}?{urlencode(params)}"
        return logout_endpoint

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for secure storage.

        Args:
            token: Token to hash

        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()


# Singleton instance cache
_oidc_services: Dict[str, OIDCService] = {}


def get_oidc_service(
    config: OIDCConfiguration,
    organization_id: str,
) -> OIDCService:
    """
    Get or create an OIDC service instance for an organization.

    Args:
        config: OIDC configuration
        organization_id: Organization ID

    Returns:
        OIDCService instance
    """
    cache_key = f"{organization_id}:{config.provider.issuer}"
    if cache_key not in _oidc_services:
        _oidc_services[cache_key] = OIDCService(config, organization_id)
    return _oidc_services[cache_key]


def clear_oidc_service_cache(organization_id: Optional[str] = None) -> None:
    """
    Clear OIDC service cache.

    Args:
        organization_id: Optional organization ID to clear.
                        If None, clears all cached services.
    """
    global _oidc_services
    if organization_id:
        _oidc_services = {
            k: v for k, v in _oidc_services.items() if not k.startswith(f"{organization_id}:")
        }
    else:
        _oidc_services = {}
