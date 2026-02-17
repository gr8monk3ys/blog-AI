"""
Tests for SSO (Single Sign-On) routes.

Comprehensive tests covering:
- SAML login initiation and callback
- OIDC authorization and callback
- Session management (creation, validation, expiry)
- Security: relay state validation, replay attack prevention
- Metadata endpoint
- Error handling for unconfigured/disabled SSO
- Cookie attributes on session creation
- SSO status endpoint
- Logout flow
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create test client."""
    from server import app
    return TestClient(app)


@pytest.fixture
def mock_sso_user():
    """Create a mock SSOUser instance."""
    from src.types.sso import SSOProviderType, SSOUser
    return SSOUser(
        provider_user_id="idp-user-001",
        email="alice@example.com",
        email_verified=True,
        first_name="Alice",
        last_name="Smith",
        display_name="Alice Smith",
        groups=["engineering"],
        raw_attributes={},
        provider_type=SSOProviderType.SAML,
    )


@pytest.fixture
def mock_sso_config_saml():
    """Create a mock SAML SSOConfiguration."""
    from src.types.sso import (
        SSOConfiguration,
        SSOConnectionStatus,
        SSOProviderType,
    )
    saml_config = MagicMock()
    saml_config.idp = MagicMock()
    saml_config.idp.certificate_expiry = None
    saml_config.idp.slo_url = None

    return SSOConfiguration.model_construct(
        id="sso-config-001",
        organization_id="org-001",
        provider_type=SSOProviderType.SAML,
        enabled=True,
        enforce_sso=False,
        status=SSOConnectionStatus.ACTIVE,
        saml_config=saml_config,
        oidc_config=None,
        allowed_email_domains=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by="test-user",
    )


@pytest.fixture
def mock_sso_config_oidc():
    """Create a mock OIDC SSOConfiguration."""
    from src.types.sso import (
        SSOConfiguration,
        SSOConnectionStatus,
        SSOProviderType,
    )
    oidc_config = MagicMock()
    oidc_config.require_email_verified = False

    return SSOConfiguration.model_construct(
        id="sso-config-002",
        organization_id="org-002",
        provider_type=SSOProviderType.OIDC,
        enabled=True,
        enforce_sso=False,
        status=SSOConnectionStatus.ACTIVE,
        saml_config=None,
        oidc_config=oidc_config,
        allowed_email_domains=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by="test-user",
    )


@pytest.fixture
def mock_sso_config_disabled():
    """Create a disabled SSO configuration."""
    from src.types.sso import (
        SSOConfiguration,
        SSOConnectionStatus,
        SSOProviderType,
    )
    saml_config = MagicMock()

    return SSOConfiguration.model_construct(
        id="sso-config-003",
        organization_id="org-003",
        provider_type=SSOProviderType.SAML,
        enabled=False,
        enforce_sso=False,
        status=SSOConnectionStatus.INACTIVE,
        saml_config=saml_config,
        oidc_config=None,
        allowed_email_domains=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by="test-user",
    )


# =============================================================================
# SAML Metadata Endpoint
# =============================================================================


class TestSAMLMetadata:
    """Tests for SAML SP metadata endpoint."""

    def test_saml_metadata_returns_xml_when_configured(
        self, client, mock_sso_config_saml
    ):
        """SAML metadata endpoint returns valid XML with correct content type."""
        mock_saml_service = MagicMock()
        mock_saml_service.generate_sp_metadata.return_value = (
            '<?xml version="1.0"?><md:EntityDescriptor/>'
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLService", return_value=mock_saml_service
        ):
            response = client.get("/sso/saml/metadata/org-001")

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "EntityDescriptor" in response.text

    def test_saml_metadata_returns_template_when_not_configured(self, client):
        """SAML metadata returns a template XML when no SSO config exists."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get("/sso/saml/metadata/org-unknown")

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "EntityDescriptor" in response.text
        assert "SPSSODescriptor" in response.text

    def test_saml_metadata_content_disposition_header(self, client):
        """Metadata response includes Content-Disposition attachment header."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get("/sso/saml/metadata/org-test")

        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert "org-test" in response.headers["Content-Disposition"]


# =============================================================================
# SAML Login Initiation
# =============================================================================


class TestSAMLLogin:
    """Tests for SAML login initiation endpoint."""

    def test_saml_login_returns_redirect(self, client, mock_sso_config_saml):
        """SAML login initiates redirect to the IdP."""
        mock_provider = MagicMock()
        mock_provider.initiate_authentication = AsyncMock(
            return_value=(
                "https://idp.example.com/sso?SAMLRequest=encoded",
                {"request_id": "req-001"},
            )
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.get(
                "/sso/saml/login/org-001", follow_redirects=False
            )

        assert response.status_code == 302
        assert "idp.example.com" in response.headers["location"]

    def test_saml_login_sets_auth_session_cookie(
        self, client, mock_sso_config_saml
    ):
        """SAML login sets an httpOnly auth session cookie."""
        mock_provider = MagicMock()
        mock_provider.initiate_authentication = AsyncMock(
            return_value=("https://idp.example.com/sso", {"request_id": "req-002"})
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.get(
                "/sso/saml/login/org-001", follow_redirects=False
            )

        cookie_header = response.headers.get("set-cookie", "")
        assert "sso_auth_session" in cookie_header
        assert "httponly" in cookie_header.lower()
        assert "secure" in cookie_header.lower()

    def test_saml_login_not_configured_returns_404(self, client):
        """SAML login returns 404 when SSO is not configured for org."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get("/sso/saml/login/org-missing")

        assert response.status_code == 404
        assert "SSO_NOT_CONFIGURED" in str(response.json().get("detail", ""))

    def test_saml_login_disabled_returns_403(
        self, client, mock_sso_config_disabled
    ):
        """SAML login returns 403 when SSO is disabled for org."""
        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_disabled
        ):
            response = client.get("/sso/saml/login/org-003")

        assert response.status_code == 403
        assert "SSO_DISABLED" in str(response.json().get("detail", ""))

    def test_saml_login_configuration_error_returns_500(
        self, client, mock_sso_config_saml
    ):
        """SAML login returns 500 on configuration error."""
        from src.auth.sso.providers import SSOConfigurationError

        mock_provider = MagicMock()
        mock_provider.initiate_authentication = AsyncMock(
            side_effect=SSOConfigurationError("Missing IdP certificate")
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.get("/sso/saml/login/org-001")

        assert response.status_code == 500
        assert "SSO_CONFIG_ERROR" in str(response.json().get("detail", ""))


# =============================================================================
# SAML ACS (Assertion Consumer Service) Callback
# =============================================================================


class TestSAMLACS:
    """Tests for SAML ACS callback endpoint."""

    def test_saml_acs_missing_response_returns_400(
        self, client, mock_sso_config_saml
    ):
        """ACS callback without SAMLResponse returns 400."""
        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ):
            response = client.post(
                "/sso/saml/acs/org-001", data={}
            )

        assert response.status_code == 400
        assert "SAML_MISSING_RESPONSE" in str(response.json().get("detail", ""))

    def test_saml_acs_invalid_signature_returns_400(
        self, client, mock_sso_config_saml
    ):
        """ACS callback with invalid SAML signature returns 400."""
        from src.auth.sso.providers import SSOValidationError

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(
            side_effect=SSOValidationError("Invalid SAML response signature")
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.post(
                "/sso/saml/acs/org-001",
                data={"SAMLResponse": "invalid-base64-data"},
            )

        assert response.status_code == 400
        assert "SSO_VALIDATION_ERROR" in str(response.json().get("detail", ""))

    def test_saml_acs_valid_response_creates_session(
        self, client, mock_sso_config_saml, mock_sso_user
    ):
        """ACS callback with valid SAML response creates user session and redirects."""
        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(return_value=mock_sso_user)

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.post(
                "/sso/saml/acs/org-001",
                data={"SAMLResponse": "valid-encoded-response"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        cookie_header = response.headers.get("set-cookie", "")
        assert "sso_session" in cookie_header

    def test_saml_acs_replay_attack_returns_400(
        self, client, mock_sso_config_saml
    ):
        """ACS callback rejects replay attacks with 400."""
        from src.auth.sso.providers import SSOReplayError

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(
            side_effect=SSOReplayError("Potential replay attack detected")
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.post(
                "/sso/saml/acs/org-001",
                data={"SAMLResponse": "replayed-response"},
            )

        assert response.status_code == 400
        assert "SSO_REPLAY_ERROR" in str(response.json().get("detail", ""))

    def test_saml_acs_auth_failure_returns_401(
        self, client, mock_sso_config_saml
    ):
        """ACS callback returns 401 on authentication failure."""
        from src.auth.sso.providers import SSOAuthenticationError

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(
            side_effect=SSOAuthenticationError("Authentication failed")
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.post(
                "/sso/saml/acs/org-001",
                data={"SAMLResponse": "bad-response"},
            )

        assert response.status_code == 401
        assert "SSO_AUTH_ERROR" in str(response.json().get("detail", ""))

    def test_saml_acs_not_configured_returns_404(self, client):
        """ACS callback returns 404 when SSO is not configured."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.post(
                "/sso/saml/acs/org-missing",
                data={"SAMLResponse": "some-response"},
            )

        assert response.status_code == 404

    def test_saml_acs_email_domain_restriction(
        self, client, mock_sso_user
    ):
        """ACS callback rejects users from disallowed email domains."""
        from src.types.sso import (
            SSOConfiguration,
            SSOConnectionStatus,
            SSOProviderType,
        )

        config = SSOConfiguration(
            id="sso-restricted",
            organization_id="org-restricted",
            provider_type=SSOProviderType.SAML,
            enabled=True,
            status=SSOConnectionStatus.ACTIVE,
            saml_config=MagicMock(),
            oidc_config=None,
            allowed_email_domains=["company.com"],
        )

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(return_value=mock_sso_user)

        with patch(
            "app.routes.sso._get_sso_config", return_value=config
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            # mock_sso_user has email alice@example.com, not company.com
            response = client.post(
                "/sso/saml/acs/org-restricted",
                data={"SAMLResponse": "valid-response"},
            )

        assert response.status_code == 403
        assert "SSO_DOMAIN_NOT_ALLOWED" in str(response.json().get("detail", ""))

    def test_saml_acs_session_cookie_attributes(
        self, client, mock_sso_config_saml, mock_sso_user
    ):
        """ACS callback sets session cookie with secure attributes."""
        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(return_value=mock_sso_user)

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ), patch(
            "app.routes.sso.SAMLProvider", return_value=mock_provider
        ):
            response = client.post(
                "/sso/saml/acs/org-001",
                data={"SAMLResponse": "valid-response"},
                follow_redirects=False,
            )

        # Verify session cookie has secure attributes
        set_cookies = response.headers.get_list("set-cookie")
        session_cookie = [c for c in set_cookies if "sso_session=" in c]
        assert len(session_cookie) > 0
        cookie_str = session_cookie[0].lower()
        assert "httponly" in cookie_str
        assert "secure" in cookie_str
        assert "samesite=lax" in cookie_str


# =============================================================================
# OIDC Authorization and Callback
# =============================================================================


class TestOIDCAuthorize:
    """Tests for OIDC authorization initiation endpoint."""

    def test_oidc_authorize_returns_redirect(self, client, mock_sso_config_oidc):
        """OIDC authorization initiates redirect to provider."""
        mock_provider = MagicMock()
        mock_provider.initiate_authentication = AsyncMock(
            return_value=(
                "https://accounts.google.com/o/oauth2/v2/auth?client_id=abc",
                {"state": "random-state", "nonce": "random-nonce"},
            )
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso.OIDCProvider", return_value=mock_provider
        ):
            response = client.get(
                "/sso/oidc/authorize/org-002", follow_redirects=False
            )

        assert response.status_code == 302
        assert "accounts.google.com" in response.headers["location"]

    def test_oidc_authorize_not_configured_returns_404(self, client):
        """OIDC authorize returns 404 when not configured."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get("/sso/oidc/authorize/org-missing")

        assert response.status_code == 404

    def test_oidc_authorize_disabled_returns_403(
        self, client, mock_sso_config_disabled
    ):
        """OIDC authorize returns 403 when SSO is disabled."""
        mock_sso_config_disabled.oidc_config = MagicMock()
        mock_sso_config_disabled.saml_config = None
        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_disabled
        ):
            response = client.get("/sso/oidc/authorize/org-003")

        assert response.status_code == 403

    def test_oidc_authorize_sets_auth_session_cookie(
        self, client, mock_sso_config_oidc
    ):
        """OIDC authorize sets auth session cookie for callback validation."""
        mock_provider = MagicMock()
        mock_provider.initiate_authentication = AsyncMock(
            return_value=("https://provider.example.com/auth", {"state": "s123"})
        )

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso.OIDCProvider", return_value=mock_provider
        ):
            response = client.get(
                "/sso/oidc/authorize/org-002", follow_redirects=False
            )

        cookie_header = response.headers.get("set-cookie", "")
        assert "sso_auth_session" in cookie_header


class TestOIDCCallback:
    """Tests for OIDC callback endpoint."""

    def test_oidc_callback_error_param_returns_401(self, client):
        """OIDC callback with error parameter returns 401."""
        response = client.get(
            "/sso/oidc/callback/org-002?error=access_denied"
            "&error_description=User+denied+access"
        )

        assert response.status_code == 401
        assert "OIDC_ACCESS_DENIED" in str(response.json().get("detail", ""))

    def test_oidc_callback_invalid_state_returns_400(
        self, client, mock_sso_config_oidc
    ):
        """OIDC callback with expired/missing session returns 400."""
        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso._get_auth_session", return_value=None
        ):
            response = client.get(
                "/sso/oidc/callback/org-002?code=authcode&state=bad-state"
            )

        assert response.status_code == 400
        assert "OIDC_SESSION_EXPIRED" in str(response.json().get("detail", ""))

    def test_oidc_callback_valid_creates_session(
        self, client, mock_sso_config_oidc, mock_sso_user
    ):
        """OIDC callback with valid code creates user session."""
        from src.types.sso import SSOProviderType
        mock_sso_user.provider_type = SSOProviderType.OIDC

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(return_value=mock_sso_user)

        session_data = {
            "state": "valid-state",
            "nonce": "valid-nonce",
            "organization_id": "org-002",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso.OIDCProvider", return_value=mock_provider
        ), patch(
            "app.routes.sso._get_auth_session", return_value=session_data
        ), patch(
            "app.routes.sso._delete_auth_session"
        ):
            response = client.get(
                "/sso/oidc/callback/org-002?code=valid-code&state=valid-state",
                cookies={"sso_auth_session": "test-session-id"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        cookie_header = response.headers.get("set-cookie", "")
        assert "sso_session" in cookie_header

    def test_oidc_callback_replay_attack_returns_400(
        self, client, mock_sso_config_oidc
    ):
        """OIDC callback rejects replay attacks."""
        from src.auth.sso.providers import SSOReplayError

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(
            side_effect=SSOReplayError()
        )

        session_data = {
            "state": "s1",
            "organization_id": "org-002",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso.OIDCProvider", return_value=mock_provider
        ), patch(
            "app.routes.sso._get_auth_session", return_value=session_data
        ):
            response = client.get(
                "/sso/oidc/callback/org-002?code=reused-code&state=s1",
                cookies={"sso_auth_session": "session-id"},
            )

        assert response.status_code == 400
        assert "SSO_REPLAY_ERROR" in str(response.json().get("detail", ""))

    def test_oidc_callback_validation_error_returns_400(
        self, client, mock_sso_config_oidc
    ):
        """OIDC callback with validation error returns 400."""
        from src.auth.sso.providers import SSOValidationError

        mock_provider = MagicMock()
        mock_provider.handle_callback = AsyncMock(
            side_effect=SSOValidationError("Token signature invalid")
        )

        session_data = {
            "state": "s1",
            "organization_id": "org-002",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_oidc
        ), patch(
            "app.routes.sso.OIDCProvider", return_value=mock_provider
        ), patch(
            "app.routes.sso._get_auth_session", return_value=session_data
        ):
            response = client.get(
                "/sso/oidc/callback/org-002?code=bad-code&state=s1",
                cookies={"sso_auth_session": "session-id"},
            )

        assert response.status_code == 400


# =============================================================================
# Session Management
# =============================================================================


class TestSSOSessionManagement:
    """Tests for SSO session and status endpoints."""

    def test_sso_session_no_cookie_returns_unauthenticated(self, client):
        """Session endpoint returns unauthenticated when no cookie is present."""
        response = client.get("/sso/session")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_sso_session_expired_returns_unauthenticated(self, client):
        """Session endpoint returns unauthenticated for expired sessions."""
        from app.routes.sso import _sso_user_sessions
        from src.types.sso import SSOProviderType, SSOSession, SSOUser

        token = secrets.token_urlsafe(32)
        session_hash = hashlib.sha256(token.encode()).hexdigest()

        sso_user = SSOUser(
            provider_user_id="idp-expired",
            email="expired@example.com",
            email_verified=True,
            groups=[],
            raw_attributes={},
            provider_type=SSOProviderType.SAML,
        )

        _sso_user_sessions[session_hash] = SSOSession(
            id=session_hash,
            organization_id="org-001",
            user_id="expired@example.com",
            sso_user=sso_user,
            provider_type=SSOProviderType.SAML,
            created_at=datetime.now(timezone.utc) - timedelta(hours=10),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
            last_activity_at=datetime.now(timezone.utc) - timedelta(hours=10),
        )

        response = client.get(
            "/sso/session", cookies={"sso_session": token}
        )
        data = response.json()
        assert data["authenticated"] is False

        # Cleanup
        _sso_user_sessions.pop(session_hash, None)

    def test_sso_session_valid_returns_user_info(self, client):
        """Session endpoint returns user info for a valid session."""
        from app.routes.sso import _sso_user_sessions
        from src.types.sso import SSOProviderType, SSOSession, SSOUser

        token = secrets.token_urlsafe(32)
        session_hash = hashlib.sha256(token.encode()).hexdigest()

        sso_user = SSOUser(
            provider_user_id="idp-valid",
            email="valid@example.com",
            email_verified=True,
            display_name="Valid User",
            first_name="Valid",
            last_name="User",
            groups=["admins"],
            raw_attributes={},
            provider_type=SSOProviderType.SAML,
        )

        now = datetime.now(timezone.utc)
        _sso_user_sessions[session_hash] = SSOSession(
            id=session_hash,
            organization_id="org-001",
            user_id="valid@example.com",
            sso_user=sso_user,
            provider_type=SSOProviderType.SAML,
            created_at=now,
            expires_at=now + timedelta(hours=8),
            last_activity_at=now,
        )

        response = client.get(
            "/sso/session", cookies={"sso_session": token}
        )
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == "valid@example.com"
        assert data["user"]["display_name"] == "Valid User"
        assert data["organization_id"] == "org-001"
        assert data["provider_type"] == "saml"

        # Cleanup
        _sso_user_sessions.pop(session_hash, None)


# =============================================================================
# SSO Status
# =============================================================================


class TestSSOStatus:
    """Tests for SSO status endpoint."""

    def test_sso_status_not_configured(self, client):
        """Status returns disabled when no SSO config exists."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get("/sso/status/org-unconfigured")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["active_sessions_count"] == 0

    def test_sso_status_configured(self, client, mock_sso_config_saml):
        """Status returns correct data when SSO is configured."""
        with patch(
            "app.routes.sso._get_sso_config", return_value=mock_sso_config_saml
        ):
            response = client.get("/sso/status/org-001")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["provider_type"] == "saml"


# =============================================================================
# SSO Logout
# =============================================================================


class TestSSOLogout:
    """Tests for SSO logout endpoint."""

    def test_sso_logout_no_session(self, client):
        """Logout with no session returns success."""
        response = client.post("/sso/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "No active session"

    def test_sso_logout_active_session(self, client):
        """Logout with active session removes it."""
        from app.routes.sso import _sso_user_sessions
        from src.types.sso import SSOProviderType, SSOSession, SSOUser

        token = secrets.token_urlsafe(32)
        session_hash = hashlib.sha256(token.encode()).hexdigest()

        sso_user = SSOUser(
            provider_user_id="idp-logout",
            email="logout@example.com",
            email_verified=True,
            groups=[],
            raw_attributes={},
            provider_type=SSOProviderType.SAML,
        )

        now = datetime.now(timezone.utc)
        _sso_user_sessions[session_hash] = SSOSession(
            id=session_hash,
            organization_id="org-001",
            user_id="logout@example.com",
            sso_user=sso_user,
            provider_type=SSOProviderType.SAML,
            created_at=now,
            expires_at=now + timedelta(hours=8),
            last_activity_at=now,
        )

        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.post(
                "/sso/logout", cookies={"sso_session": token}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert session_hash not in _sso_user_sessions


# =============================================================================
# SAML SLO (Single Logout)
# =============================================================================


class TestSAMLSLO:
    """Tests for SAML Single Logout endpoint."""

    def test_saml_slo_no_config_redirects_home(self, client):
        """SLO with no SSO config redirects to home."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get(
                "/sso/saml/slo/org-001", follow_redirects=False
            )

        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_saml_slo_deletes_session_cookie(self, client):
        """SLO deletes the session cookies."""
        with patch("app.routes.sso._get_sso_config", return_value=None):
            response = client.get(
                "/sso/saml/slo/org-001",
                cookies={"sso_session": "some-token"},
                follow_redirects=False,
            )

        assert response.status_code == 302
        set_cookies = response.headers.get_list("set-cookie")
        cookie_names = " ".join(set_cookies)
        assert "sso_session" in cookie_names


# =============================================================================
# Auth Session Timeout
# =============================================================================


class TestAuthSessionTimeout:
    """Tests for authentication session timeout enforcement."""

    def test_auth_session_timeout_enforcement(self):
        """Expired auth sessions are cleaned up on access."""
        from app.routes.sso import (
            _get_auth_session,
            _store_auth_session,
            _sso_auth_sessions,
        )

        session_id = "test-timeout-session"
        _store_auth_session(session_id, {"organization_id": "org-001"})

        # Manually set created_at to the past
        _sso_auth_sessions[session_id]["created_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=15)
        ).isoformat()

        # Should return None for expired session
        result = _get_auth_session(session_id)
        assert result is None
        assert session_id not in _sso_auth_sessions

    def test_auth_session_valid_within_timeout(self):
        """Auth sessions within timeout period are returned normally."""
        from app.routes.sso import (
            _get_auth_session,
            _store_auth_session,
            _sso_auth_sessions,
        )

        session_id = "test-valid-session"
        _store_auth_session(session_id, {"organization_id": "org-001"})

        result = _get_auth_session(session_id)
        assert result is not None
        assert result["organization_id"] == "org-001"

        # Cleanup
        _sso_auth_sessions.pop(session_id, None)
