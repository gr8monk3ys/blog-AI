"""
SSO Provider Abstraction Layer.

This module provides abstract base classes and concrete implementations
for SSO providers (SAML and OIDC).

Security Considerations:
- All provider implementations must validate signatures
- Replay protection must be implemented
- Session state must be cryptographically secure
- All IdP communications must use TLS 1.2+
"""

import hashlib
import logging
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from src.types.sso import (
    OIDCConfiguration,
    SAMLConfiguration,
    SSOConfiguration,
    SSOProviderType,
    SSOSession,
    SSOUser,
)

logger = logging.getLogger(__name__)


class SSOProviderError(Exception):
    """Base exception for SSO provider errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SSO_ERROR"
        self.details = details or {}


class SSOAuthenticationError(SSOProviderError):
    """Authentication failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SSO_AUTH_ERROR", details)


class SSOConfigurationError(SSOProviderError):
    """Configuration is invalid or incomplete."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SSO_CONFIG_ERROR", details)


class SSOValidationError(SSOProviderError):
    """Validation of assertion/token failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SSO_VALIDATION_ERROR", details)


class SSOReplayError(SSOProviderError):
    """Replay attack detected."""

    def __init__(self, message: str = "Potential replay attack detected"):
        super().__init__(message, "SSO_REPLAY_ERROR")


class SSOProvider(ABC):
    """
    Abstract base class for SSO providers.

    All SSO providers must implement these methods to ensure
    consistent behavior across different protocols.
    """

    def __init__(self, organization_id: str, config: SSOConfiguration):
        """
        Initialize the SSO provider.

        Args:
            organization_id: The organization this provider is for
            config: The SSO configuration
        """
        self.organization_id = organization_id
        self.config = config
        self._used_ids: Dict[str, datetime] = {}  # For replay protection
        self._id_expiry = timedelta(hours=24)

    @property
    @abstractmethod
    def provider_type(self) -> SSOProviderType:
        """Get the provider type."""
        pass

    @abstractmethod
    async def initiate_authentication(
        self,
        relay_state: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Initiate the SSO authentication flow.

        Args:
            relay_state: Optional state to pass through the authentication flow
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (redirect_url, session_data)
            - redirect_url: URL to redirect the user to
            - session_data: Data to store in session for callback validation
        """
        pass

    @abstractmethod
    async def handle_callback(
        self,
        callback_data: Dict[str, Any],
        session_data: Dict[str, Any],
    ) -> SSOUser:
        """
        Handle the SSO callback after IdP authentication.

        Args:
            callback_data: Data received from IdP callback
            session_data: Session data stored during initiate_authentication

        Returns:
            Authenticated user information

        Raises:
            SSOAuthenticationError: If authentication fails
            SSOValidationError: If assertion/token validation fails
            SSOReplayError: If replay attack is detected
        """
        pass

    @abstractmethod
    async def initiate_logout(
        self,
        session: SSOSession,
        **kwargs,
    ) -> Optional[str]:
        """
        Initiate SSO logout (Single Logout).

        Args:
            session: The SSO session to terminate
            **kwargs: Additional provider-specific parameters

        Returns:
            Redirect URL for IdP logout, or None if not supported
        """
        pass

    @abstractmethod
    async def handle_logout_callback(
        self,
        callback_data: Dict[str, Any],
    ) -> bool:
        """
        Handle the logout callback from IdP.

        Args:
            callback_data: Data received from IdP logout callback

        Returns:
            True if logout was successful
        """
        pass

    @abstractmethod
    async def validate_configuration(self) -> Tuple[bool, list[str], list[str]]:
        """
        Validate the SSO configuration.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        pass

    def _check_replay(self, assertion_id: str) -> None:
        """
        Check for replay attacks using assertion/token ID.

        Args:
            assertion_id: The unique ID of the assertion/token

        Raises:
            SSOReplayError: If this ID has been seen before
        """
        # Clean up expired IDs
        now = datetime.now(timezone.utc)
        self._used_ids = {
            id_: ts
            for id_, ts in self._used_ids.items()
            if now - ts < self._id_expiry
        }

        # Check if ID has been used
        if assertion_id in self._used_ids:
            logger.warning(
                f"Replay attack detected: assertion ID {assertion_id[:20]}... "
                f"already used at {self._used_ids[assertion_id]}"
            )
            raise SSOReplayError()

        # Record this ID
        self._used_ids[assertion_id] = now

    def _generate_secure_id(self, prefix: str = "") -> str:
        """Generate a cryptographically secure ID."""
        return f"{prefix}{secrets.token_urlsafe(32)}"

    def _hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()


class SAMLProvider(SSOProvider):
    """
    SAML 2.0 SSO Provider.

    Implements SAML authentication using the python3-saml library.
    """

    def __init__(self, organization_id: str, config: SSOConfiguration):
        super().__init__(organization_id, config)
        if not config.saml_config:
            raise SSOConfigurationError("SAML configuration is required")
        self.saml_config: SAMLConfiguration = config.saml_config
        self._saml_auth = None

    @property
    def provider_type(self) -> SSOProviderType:
        return SSOProviderType.SAML

    def _get_saml_settings(self) -> Dict[str, Any]:
        """
        Build OneLogin SAML settings dictionary.

        Returns:
            Settings dict for OneLogin_Saml2_Auth
        """
        from src.auth.sso.saml_service import SAMLService

        return SAMLService.build_saml_settings(
            self.saml_config,
            self.organization_id,
        )

    async def initiate_authentication(
        self,
        relay_state: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Initiate SAML authentication.

        Creates an AuthnRequest and returns the redirect URL to the IdP.
        """
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        # Build request info for python3-saml
        request_data = kwargs.get("request_data", {})

        settings = self._get_saml_settings()
        auth = OneLogin_Saml2_Auth(request_data, settings)

        # Generate AuthnRequest
        redirect_url = auth.login(return_to=relay_state)

        # Store request ID for replay protection
        request_id = auth.get_last_request_id()

        session_data = {
            "request_id": request_id,
            "relay_state": relay_state,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"SAML auth initiated for org {self.organization_id}, "
            f"request_id: {request_id[:20]}..."
        )

        return redirect_url, session_data

    async def handle_callback(
        self,
        callback_data: Dict[str, Any],
        session_data: Dict[str, Any],
    ) -> SSOUser:
        """
        Handle SAML callback (Assertion Consumer Service).

        Validates the SAML Response and extracts user information.
        """
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        from src.auth.sso.saml_service import SAMLService

        # Build request info
        request_data = callback_data.get("request_data", {})

        settings = self._get_saml_settings()
        auth = OneLogin_Saml2_Auth(request_data, settings)

        # Process the SAML Response
        auth.process_response()

        # Check for errors
        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason()
            logger.error(
                f"SAML authentication failed for org {self.organization_id}: "
                f"{errors}, reason: {error_reason}"
            )
            raise SSOAuthenticationError(
                f"SAML authentication failed: {error_reason or errors}",
                details={"errors": errors, "reason": error_reason},
            )

        # Validate authentication
        if not auth.is_authenticated():
            logger.error(
                f"SAML authentication not confirmed for org {self.organization_id}"
            )
            raise SSOAuthenticationError("SAML authentication not confirmed")

        # Check InResponseTo for request ID validation
        response_in_response_to = auth.get_last_response_in_response_to()
        if session_data.get("request_id"):
            if response_in_response_to != session_data["request_id"]:
                logger.warning(
                    f"SAML InResponseTo mismatch for org {self.organization_id}: "
                    f"expected {session_data['request_id'][:20]}..., "
                    f"got {response_in_response_to[:20] if response_in_response_to else 'None'}..."
                )
                raise SSOValidationError("SAML response InResponseTo mismatch")

        # Check for replay
        assertion_id = auth.get_last_assertion_id()
        if assertion_id:
            self._check_replay(assertion_id)

        # Extract user attributes
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        session_index = auth.get_session_index()

        # Map attributes to user
        user = SAMLService.map_attributes_to_user(
            attributes=attributes,
            name_id=name_id,
            mapping=self.saml_config.attribute_mapping,
        )

        logger.info(
            f"SAML authentication successful for org {self.organization_id}, "
            f"user: {user.email}"
        )

        return user

    async def initiate_logout(
        self,
        session: SSOSession,
        **kwargs,
    ) -> Optional[str]:
        """
        Initiate SAML Single Logout.

        Creates a LogoutRequest and returns the redirect URL to the IdP.
        """
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        if not self.saml_config.idp.slo_url:
            logger.info(
                f"SLO not configured for org {self.organization_id}, "
                "performing local logout only"
            )
            return None

        request_data = kwargs.get("request_data", {})
        settings = self._get_saml_settings()
        auth = OneLogin_Saml2_Auth(request_data, settings)

        # Create logout request
        redirect_url = auth.logout(
            name_id=session.saml_name_id,
            session_index=session.saml_session_index,
            nq=session.saml_name_id_format,
        )

        logger.info(
            f"SAML logout initiated for org {self.organization_id}, "
            f"user: {session.sso_user.email}"
        )

        return redirect_url

    async def handle_logout_callback(
        self,
        callback_data: Dict[str, Any],
    ) -> bool:
        """
        Handle SAML logout callback.

        Processes the LogoutResponse from the IdP.
        """
        from onelogin.saml2.auth import OneLogin_Saml2_Auth

        request_data = callback_data.get("request_data", {})
        settings = self._get_saml_settings()
        auth = OneLogin_Saml2_Auth(request_data, settings)

        # Process logout response
        url = auth.process_slo()

        errors = auth.get_errors()
        if errors:
            logger.error(
                f"SAML logout failed for org {self.organization_id}: {errors}"
            )
            return False

        logger.info(f"SAML logout successful for org {self.organization_id}")
        return True

    async def validate_configuration(self) -> Tuple[bool, list[str], list[str]]:
        """Validate SAML configuration."""
        errors = []
        warnings = []

        # Validate IdP configuration
        if not self.saml_config.idp.entity_id:
            errors.append("IdP Entity ID is required")
        if not self.saml_config.idp.sso_url:
            errors.append("IdP SSO URL is required")
        if not self.saml_config.idp.certificate:
            errors.append("IdP certificate is required")

        # Check certificate expiry
        if self.saml_config.idp.certificate_expiry:
            days_until_expiry = (
                self.saml_config.idp.certificate_expiry - datetime.now(timezone.utc)
            ).days
            if days_until_expiry < 0:
                errors.append(
                    f"IdP certificate expired {abs(days_until_expiry)} days ago"
                )
            elif days_until_expiry < 30:
                warnings.append(
                    f"IdP certificate expires in {days_until_expiry} days"
                )

        # Validate SP configuration
        if not self.saml_config.sp.entity_id:
            errors.append("SP Entity ID is required")
        if not self.saml_config.sp.acs_url:
            errors.append("SP ACS URL is required")

        # Check SLO configuration
        if not self.saml_config.idp.slo_url:
            warnings.append("Single Logout is not configured")

        return len(errors) == 0, errors, warnings


class OIDCProvider(SSOProvider):
    """
    OpenID Connect SSO Provider.

    Implements OIDC authentication using the authlib library.
    """

    def __init__(self, organization_id: str, config: SSOConfiguration):
        super().__init__(organization_id, config)
        if not config.oidc_config:
            raise SSOConfigurationError("OIDC configuration is required")
        self.oidc_config: OIDCConfiguration = config.oidc_config
        self._oauth_client = None
        self._jwks = None
        self._jwks_last_updated: Optional[datetime] = None

    @property
    def provider_type(self) -> SSOProviderType:
        return SSOProviderType.OIDC

    async def _get_oauth_client(self):
        """Get or create the OAuth client."""
        if self._oauth_client is None:
            from authlib.integrations.httpx_client import AsyncOAuth2Client

            self._oauth_client = AsyncOAuth2Client(
                client_id=self.oidc_config.client.client_id,
                client_secret=self.oidc_config.client.client_secret.get_secret_value(),
                redirect_uri=self.oidc_config.client.redirect_uri,
                scope=" ".join(self.oidc_config.client.scopes),
            )

        return self._oauth_client

    async def _discover_endpoints(self) -> None:
        """Discover OIDC endpoints from the discovery URL."""
        import httpx

        if self.oidc_config.provider.discovery_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.oidc_config.provider.discovery_url,
                    timeout=10.0,
                )
                response.raise_for_status()
                config = response.json()

                # Update provider config with discovered endpoints
                if not self.oidc_config.provider.authorization_endpoint:
                    self.oidc_config.provider.authorization_endpoint = config.get(
                        "authorization_endpoint"
                    )
                if not self.oidc_config.provider.token_endpoint:
                    self.oidc_config.provider.token_endpoint = config.get(
                        "token_endpoint"
                    )
                if not self.oidc_config.provider.userinfo_endpoint:
                    self.oidc_config.provider.userinfo_endpoint = config.get(
                        "userinfo_endpoint"
                    )
                if not self.oidc_config.provider.jwks_uri:
                    self.oidc_config.provider.jwks_uri = config.get("jwks_uri")
                if not self.oidc_config.provider.end_session_endpoint:
                    self.oidc_config.provider.end_session_endpoint = config.get(
                        "end_session_endpoint"
                    )

    async def initiate_authentication(
        self,
        relay_state: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Initiate OIDC authentication.

        Creates an authorization URL and returns session data.
        """
        await self._discover_endpoints()

        client = await self._get_oauth_client()

        # Generate state and nonce
        state = self._generate_secure_id("state_")
        nonce = self._generate_secure_id("nonce_")

        # Generate PKCE values if enabled
        code_verifier = None
        code_challenge = None
        if self.oidc_config.use_pkce:
            code_verifier = secrets.token_urlsafe(64)
            # Create code challenge using S256
            code_challenge = (
                hashlib.sha256(code_verifier.encode())
                .digest()
            )
            import base64
            code_challenge = (
                base64.urlsafe_b64encode(code_challenge)
                .decode()
                .rstrip("=")
            )

        # Build authorization URL
        auth_params = {
            "state": state,
            "nonce": nonce,
            "response_type": self.oidc_config.client.response_type.value,
        }

        if code_challenge:
            auth_params["code_challenge"] = code_challenge
            auth_params["code_challenge_method"] = self.oidc_config.pkce_method

        redirect_url, _ = client.create_authorization_url(
            self.oidc_config.provider.authorization_endpoint,
            **auth_params,
        )

        session_data = {
            "state": state,
            "nonce": nonce,
            "code_verifier": code_verifier,
            "relay_state": relay_state,
            "initiated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"OIDC auth initiated for org {self.organization_id}, "
            f"state: {state[:20]}..."
        )

        return redirect_url, session_data

    async def handle_callback(
        self,
        callback_data: Dict[str, Any],
        session_data: Dict[str, Any],
    ) -> SSOUser:
        """
        Handle OIDC callback.

        Exchanges authorization code for tokens and validates ID token.
        """
        from src.auth.sso.oidc_service import OIDCService

        await self._discover_endpoints()

        # Validate state
        received_state = callback_data.get("state")
        if received_state != session_data.get("state"):
            logger.warning(
                f"OIDC state mismatch for org {self.organization_id}: "
                f"expected {session_data.get('state', '')[:20]}..., "
                f"got {received_state[:20] if received_state else 'None'}..."
            )
            raise SSOValidationError("OIDC state mismatch - possible CSRF attack")

        # Check for error response
        if "error" in callback_data:
            error = callback_data.get("error")
            error_description = callback_data.get("error_description", "")
            logger.error(
                f"OIDC error for org {self.organization_id}: "
                f"{error} - {error_description}"
            )
            raise SSOAuthenticationError(
                f"OIDC authentication failed: {error}",
                details={
                    "error": error,
                    "error_description": error_description,
                },
            )

        # Exchange code for tokens
        code = callback_data.get("code")
        if not code:
            raise SSOAuthenticationError("No authorization code received")

        client = await self._get_oauth_client()

        token_params = {}
        if session_data.get("code_verifier"):
            token_params["code_verifier"] = session_data["code_verifier"]

        token_response = await client.fetch_token(
            self.oidc_config.provider.token_endpoint,
            code=code,
            **token_params,
        )

        # Validate ID token
        id_token = token_response.get("id_token")
        if not id_token:
            raise SSOAuthenticationError("No ID token in response")

        # Parse and validate ID token
        id_token_claims = await OIDCService.validate_id_token(
            id_token=id_token,
            oidc_config=self.oidc_config,
            nonce=session_data.get("nonce"),
            jwks_uri=self.oidc_config.provider.jwks_uri,
        )

        # Check for replay using token's jti claim if present
        jti = id_token_claims.raw_claims.get("jti")
        if jti:
            self._check_replay(jti)

        # Get additional user info if available
        userinfo = None
        if self.oidc_config.provider.userinfo_endpoint:
            try:
                userinfo = await client.get(
                    self.oidc_config.provider.userinfo_endpoint,
                    token=token_response,
                )
                userinfo = userinfo.json()
            except Exception as e:
                logger.warning(
                    f"Failed to fetch userinfo for org {self.organization_id}: {e}"
                )

        # Map claims to user
        user = OIDCService.map_claims_to_user(
            id_token_claims=id_token_claims,
            userinfo=userinfo,
            claim_mapping=self.oidc_config.claim_mapping,
        )

        logger.info(
            f"OIDC authentication successful for org {self.organization_id}, "
            f"user: {user.email}"
        )

        return user

    async def initiate_logout(
        self,
        session: SSOSession,
        **kwargs,
    ) -> Optional[str]:
        """
        Initiate OIDC logout.

        Redirects to the end_session_endpoint if configured.
        """
        await self._discover_endpoints()

        if not self.oidc_config.provider.end_session_endpoint:
            logger.info(
                f"OIDC logout endpoint not configured for org {self.organization_id}, "
                "performing local logout only"
            )
            return None

        # Build logout URL
        logout_url = self.oidc_config.provider.end_session_endpoint

        params = {}
        if self.oidc_config.client.post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = (
                self.oidc_config.client.post_logout_redirect_uri
            )

        if params:
            from urllib.parse import urlencode
            logout_url = f"{logout_url}?{urlencode(params)}"

        logger.info(
            f"OIDC logout initiated for org {self.organization_id}, "
            f"user: {session.sso_user.email}"
        )

        return logout_url

    async def handle_logout_callback(
        self,
        callback_data: Dict[str, Any],
    ) -> bool:
        """
        Handle OIDC logout callback.

        OIDC typically doesn't have a logout callback, so this is mostly a no-op.
        """
        logger.info(f"OIDC logout callback for org {self.organization_id}")
        return True

    async def validate_configuration(self) -> Tuple[bool, list[str], list[str]]:
        """Validate OIDC configuration."""
        errors = []
        warnings = []

        # Validate provider configuration
        if not self.oidc_config.provider.issuer:
            errors.append("OIDC Issuer is required")

        if (
            not self.oidc_config.provider.discovery_url
            and not self.oidc_config.provider.authorization_endpoint
        ):
            errors.append(
                "Either discovery_url or authorization_endpoint is required"
            )

        # Validate client configuration
        if not self.oidc_config.client.client_id:
            errors.append("Client ID is required")
        if not self.oidc_config.client.client_secret:
            errors.append("Client Secret is required")
        if not self.oidc_config.client.redirect_uri:
            errors.append("Redirect URI is required")

        # Check if endpoints can be discovered
        if self.oidc_config.provider.discovery_url:
            try:
                await self._discover_endpoints()
            except Exception as e:
                errors.append(f"Failed to discover OIDC endpoints: {e}")

        # Check logout configuration
        if not self.oidc_config.provider.end_session_endpoint:
            warnings.append("OIDC logout endpoint is not configured")

        return len(errors) == 0, errors, warnings


class SSOProviderFactory:
    """
    Factory for creating SSO provider instances.

    Manages provider registration and instantiation.
    """

    _providers: Dict[SSOProviderType, type] = {
        SSOProviderType.SAML: SAMLProvider,
        SSOProviderType.OIDC: OIDCProvider,
    }

    @classmethod
    def register_provider(
        cls,
        provider_type: SSOProviderType,
        provider_class: type,
    ) -> None:
        """
        Register a new provider type.

        Args:
            provider_type: The provider type to register
            provider_class: The provider class (must extend SSOProvider)
        """
        if not issubclass(provider_class, SSOProvider):
            raise ValueError("Provider class must extend SSOProvider")
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered SSO provider: {provider_type.value}")

    @classmethod
    def create_provider(
        cls,
        organization_id: str,
        config: SSOConfiguration,
    ) -> SSOProvider:
        """
        Create an SSO provider instance.

        Args:
            organization_id: The organization ID
            config: The SSO configuration

        Returns:
            An initialized SSO provider instance

        Raises:
            SSOConfigurationError: If provider type is not supported
        """
        provider_class = cls._providers.get(config.provider_type)
        if not provider_class:
            raise SSOConfigurationError(
                f"Unsupported SSO provider type: {config.provider_type}",
                details={"supported_types": list(cls._providers.keys())},
            )

        return provider_class(organization_id, config)

    @classmethod
    def get_supported_types(cls) -> list[SSOProviderType]:
        """Get list of supported provider types."""
        return list(cls._providers.keys())


# Singleton instance
_provider_factory: Optional[SSOProviderFactory] = None


def get_provider_factory() -> SSOProviderFactory:
    """Get the SSO provider factory singleton."""
    global _provider_factory
    if _provider_factory is None:
        _provider_factory = SSOProviderFactory()
    return _provider_factory
