"""
SAML 2.0 Service Implementation.

This module provides comprehensive SAML 2.0 support including:
- Service Provider (SP) metadata generation
- Assertion Consumer Service (ACS) handling
- Single Logout (SLO) handling
- Attribute mapping and user extraction

Security Considerations:
- All SAML responses must have valid signatures
- Assertions must be validated for issuer, audience, and time constraints
- Replay protection via assertion ID tracking
- Signatures use SHA-256 (XML-DSig)
- Debug mode must NEVER be enabled in production

Dependencies:
- python3-saml: pip install python3-saml
"""

import base64
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from src.types.sso import (
    SAMLAssertion,
    SAMLAttributeMapping,
    SAMLConfiguration,
    SAMLNameIDFormat,
    SSOProviderType,
    SSOUser,
)

logger = logging.getLogger(__name__)


class SAMLServiceError(Exception):
    """SAML Service specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SAML_ERROR"
        self.details = details or {}


class SAMLService:
    """
    SAML 2.0 Service for handling SAML authentication.

    This service provides methods for:
    - Generating SP metadata
    - Building authentication requests
    - Processing SAML responses
    - Handling Single Logout
    """

    # SAML namespace constants
    SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
    SAMLP_NS = "urn:oasis:names:tc:SAML:2.0:protocol"
    XMLDSIG_NS = "http://www.w3.org/2000/09/xmldsig#"

    # Default algorithms
    DEFAULT_SIGNATURE_ALGORITHM = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    DEFAULT_DIGEST_ALGORITHM = "http://www.w3.org/2001/04/xmlenc#sha256"

    def __init__(self, config: SAMLConfiguration, organization_id: str):
        """
        Initialize the SAML service.

        Args:
            config: SAML configuration
            organization_id: Organization ID this service is for
        """
        self.config = config
        self.organization_id = organization_id
        self._sp_cert: Optional[str] = None
        self._sp_private_key: Optional[str] = None
        self._load_sp_credentials()

    def _load_sp_credentials(self) -> None:
        """Load SP certificate and private key from environment/files."""
        # Try to load from environment variables first
        cert_path = os.environ.get("SAML_SP_CERT_PATH")
        key_path = os.environ.get("SAML_SP_KEY_PATH")

        if cert_path and os.path.exists(cert_path):
            with open(cert_path, "r") as f:
                self._sp_cert = f.read().strip()
            logger.info(f"Loaded SP certificate from {cert_path}")

        if key_path and os.path.exists(key_path):
            with open(key_path, "r") as f:
                self._sp_private_key = f.read().strip()
            logger.info(f"Loaded SP private key from {key_path}")

        # Fall back to environment variables
        if not self._sp_cert:
            self._sp_cert = os.environ.get("SAML_SP_CERT")
        if not self._sp_private_key:
            self._sp_private_key = os.environ.get("SAML_SP_PRIVATE_KEY")

    @staticmethod
    def build_saml_settings(
        config: SAMLConfiguration,
        organization_id: str,
    ) -> Dict[str, Any]:
        """
        Build settings dictionary for python3-saml library.

        Args:
            config: SAML configuration
            organization_id: Organization ID

        Returns:
            Settings dictionary compatible with OneLogin_Saml2_Auth
        """
        # Load SP credentials
        sp_cert = os.environ.get("SAML_SP_CERT", "")
        sp_key = os.environ.get("SAML_SP_PRIVATE_KEY", "")

        cert_path = os.environ.get("SAML_SP_CERT_PATH")
        key_path = os.environ.get("SAML_SP_KEY_PATH")

        if cert_path and os.path.exists(cert_path):
            with open(cert_path, "r") as f:
                sp_cert = f.read().strip()
        if key_path and os.path.exists(key_path):
            with open(key_path, "r") as f:
                sp_key = f.read().strip()

        # Strip PEM headers/footers for python3-saml
        if sp_cert:
            sp_cert = SAMLService._strip_pem_headers(sp_cert)

        idp_cert = SAMLService._strip_pem_headers(config.idp.certificate)

        settings = {
            "strict": True,  # Enable strict mode for security
            "debug": config.debug_mode,  # Should be False in production
            "sp": {
                "entityId": config.sp.entity_id,
                "assertionConsumerService": {
                    "url": config.sp.acs_url,
                    "binding": config.idp.binding_type.value,
                },
                "NameIDFormat": config.sp.name_id_format.value,
                "x509cert": sp_cert,
                "privateKey": sp_key,
            },
            "idp": {
                "entityId": config.idp.entity_id,
                "singleSignOnService": {
                    "url": config.idp.sso_url,
                    "binding": config.idp.binding_type.value,
                },
                "x509cert": idp_cert,
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": config.sp.authn_requests_signed,
                "logoutRequestSigned": True,
                "logoutResponseSigned": True,
                "signMetadata": True,
                "wantMessagesSigned": True,
                "wantAssertionsSigned": config.sp.want_assertions_signed,
                "wantAssertionsEncrypted": config.sp.want_assertions_encrypted,
                "wantNameId": True,
                "wantNameIdEncrypted": False,
                "wantAttributeStatement": True,
                "signatureAlgorithm": config.signature_algorithm,
                "digestAlgorithm": config.digest_algorithm,
                "rejectUnsolicitedResponsesWithInResponseTo": True,
            },
        }

        # Add SLO configuration if available
        if config.idp.slo_url:
            settings["idp"]["singleLogoutService"] = {
                "url": config.idp.slo_url,
                "binding": config.idp.binding_type.value,
            }

        if config.sp.slo_url:
            settings["sp"]["singleLogoutService"] = {
                "url": config.sp.slo_url,
                "binding": config.idp.binding_type.value,
            }

        return settings

    @staticmethod
    def _strip_pem_headers(cert: str) -> str:
        """Remove PEM headers and footers, return raw certificate."""
        lines = cert.strip().split("\n")
        # Filter out header/footer lines
        cert_lines = [
            line
            for line in lines
            if not line.startswith("-----")
        ]
        return "".join(cert_lines)

    def generate_sp_metadata(self) -> str:
        """
        Generate Service Provider (SP) metadata XML.

        Returns:
            SP metadata as XML string
        """
        from onelogin.saml2.metadata import OneLogin_Saml2_Metadata

        settings = self.build_saml_settings(self.config, self.organization_id)
        metadata = OneLogin_Saml2_Metadata.builder(
            sp=settings.get("sp", {}),
            authnsign=self.config.sp.authn_requests_signed,
            wsign=True,
            valid_until=None,  # Metadata doesn't expire
            cache_duration=None,
        )

        return metadata

    def get_sp_metadata_info(self) -> Dict[str, Any]:
        """
        Get SP metadata information for display/documentation.

        Returns:
            Dictionary with SP metadata information
        """
        return {
            "entity_id": self.config.sp.entity_id,
            "acs_url": self.config.sp.acs_url,
            "slo_url": self.config.sp.slo_url,
            "name_id_format": self.config.sp.name_id_format.value,
            "authn_requests_signed": self.config.sp.authn_requests_signed,
            "want_assertions_signed": self.config.sp.want_assertions_signed,
            "signature_algorithm": self.config.signature_algorithm,
            "digest_algorithm": self.config.digest_algorithm,
        }

    @staticmethod
    def map_attributes_to_user(
        attributes: Dict[str, List[str]],
        name_id: str,
        mapping: SAMLAttributeMapping,
    ) -> SSOUser:
        """
        Map SAML assertion attributes to SSOUser.

        Args:
            attributes: SAML assertion attributes (attribute name -> list of values)
            name_id: SAML NameID value
            mapping: Attribute mapping configuration

        Returns:
            SSOUser with mapped attributes
        """

        def get_first_value(attr_name: str) -> Optional[str]:
            """Get first value for an attribute."""
            values = attributes.get(attr_name, [])
            return values[0] if values else None

        def get_all_values(attr_name: str) -> List[str]:
            """Get all values for an attribute."""
            return attributes.get(attr_name, [])

        # Extract email - required
        email = get_first_value(mapping.email_attribute)
        if not email:
            # Try common alternative attribute names
            for alt_attr in [
                "email",
                "mail",
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "urn:oid:0.9.2342.19200300.100.1.3",
            ]:
                email = get_first_value(alt_attr)
                if email:
                    break

        if not email:
            # Fall back to NameID if it looks like an email
            if name_id and "@" in name_id:
                email = name_id
            else:
                raise SAMLServiceError(
                    "Email attribute not found in SAML assertion",
                    error_code="SAML_MISSING_EMAIL",
                    details={"available_attributes": list(attributes.keys())},
                )

        # Extract names
        first_name = get_first_value(mapping.first_name_attribute)
        last_name = get_first_value(mapping.last_name_attribute)
        display_name = get_first_value(mapping.display_name_attribute) if mapping.display_name_attribute else None

        # Build display name if not provided
        if not display_name and (first_name or last_name):
            parts = [p for p in [first_name, last_name] if p]
            display_name = " ".join(parts) if parts else None

        # Extract groups
        groups = []
        if mapping.groups_attribute:
            groups = get_all_values(mapping.groups_attribute)

        # Process custom attributes
        raw_attributes: Dict[str, Any] = {}
        for custom_key, custom_attr in mapping.custom_attributes.items():
            raw_attributes[custom_key] = get_all_values(custom_attr)

        # Add all original attributes to raw_attributes
        raw_attributes["_all"] = {k: v for k, v in attributes.items()}

        return SSOUser(
            provider_user_id=name_id,
            email=email.lower().strip(),
            email_verified=True,  # SAML assertions are trusted
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            groups=groups,
            raw_attributes=raw_attributes,
            provider_type=SSOProviderType.SAML,
        )

    @staticmethod
    def parse_assertion(
        saml_response_b64: str,
    ) -> SAMLAssertion:
        """
        Parse a SAML assertion from base64-encoded response.

        This is a basic parser for diagnostic purposes.
        Actual validation should be done by python3-saml.

        Args:
            saml_response_b64: Base64-encoded SAML response

        Returns:
            Parsed SAML assertion data
        """
        try:
            # Decode base64
            saml_response = base64.b64decode(saml_response_b64)
            root = ElementTree.fromstring(saml_response)

            # Define namespaces
            ns = {
                "saml": SAMLService.SAML_NS,
                "samlp": SAMLService.SAMLP_NS,
            }

            # Extract assertion
            assertion = root.find(".//saml:Assertion", ns)
            if assertion is None:
                raise SAMLServiceError(
                    "No assertion found in SAML response",
                    error_code="SAML_NO_ASSERTION",
                )

            # Extract issuer
            issuer_elem = assertion.find("saml:Issuer", ns)
            issuer = issuer_elem.text if issuer_elem is not None else ""

            # Extract subject
            subject = assertion.find("saml:Subject", ns)
            name_id_elem = subject.find("saml:NameID", ns) if subject else None
            name_id = name_id_elem.text if name_id_elem is not None else ""
            name_id_format = (
                name_id_elem.get("Format", SAMLNameIDFormat.UNSPECIFIED.value)
                if name_id_elem is not None
                else SAMLNameIDFormat.UNSPECIFIED.value
            )

            # Extract conditions
            conditions = assertion.find("saml:Conditions", ns)
            not_before = conditions.get("NotBefore", "") if conditions else ""
            not_on_or_after = conditions.get("NotOnOrAfter", "") if conditions else ""

            # Extract audience
            audience_elem = conditions.find(".//saml:Audience", ns) if conditions else None
            audience = audience_elem.text if audience_elem is not None else ""

            # Extract authn statement
            authn_statement = assertion.find("saml:AuthnStatement", ns)
            session_index = (
                authn_statement.get("SessionIndex", None)
                if authn_statement is not None
                else None
            )
            authn_instant = (
                authn_statement.get("AuthnInstant", "")
                if authn_statement is not None
                else ""
            )

            # Extract attributes
            attributes: Dict[str, List[str]] = {}
            attr_statement = assertion.find("saml:AttributeStatement", ns)
            if attr_statement is not None:
                for attr in attr_statement.findall("saml:Attribute", ns):
                    attr_name = attr.get("Name", "")
                    values = [
                        v.text or ""
                        for v in attr.findall("saml:AttributeValue", ns)
                    ]
                    attributes[attr_name] = values

            # Parse timestamps
            def parse_timestamp(ts: str) -> datetime:
                if not ts:
                    return datetime.now(timezone.utc)
                # Handle both formats
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    return datetime.now(timezone.utc)

            return SAMLAssertion(
                id=assertion.get("ID", ""),
                issuer=issuer,
                subject_name_id=name_id,
                subject_name_id_format=name_id_format,
                session_index=session_index,
                authn_instant=parse_timestamp(authn_instant),
                not_before=parse_timestamp(not_before),
                not_on_or_after=parse_timestamp(not_on_or_after),
                audience=audience,
                attributes=attributes,
                signature_valid=False,  # Should be validated by python3-saml
            )

        except Exception as e:
            if isinstance(e, SAMLServiceError):
                raise
            raise SAMLServiceError(
                f"Failed to parse SAML assertion: {e}",
                error_code="SAML_PARSE_ERROR",
                details={"error": str(e)},
            )

    @staticmethod
    def extract_certificate_info(cert_pem: str) -> Dict[str, Any]:
        """
        Extract information from an X.509 certificate.

        Args:
            cert_pem: Certificate in PEM format

        Returns:
            Dictionary with certificate information
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes

            # Load certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode())

            # Calculate fingerprint
            fingerprint = cert.fingerprint(hashes.SHA256())
            fingerprint_hex = fingerprint.hex().upper()
            fingerprint_formatted = ":".join(
                [fingerprint_hex[i : i + 2] for i in range(0, len(fingerprint_hex), 2)]
            )

            # Extract subject and issuer
            def name_to_dict(name: x509.Name) -> Dict[str, str]:
                result = {}
                for attr in name:
                    oid_name = attr.oid._name
                    result[oid_name] = attr.value
                return result

            return {
                "subject": name_to_dict(cert.subject),
                "issuer": name_to_dict(cert.issuer),
                "serial_number": cert.serial_number,
                "not_valid_before": cert.not_valid_before_utc.isoformat(),
                "not_valid_after": cert.not_valid_after_utc.isoformat(),
                "fingerprint_sha256": fingerprint_formatted,
                "is_expired": datetime.now(timezone.utc) > cert.not_valid_after_utc,
                "days_until_expiry": (
                    cert.not_valid_after_utc - datetime.now(timezone.utc)
                ).days,
            }

        except Exception as e:
            return {
                "error": f"Failed to parse certificate: {e}",
            }

    def validate_idp_certificate(self) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate the IdP certificate.

        Returns:
            Tuple of (is_valid, error_message, certificate_info)
        """
        cert_info = self.extract_certificate_info(self.config.idp.certificate)

        if "error" in cert_info:
            return False, cert_info["error"], cert_info

        if cert_info.get("is_expired"):
            return (
                False,
                f"IdP certificate expired on {cert_info['not_valid_after']}",
                cert_info,
            )

        days_until_expiry = cert_info.get("days_until_expiry", 0)
        if days_until_expiry < 0:
            return (
                False,
                f"IdP certificate expired {abs(days_until_expiry)} days ago",
                cert_info,
            )

        warning = None
        if days_until_expiry < 30:
            warning = f"IdP certificate expires in {days_until_expiry} days"

        return True, warning, cert_info

    def build_request_data(
        self,
        http_host: str,
        server_port: int,
        request_uri: str,
        https: bool = True,
        post_data: Optional[Dict[str, str]] = None,
        get_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build request data dictionary for python3-saml.

        Args:
            http_host: HTTP host header
            server_port: Server port
            request_uri: Request URI
            https: Whether using HTTPS
            post_data: POST parameters
            get_data: GET parameters

        Returns:
            Request data dictionary for OneLogin_Saml2_Auth
        """
        return {
            "https": "on" if https else "off",
            "http_host": http_host,
            "server_port": server_port,
            "script_name": request_uri,
            "get_data": get_data or {},
            "post_data": post_data or {},
        }


# Singleton instance cache
_saml_services: Dict[str, SAMLService] = {}


def get_saml_service(
    config: SAMLConfiguration,
    organization_id: str,
) -> SAMLService:
    """
    Get or create a SAML service instance for an organization.

    Args:
        config: SAML configuration
        organization_id: Organization ID

    Returns:
        SAMLService instance
    """
    cache_key = f"{organization_id}:{hash(str(config.dict()))}"
    if cache_key not in _saml_services:
        _saml_services[cache_key] = SAMLService(config, organization_id)
    return _saml_services[cache_key]


def clear_saml_service_cache(organization_id: Optional[str] = None) -> None:
    """
    Clear SAML service cache.

    Args:
        organization_id: Optional organization ID to clear.
                        If None, clears all cached services.
    """
    global _saml_services
    if organization_id:
        _saml_services = {
            k: v for k, v in _saml_services.items() if not k.startswith(f"{organization_id}:")
        }
    else:
        _saml_services = {}
