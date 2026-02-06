"""
Security validators for input sanitization and validation.

This module provides centralized validation functions to protect against:
- SSRF (Server-Side Request Forgery) via URL validation
- CSV formula injection in batch imports/exports
- HTML injection in brand voice samples
- Prompt injection in topic/content fields
- Provider enumeration attacks

Usage:
    from app.validators import validate_url, validate_topic, sanitize_csv_field
"""

import html
import ipaddress
import re
import socket
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse

import bleach

# =============================================================================
# Constants
# =============================================================================

# Allowed LLM providers (whitelist)
ALLOWED_PROVIDERS: Set[str] = {"openai", "anthropic", "gemini"}

# Allowed URL schemes for external resources
ALLOWED_URL_SCHEMES: Set[str] = {"http", "https"}

# Blocked hostnames for SSRF protection
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::1]",
    "metadata.google.internal",
    "metadata.google",
    "169.254.169.254",  # AWS/GCP metadata endpoint
    "metadata",
    "instance-data",
}

# Private IP ranges (CIDR notation)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

# CSV formula injection characters
CSV_FORMULA_CHARS: Set[str] = {"=", "+", "-", "@", "\t", "\r", "\n"}

# Allowed HTML tags for brand voice samples (whitelist approach)
# Used by bleach for proper HTML sanitization
ALLOWED_HTML_TAGS: Set[str] = {
    "p", "br", "b", "i", "u", "strong", "em", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "code", "pre",
}

# Allowed HTML attributes (whitelist for bleach)
ALLOWED_HTML_ATTRIBUTES: dict = {
    "*": ["class", "id"],  # Allow class and id on all elements
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}

# Prompt injection patterns (additional to existing sanitization)
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|?(system|user|assistant)\|?>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"```\s*(system|prompt)", re.IGNORECASE),
    re.compile(r"human:\s*", re.IGNORECASE),
    re.compile(r"assistant:\s*", re.IGNORECASE),
    re.compile(r"</?s>", re.IGNORECASE),  # Some model special tokens
]


# =============================================================================
# URL Validation (SSRF Protection)
# =============================================================================

class SSRFValidationError(ValueError):
    """Raised when URL fails SSRF validation."""
    pass


def _is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is in a private/reserved range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return True
        # Also check for reserved addresses
        if hasattr(ip, 'is_private') and ip.is_private:
            return True
        if hasattr(ip, 'is_reserved') and ip.is_reserved:
            return True
        if hasattr(ip, 'is_loopback') and ip.is_loopback:
            return True
        if hasattr(ip, 'is_link_local') and ip.is_link_local:
            return True
        return False
    except ValueError:
        return False


def _resolve_hostname(hostname: str) -> Optional[str]:
    """Resolve hostname to IP address for validation."""
    try:
        # Get all IP addresses for the hostname
        ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        if ip_addresses:
            # Return the first IP address
            return ip_addresses[0][4][0]
    except (socket.gaierror, socket.herror, OSError):
        pass
    return None


def validate_url(
    url: str,
    allow_private: bool = False,
    allowed_schemes: Optional[Set[str]] = None,
    resolve_dns: bool = True,
) -> Tuple[bool, str]:
    """
    Validate a URL for SSRF protection.

    This function checks:
    1. URL scheme is allowed (http/https by default)
    2. Hostname is not in blocklist
    3. Resolved IP is not in private/reserved ranges

    Args:
        url: The URL to validate
        allow_private: Allow private IP addresses (default: False)
        allowed_schemes: Set of allowed URL schemes (default: http, https)
        resolve_dns: Whether to resolve DNS and check IP (default: True)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_url("https://example.com/api")
        >>> if not is_valid:
        ...     raise ValueError(error)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()
    schemes = allowed_schemes or ALLOWED_URL_SCHEMES

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Check scheme
    if not parsed.scheme:
        return False, "URL must include a scheme (http:// or https://)"

    if parsed.scheme.lower() not in schemes:
        return False, f"URL scheme must be one of: {', '.join(schemes)}"

    # Check hostname exists
    if not parsed.hostname:
        return False, "URL must include a hostname"

    hostname = parsed.hostname.lower()

    # Check blocked hostnames
    if hostname in BLOCKED_HOSTNAMES:
        return False, f"Hostname '{hostname}' is not allowed"

    # Check for IP address in hostname
    try:
        ip = ipaddress.ip_address(hostname)
        if not allow_private and _is_private_ip(str(ip)):
            return False, "Private/internal IP addresses are not allowed"
    except ValueError:
        # Not an IP address, it's a hostname - resolve it
        if resolve_dns:
            resolved_ip = _resolve_hostname(hostname)
            if resolved_ip and not allow_private and _is_private_ip(resolved_ip):
                return False, f"Hostname resolves to private/internal IP address"

    # Check for suspicious patterns in URL
    if "@" in parsed.netloc:
        return False, "URL contains suspicious authentication pattern"

    # Check port (block common internal service ports)
    if parsed.port:
        blocked_ports = {22, 23, 25, 3306, 5432, 6379, 27017, 11211}
        if parsed.port in blocked_ports:
            return False, f"Port {parsed.port} is not allowed"

    return True, ""


def validate_url_strict(url: str) -> str:
    """
    Validate URL and raise exception if invalid.

    Use this as a Pydantic field validator.

    Args:
        url: The URL to validate

    Returns:
        The validated URL

    Raises:
        ValueError: If URL fails validation
    """
    is_valid, error = validate_url(url)
    if not is_valid:
        raise ValueError(error)
    return url


# =============================================================================
# Provider Validation
# =============================================================================

def validate_provider(provider: str) -> str:
    """
    Validate that provider is in the allowed whitelist.

    Args:
        provider: The provider name to validate

    Returns:
        The validated provider name (lowercase)

    Raises:
        ValueError: If provider is not in allowed list
    """
    if not provider:
        return "openai"  # Default

    normalized = provider.lower().strip()

    if normalized not in ALLOWED_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. "
            f"Allowed providers: {', '.join(sorted(ALLOWED_PROVIDERS))}"
        )

    return normalized


# =============================================================================
# Topic and Content Validation
# =============================================================================

def validate_topic(topic: str, max_length: int = 500) -> str:
    """
    Validate and sanitize a topic string.

    Checks for:
    - Empty/whitespace-only content
    - Excessive length
    - Prompt injection patterns
    - Control characters

    Args:
        topic: The topic string to validate
        max_length: Maximum allowed length (default: 500)

    Returns:
        The sanitized topic string

    Raises:
        ValueError: If topic is invalid or contains injection attempts
    """
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")

    # Strip whitespace and normalize
    topic = topic.strip()

    # Check length
    if len(topic) > max_length:
        raise ValueError(f"Topic exceeds maximum length of {max_length} characters")

    if len(topic) < 3:
        raise ValueError("Topic must be at least 3 characters")

    # Remove control characters (keep newlines for multi-line topics)
    topic = "".join(char for char in topic if char.isprintable() or char in "\n\t")

    # Check for prompt injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(topic):
            raise ValueError("Topic contains potentially unsafe content")

    return topic


def validate_keywords(keywords: List[str], max_count: int = 20, max_length: int = 50) -> List[str]:
    """
    Validate and sanitize a list of keywords.

    Args:
        keywords: List of keyword strings
        max_count: Maximum number of keywords allowed
        max_length: Maximum length per keyword

    Returns:
        List of validated, sanitized keywords

    Raises:
        ValueError: If keywords are invalid
    """
    if not keywords:
        return []

    if len(keywords) > max_count:
        raise ValueError(f"Too many keywords. Maximum allowed: {max_count}")

    validated = []
    for kw in keywords:
        if not kw or not kw.strip():
            continue

        kw = kw.strip().lower()

        # Check length
        if len(kw) > max_length:
            raise ValueError(f"Keyword '{kw[:20]}...' exceeds maximum length of {max_length}")

        # Remove any control characters
        kw = "".join(char for char in kw if char.isprintable())

        # Check for injection patterns
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(kw):
                raise ValueError(f"Keyword contains potentially unsafe content")

        if kw:  # Only add non-empty keywords
            validated.append(kw)

    return validated


# =============================================================================
# CSV Sanitization (Formula Injection Protection)
# =============================================================================

def sanitize_csv_field(value: str) -> str:
    """
    Sanitize a string value for safe CSV export.

    Prevents CSV formula injection by prefixing dangerous characters
    with a single quote, which prevents Excel/Sheets from interpreting
    the cell as a formula.

    Args:
        value: The string value to sanitize

    Returns:
        Sanitized string safe for CSV export

    Example:
        >>> sanitize_csv_field("=SUM(A1:A10)")
        "'=SUM(A1:A10)"
        >>> sanitize_csv_field("Normal text")
        "Normal text"
    """
    if not value:
        return value

    value = str(value)

    # Check if first character could trigger formula interpretation
    if value and value[0] in CSV_FORMULA_CHARS:
        # Prefix with single quote to prevent formula execution
        return f"'{value}"

    return value


def sanitize_csv_row(row: dict) -> dict:
    """
    Sanitize all string fields in a CSV row dictionary.

    Args:
        row: Dictionary of field name -> value pairs

    Returns:
        Dictionary with all string values sanitized
    """
    return {
        key: sanitize_csv_field(str(val)) if isinstance(val, str) else val
        for key, val in row.items()
    }


def validate_csv_import_field(value: str, field_name: str, max_length: int = 1000) -> str:
    """
    Validate and sanitize a field from CSV import.

    Args:
        value: The field value
        field_name: Name of the field (for error messages)
        max_length: Maximum allowed length

    Returns:
        Validated and sanitized value

    Raises:
        ValueError: If validation fails
    """
    if not value:
        return value

    value = str(value).strip()

    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

    # Strip formula characters from start
    while value and value[0] in CSV_FORMULA_CHARS:
        value = value[1:].strip()

    return value


# =============================================================================
# HTML Sanitization (XSS Protection)
# =============================================================================

def sanitize_html_content(content: str, strip_all_tags: bool = False) -> str:
    """
    Sanitize HTML content for safe storage and display.

    Uses the bleach library for proper HTML sanitization that cannot be
    bypassed by crafted input (unlike regex-based approaches).

    Removes dangerous HTML elements (script, style, iframe, etc.) and
    event handlers while optionally preserving safe formatting tags.

    Args:
        content: The HTML content to sanitize
        strip_all_tags: If True, remove ALL HTML tags (default: False)

    Returns:
        Sanitized content
    """
    if not content:
        return content

    if strip_all_tags:
        # Remove all HTML tags using bleach
        content = bleach.clean(content, tags=[], strip=True)
    else:
        # Use bleach with whitelist of allowed tags
        # This properly handles all edge cases that regex cannot
        content = bleach.clean(
            content,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            strip=True,
            strip_comments=True,
        )

    return content.strip()


def validate_html_content(
    content: str,
    max_length: int = 50000,
    strip_all_tags: bool = False
) -> str:
    """
    Validate and sanitize HTML content.

    Args:
        content: The content to validate
        max_length: Maximum allowed length after sanitization
        strip_all_tags: Whether to strip all HTML tags

    Returns:
        Validated and sanitized content

    Raises:
        ValueError: If content is invalid
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    # Sanitize first
    sanitized = sanitize_html_content(content, strip_all_tags)

    # Check length after sanitization
    if len(sanitized) > max_length:
        raise ValueError(f"Content exceeds maximum length of {max_length} characters")

    if len(sanitized) < 10:
        raise ValueError("Content must be at least 10 characters after sanitization")

    return sanitized


# =============================================================================
# ID Validation (Path Parameter Protection)
# =============================================================================

# Valid ID formats
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)
SIMPLE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
CONVERSATION_ID_PATTERN = re.compile(r"^conv-[a-zA-Z0-9_-]{1,100}$")


def validate_id(
    id_value: str,
    id_type: str = "generic",
    allow_uuid: bool = True,
    allow_simple: bool = True
) -> str:
    """
    Validate an ID parameter for safe use in queries and paths.

    Args:
        id_value: The ID value to validate
        id_type: Type of ID for error messages (e.g., "job", "profile")
        allow_uuid: Allow UUID format
        allow_simple: Allow simple alphanumeric format

    Returns:
        Validated ID value

    Raises:
        ValueError: If ID format is invalid
    """
    if not id_value or not id_value.strip():
        raise ValueError(f"{id_type.title()} ID cannot be empty")

    id_value = id_value.strip()

    # Check against allowed patterns
    if allow_uuid and UUID_PATTERN.match(id_value):
        return id_value

    if allow_simple and SIMPLE_ID_PATTERN.match(id_value):
        return id_value

    # Check for conversation ID format
    if CONVERSATION_ID_PATTERN.match(id_value):
        return id_value

    raise ValueError(
        f"Invalid {id_type} ID format. "
        "Must be a UUID or alphanumeric string (max 100 chars, may include - and _)"
    )


def validate_job_id(job_id: str) -> str:
    """Validate a batch job ID."""
    return validate_id(job_id, id_type="job")


def validate_profile_id(profile_id: str) -> str:
    """Validate a brand profile ID."""
    return validate_id(profile_id, id_type="profile")


def validate_conversation_id(conversation_id: str) -> str:
    """Validate a conversation ID."""
    return validate_id(conversation_id, id_type="conversation")


# =============================================================================
# Content Size Validation
# =============================================================================

def validate_content_size(
    content: str,
    min_length: int = 0,
    max_length: int = 100000,
    field_name: str = "content"
) -> str:
    """
    Validate content meets size requirements.

    Args:
        content: The content to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        field_name: Name of field for error messages

    Returns:
        The validated content

    Raises:
        ValueError: If content size is invalid
    """
    if content is None:
        if min_length > 0:
            raise ValueError(f"{field_name} is required")
        return ""

    content = str(content)

    if len(content) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if len(content) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")

    return content
