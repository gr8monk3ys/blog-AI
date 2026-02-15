"""
Configuration validation for Blog AI startup.

This module provides comprehensive validation of the application configuration
at startup time, with clear error messages and warnings for missing or
invalid configuration.

Usage:
    from src.config_validator import validate_config, ConfigurationError

    try:
        validate_config()
    except ConfigurationError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)
"""

import logging
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class ConfigurationError(Exception):
    """
    Raised when critical configuration is missing or invalid.

    This exception should cause the application to fail fast at startup.
    """

    def __init__(self, message: str, missing_vars: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_vars = missing_vars or []


class ConfigurationWarning(Exception):
    """
    Raised for non-critical configuration issues.

    These are logged as warnings but don't prevent startup.
    """

    pass


# =============================================================================
# Validation Result
# =============================================================================


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add a critical error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a non-critical warning."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add an informational message."""
        self.info.append(message)


# =============================================================================
# Validation Functions
# =============================================================================


def validate_llm_config(settings: Settings, result: ValidationResult) -> None:
    """Validate LLM provider configuration."""
    llm = settings.llm

    if not llm.has_any_provider:
        result.add_error(
            "No LLM provider configured. At least one of the following is required: "
            "OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
        )
        return

    # Log available providers
    providers = llm.available_providers
    result.add_info(f"LLM providers configured: {', '.join(providers)}")
    result.add_info(f"Default provider: {llm.default_provider}")

    # Warn about timeout settings
    if llm.llm_api_timeout < 30:
        result.add_warning(
            f"LLM_API_TIMEOUT is set to {llm.llm_api_timeout}s which may cause "
            "timeouts for longer generation requests. Consider 60s or higher."
        )


def validate_security_config(settings: Settings, result: ValidationResult) -> None:
    """Validate security configuration."""
    security = settings.security

    if security.is_production:
        # Production-specific checks
        if security.dev_mode:
            result.add_error(
                "DEV_MODE=true is not allowed in production environment. "
                "Set DEV_MODE=false for production deployment."
            )

        if not security.https_redirect_enabled:
            result.add_warning(
                "HTTPS_REDIRECT_ENABLED is false in production. "
                "Enable HTTPS redirect for secure deployment."
            )

        # Check for insecure origins
        for origin in security.origins_list:
            if origin == "*":
                result.add_error(
                    "Wildcard (*) CORS origin is not allowed in production. "
                    "Configure ALLOWED_ORIGINS with specific domains."
                )
            elif "localhost" in origin or "127.0.0.1" in origin:
                result.add_warning(
                    f"Development origin '{origin}' detected in production. "
                    "Remove localhost origins for production deployment."
                )

        if not security.security_enabled:
            result.add_warning(
                "SECURITY_ENABLED=false in production. "
                "This disables important security middleware."
            )

    else:
        # Development-specific info
        if security.dev_mode:
            result.add_info(
                "DEV_MODE is enabled. API key authentication may be bypassed."
            )


def validate_database_config(settings: Settings, result: ValidationResult) -> None:
    """Validate database configuration."""
    db = settings.database

    if not db.is_configured:
        result.add_warning(
            "Database is not configured (DATABASE_URL or DATABASE_URL_DIRECT). "
            "Features requiring persistence may fall back to in-memory or local storage."
        )
    else:
        result.add_info("Postgres database configured")


def validate_stripe_config(settings: Settings, result: ValidationResult) -> None:
    """Validate Stripe configuration."""
    stripe = settings.stripe

    if not stripe.is_configured:
        result.add_info(
            "Stripe is not configured (STRIPE_SECRET_KEY). "
            "Payment features will be disabled."
        )
        return

    result.add_info("Stripe payment processing configured")

    if not stripe.has_webhook_secret:
        result.add_warning(
            "STRIPE_WEBHOOK_SECRET not configured. "
            "Webhook signature verification will fail."
        )

    if not stripe.has_price_ids:
        result.add_warning(
            "No Stripe price IDs configured (STRIPE_PRICE_ID_*). "
            "Subscription checkout will not work until price IDs are set."
        )


def validate_sentry_config(settings: Settings, result: ValidationResult) -> None:
    """Validate Sentry configuration."""
    sentry = settings.sentry

    if not sentry.is_configured:
        if settings.security.is_production:
            result.add_warning(
                "SENTRY_DSN not configured in production. "
                "Error tracking is recommended for production deployments."
            )
        else:
            result.add_info("Sentry not configured. Error tracking disabled.")
    else:
        result.add_info(
            f"Sentry configured for environment: {sentry.sentry_environment}"
        )


def validate_research_config(settings: Settings, result: ValidationResult) -> None:
    """Validate research API configuration."""
    research = settings.research

    if not research.has_any_research_api:
        result.add_info(
            "No research APIs configured (SERP_API_KEY, TAVILY_API_KEY, etc.). "
            "Web research features will be limited."
        )


def validate_rate_limit_config(settings: Settings, result: ValidationResult) -> None:
    """Validate rate limiting configuration."""
    rate_limit = settings.rate_limit

    if not rate_limit.rate_limit_enabled:
        if settings.security.is_production:
            result.add_warning(
                "RATE_LIMIT_ENABLED=false in production. "
                "Rate limiting is recommended to prevent abuse."
            )

    if rate_limit.rate_limit_generation > 100:
        result.add_warning(
            f"RATE_LIMIT_GENERATION is set to {rate_limit.rate_limit_generation}/min. "
            "High limits may lead to excessive API costs."
        )


def validate_storage_config(settings: Settings, result: ValidationResult) -> None:
    """Validate storage configuration."""
    import os

    storage = settings.storage

    # Check if storage directories exist or can be created
    dirs_to_check = [
        ("CONVERSATION_STORAGE_DIR", storage.conversation_storage_dir),
        ("USAGE_STORAGE_DIR", storage.usage_storage_dir),
    ]

    for name, path in dirs_to_check:
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                result.add_info(f"Created storage directory: {path}")
            except PermissionError:
                result.add_warning(
                    f"Cannot create {name} directory at {path}. "
                    "Check file system permissions."
                )


# =============================================================================
# Main Validation Function
# =============================================================================


def validate_config(
    settings: Optional[Settings] = None,
    fail_on_error: bool = True,
) -> ValidationResult:
    """
    Validate the application configuration.

    This function performs comprehensive validation of all configuration
    settings and returns a ValidationResult with errors, warnings, and info.

    Args:
        settings: Settings instance to validate (uses get_settings() if None)
        fail_on_error: If True, raises ConfigurationError on critical errors

    Returns:
        ValidationResult with validation status and messages

    Raises:
        ConfigurationError: If fail_on_error is True and critical errors found
    """
    if settings is None:
        try:
            settings = get_settings()
        except Exception as e:
            logger.critical(f"Failed to load configuration: {e}")
            if fail_on_error:
                raise ConfigurationError(f"Failed to load configuration: {e}") from e
            result = ValidationResult(is_valid=False)
            result.add_error(f"Failed to load configuration: {e}")
            return result

    result = ValidationResult(is_valid=True)

    # Run all validators
    validate_llm_config(settings, result)
    validate_security_config(settings, result)
    validate_database_config(settings, result)
    validate_stripe_config(settings, result)
    validate_sentry_config(settings, result)
    validate_research_config(settings, result)
    validate_rate_limit_config(settings, result)
    validate_storage_config(settings, result)

    # Log results
    for info in result.info:
        logger.info(f"[CONFIG] {info}")

    for warning in result.warnings:
        logger.warning(f"[CONFIG] {warning}")

    for error in result.errors:
        logger.error(f"[CONFIG] {error}")

    # Raise on critical errors if requested
    if fail_on_error and not result.is_valid:
        raise ConfigurationError(
            f"Configuration validation failed with {len(result.errors)} error(s). "
            "See logs for details.",
            missing_vars=[],
        )

    return result


def log_config_summary(settings: Optional[Settings] = None) -> None:
    """
    Log a summary of the current configuration.

    This is useful for startup logging to confirm which features are enabled.
    """
    if settings is None:
        settings = get_settings()

    summary = settings.get_config_summary()

    logger.info("=" * 60)
    logger.info("Blog AI Configuration Summary")
    logger.info("=" * 60)
    logger.info(f"Environment: {summary['environment']}")
    logger.info(f"Dev Mode: {summary['dev_mode']}")
    logger.info(f"Log Level: {summary['log_level']}")
    logger.info("-" * 60)
    logger.info("Features:")
    logger.info(f"  LLM Providers: {', '.join(summary['llm_providers']) or 'None'}")
    logger.info(f"  Default Provider: {summary['default_llm_provider'] or 'None'}")
    logger.info(f"  Database: {'Enabled' if summary.get('database_configured') else 'Disabled'}")
    logger.info(f"  Stripe Payments: {'Enabled' if summary['stripe_configured'] else 'Disabled'}")
    logger.info(f"  Stripe Webhooks: {'Enabled' if summary['stripe_webhooks_enabled'] else 'Disabled'}")
    logger.info(f"  Sentry Monitoring: {'Enabled' if summary['sentry_configured'] else 'Disabled'}")
    logger.info(f"  Redis Cache: {'Enabled' if summary['redis_configured'] else 'Disabled'}")
    logger.info(f"  Research APIs: {'Enabled' if summary['research_apis_configured'] else 'Disabled'}")
    logger.info("-" * 60)
    logger.info("Security:")
    logger.info(f"  Rate Limiting: {'Enabled' if summary['rate_limiting_enabled'] else 'Disabled'}")
    logger.info(f"  Security Middleware: {'Enabled' if summary['security_enabled'] else 'Disabled'}")
    logger.info(f"  HTTPS Redirect: {'Enabled' if summary['https_redirect'] else 'Disabled'}")
    logger.info(f"  HSTS: {'Enabled' if summary['hsts_enabled'] else 'Disabled'}")
    logger.info(f"  Allowed Origins: {len(summary['allowed_origins'])} configured")
    logger.info("=" * 60)


def startup_validation() -> Settings:
    """
    Perform full startup validation and return settings.

    This is the main entry point for configuration validation at startup.
    It validates configuration, logs a summary, and returns the settings
    or raises ConfigurationError on critical failures.

    Returns:
        Validated Settings instance

    Raises:
        ConfigurationError: If critical configuration is missing
    """
    # Load and validate settings
    settings = get_settings()
    validate_config(settings, fail_on_error=True)

    # Log configuration summary
    log_config_summary(settings)

    return settings
