"""
Tests for SSO identity mapping (SAML attributes and OIDC claims -> SSOUser).

These mappers decide a user's identity (email, name, groups) from IdP-supplied
data, so their fallback and normalization logic is security-critical: a wrong
mapping is an authentication/authorization bug. Pure unit tests (no SAML/OIDC
protocol or external-library involvement).
"""

import os
import sys

import pytest

os.environ.setdefault("DEV_API_KEY", "test-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-unit-tests-only")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.auth.sso.oidc_service import OIDCService, OIDCServiceError
from src.auth.sso.saml_service import SAMLService, SAMLServiceError
from src.types.sso import (
    OIDCClaimMapping,
    OIDCIDToken,
    SAMLAttributeMapping,
    SSOProviderType,
    SSOUser,
)

EMAIL_ATTR = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
FIRST_ATTR = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
LAST_ATTR = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
GROUPS_ATTR = "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"


def _map(attributes, name_id="name-id-123", mapping=None):
    return SAMLService.map_attributes_to_user(
        attributes=attributes,
        name_id=name_id,
        mapping=mapping or SAMLAttributeMapping(),
    )


def test_maps_standard_attributes():
    user = _map(
        {
            EMAIL_ATTR: ["Alice@Example.com"],
            FIRST_ATTR: ["Alice"],
            LAST_ATTR: ["Smith"],
            GROUPS_ATTR: ["admins", "writers"],
        }
    )
    assert isinstance(user, SSOUser)
    assert user.email == "alice@example.com"  # lowercased + stripped
    assert user.email_verified is True  # SAML assertions are trusted
    assert user.first_name == "Alice"
    assert user.last_name == "Smith"
    assert user.display_name == "Alice Smith"  # built from first + last
    assert user.groups == ["admins", "writers"]
    assert user.provider_user_id == "name-id-123"
    assert user.provider_type == SSOProviderType.SAML


def test_email_falls_back_to_common_attribute_names():
    # Mapped email attr absent; should try "email"/"mail"/etc.
    user = _map({"email": ["bob@example.com"], FIRST_ATTR: ["Bob"]})
    assert user.email == "bob@example.com"


def test_email_falls_back_to_name_id_when_email_like():
    user = _map({FIRST_ATTR: ["Carol"]}, name_id="carol@example.com")
    assert user.email == "carol@example.com"


def test_missing_email_everywhere_raises():
    with pytest.raises(SAMLServiceError):
        _map({FIRST_ATTR: ["NoEmail"]}, name_id="not-an-email")


def test_groups_default_empty_when_absent():
    user = _map({EMAIL_ATTR: ["d@example.com"]})
    assert user.groups == []


def test_custom_attributes_captured_in_raw():
    mapping = SAMLAttributeMapping(custom_attributes={"department": "dept"})
    user = _map(
        {EMAIL_ATTR: ["e@example.com"], "dept": ["Engineering"]}, mapping=mapping
    )
    assert user.raw_attributes["department"] == ["Engineering"]
    # original attributes are preserved under _all
    assert "_all" in user.raw_attributes


def test_display_name_uses_only_available_name_part():
    user = _map({EMAIL_ATTR: ["f@example.com"], FIRST_ATTR: ["Frank"]})
    assert user.display_name == "Frank"


# ---------------------------------------------------------------------------
# OIDC claim -> SSOUser mapping (parity with SAML)
# ---------------------------------------------------------------------------


def _id_token(raw_claims, sub="oidc-sub-1"):
    return OIDCIDToken(
        iss="https://idp.example.com",
        sub=sub,
        aud="client-123",
        exp=9999999999,
        iat=1700000000,
        raw_claims=raw_claims,
    )


def _map_oidc(raw_claims, userinfo=None, sub="oidc-sub-1", mapping=None):
    return OIDCService.map_claims_to_user(
        id_token_claims=_id_token(raw_claims, sub=sub),
        userinfo=userinfo,
        claim_mapping=mapping or OIDCClaimMapping(),
    )


def test_oidc_maps_standard_claims():
    user = _map_oidc(
        {
            "email": "Dana@Example.com",
            "given_name": "Dana",
            "family_name": "Lee",
            "email_verified": True,
            "groups": ["eng", "leads"],
        }
    )
    assert isinstance(user, SSOUser)
    assert user.provider_user_id == "oidc-sub-1"
    assert user.email == "dana@example.com"  # lowercased + stripped
    assert user.email_verified is True
    assert user.first_name == "Dana"
    assert user.last_name == "Lee"
    assert user.display_name == "Dana Lee"
    assert user.groups == ["eng", "leads"]
    assert user.provider_type == SSOProviderType.OIDC


def test_oidc_userinfo_takes_precedence_over_id_token():
    user = _map_oidc(
        {"email": "old@example.com"},
        userinfo={"email": "new@example.com"},
    )
    assert user.email == "new@example.com"


def test_oidc_email_falls_back_to_preferred_username():
    user = _map_oidc({"preferred_username": "grace@example.com"})
    assert user.email == "grace@example.com"


def test_oidc_groups_string_is_normalized_to_list():
    user = _map_oidc({"email": "h@example.com", "groups": "solo-group"})
    assert user.groups == ["solo-group"]


def test_oidc_missing_email_raises():
    with pytest.raises(OIDCServiceError):
        _map_oidc({"given_name": "NoEmail"})


def test_oidc_email_verified_defaults_false_when_absent():
    user = _map_oidc({"email": "i@example.com"})
    assert user.email_verified is False
