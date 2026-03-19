"""
Centralized configuration management for Blog AI.

This module provides a Pydantic Settings-based configuration system that:
- Validates environment variables at startup
- Provides type coercion (strings to ints, bools, etc.)
- Groups related settings for better organization
- Exposes methods to check if features are enabled
- Supports .env file loading

Usage:
    from src.config import get_settings, Settings

    settings = get_settings()
    if settings.is_stripe_configured:
        # Enable payment features
        ...
"""

import logging
import os
import sys
from functools import lru_cache
from typing import List, Literal, Optional, Set

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# LLM Provider Settings
# =============================================================================


class LLMSettings(BaseSettings):
    """Configuration for LLM providers (OpenAI, Anthropic, Gemini)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys (at least one is required)
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key for GPT models",
    )
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google Gemini API key",
    )

    # Model selection
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use",
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model to use",
    )

    # Request configuration
    llm_api_timeout: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Timeout in seconds for LLM API requests",
    )

    # Rate limiting
    llm_rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting for LLM API calls",
    )
    llm_rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum LLM API calls per minute",
    )
    llm_rate_limit_max_queue: int = Field(
        default=100,
        ge=1,
        description="Maximum requests to queue when rate limited",
    )
    llm_rate_limit_max_wait: float = Field(
        default=60.0,
        ge=0,
        description="Maximum seconds to wait for rate limit",
    )

    @property
    def has_any_provider(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return any([
            self.openai_api_key,
            self.anthropic_api_key,
            self.gemini_api_key,
        ])

    @property
    def available_providers(self) -> List[str]:
        """Get list of configured provider names."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.gemini_api_key:
            providers.append("gemini")
        return providers

    @property
    def default_provider(self) -> Optional[str]:
        """Get the default (first available) provider."""
        providers = self.available_providers
        return providers[0] if providers else None


# =============================================================================
# Database Settings (Postgres / Neon)
# =============================================================================


class DatabaseSettings(BaseSettings):
    """Configuration for Postgres database (Neon or any managed Postgres)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Use DATABASE_URL in serverless environments (Vercel) and prefer
    # DATABASE_URL_DIRECT for long-lived backends (Railway) when available.
    database_url: Optional[SecretStr] = Field(
        default=None,
        description="Postgres connection string (pooled is fine for serverless)",
    )
    database_url_direct: Optional[SecretStr] = Field(
        default=None,
        description="Direct Postgres connection string (recommended for long-lived backends)",
    )

    @property
    def is_configured(self) -> bool:
        """Check if a Postgres connection is configured."""
        return bool(self.database_url_direct or self.database_url)

    @property
    def effective_url(self) -> Optional[str]:
        """Return the preferred connection URL without exposing secrets in logs."""
        if self.database_url_direct:
            return self.database_url_direct.get_secret_value()
        if self.database_url:
            return self.database_url.get_secret_value()
        return None


# =============================================================================
# Payment Settings (Stripe)
# =============================================================================


class StripeSettings(BaseSettings):
    """Configuration for Stripe payment processing."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    stripe_secret_key: Optional[SecretStr] = Field(
        default=None,
        description="Stripe secret API key",
    )
    stripe_webhook_secret: Optional[SecretStr] = Field(
        default=None,
        description="Stripe webhook signing secret",
    )

    # Price IDs for subscription tiers
    stripe_price_id_starter: Optional[str] = Field(
        default=None,
        description="Stripe price ID for Starter tier",
    )
    stripe_price_id_pro: Optional[str] = Field(
        default=None,
        description="Stripe price ID for Pro tier",
    )
    stripe_price_id_business: Optional[str] = Field(
        default=None,
        description="Stripe price ID for Business tier",
    )

    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured for payments."""
        return bool(self.stripe_secret_key)

    @property
    def has_webhook_secret(self) -> bool:
        """Check if webhook verification is enabled."""
        return bool(self.stripe_webhook_secret)

    @property
    def has_price_ids(self) -> bool:
        """Check if at least one price ID is configured."""
        return any([
            self.stripe_price_id_starter,
            self.stripe_price_id_pro,
            self.stripe_price_id_business,
        ])


# =============================================================================
# Research Settings
# =============================================================================


class ResearchSettings(BaseSettings):
    """Configuration for research and web scraping APIs."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    serp_api_key: Optional[SecretStr] = Field(
        default=None,
        description="SERP API key for Google search results",
    )
    tavily_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Tavily API key for web research",
    )
    metaphor_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Metaphor API key for neural search",
    )
    sec_api_api_key: Optional[SecretStr] = Field(
        default=None,
        description="SEC API key for financial filings",
    )

    @property
    def has_any_research_api(self) -> bool:
        """Check if any research API is configured."""
        return any([
            self.serp_api_key,
            self.tavily_api_key,
            self.metaphor_api_key,
            self.sec_api_api_key,
        ])


# =============================================================================
# Image Generation Settings
# =============================================================================


class ImageSettings(BaseSettings):
    """Configuration for image generation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    image_provider: Literal["openai", "stability"] = Field(
        default="openai",
        description="Image generation provider (openai or stability)",
    )
    stability_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Stability AI API key",
    )

    @property
    def is_configured(self) -> bool:
        """Check if image generation is properly configured."""
        if self.image_provider == "openai":
            # OpenAI image gen uses the main OpenAI key
            return bool(os.environ.get("OPENAI_API_KEY"))
        elif self.image_provider == "stability":
            return bool(self.stability_api_key)
        return False


# =============================================================================
# Security Settings
# =============================================================================


class SecuritySettings(BaseSettings):
    """Configuration for security features."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    dev_api_key: Optional[str] = Field(
        default=None,
        description="Development API key for local testing (blocked in production)",
    )

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # HTTPS
    https_redirect_enabled: bool = Field(
        default=False,
        description="Enable HTTPS redirect middleware",
    )

    # HSTS
    security_hsts_enabled: Optional[bool] = Field(
        default=None,
        description="Enable HSTS (defaults to True in production)",
    )
    security_hsts_max_age: int = Field(
        default=31536000,
        ge=0,
        description="HSTS max-age in seconds",
    )

    # Request validation
    security_max_body_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Maximum request body size in bytes",
    )
    security_trust_request_id: bool = Field(
        default=False,
        description="Trust incoming X-Request-ID headers",
    )
    security_request_id_prefix: str = Field(
        default="blog-ai",
        description="Prefix for generated request IDs",
    )
    security_csp_policy: Optional[str] = Field(
        default=None,
        description="Custom Content-Security-Policy",
    )

    # General security toggle
    security_enabled: bool = Field(
        default=True,
        description="Enable security middleware stack",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def hsts_enabled(self) -> bool:
        """Get effective HSTS setting (auto-enabled in production)."""
        if self.security_hsts_enabled is not None:
            return self.security_hsts_enabled
        return self.is_production

    @property
    def origins_list(self) -> List[str]:
        """Get parsed list of allowed origins."""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


# =============================================================================
# Rate Limiting Settings
# =============================================================================


class RateLimitSettings(BaseSettings):
    """Configuration for API rate limiting."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting middleware",
    )
    rate_limit_general: int = Field(
        default=60,
        ge=1,
        description="General endpoints: requests per minute per IP",
    )
    rate_limit_generation: int = Field(
        default=10,
        ge=1,
        description="Generation endpoints: requests per minute per IP",
    )

    # Per-user generation rate limits by tier (per minute)
    rate_limit_gen_free_per_minute: int = Field(
        default=5,
        ge=1,
        description="Free tier: generation requests per minute per user",
    )
    rate_limit_gen_free_per_hour: int = Field(
        default=30,
        ge=1,
        description="Free tier: generation requests per hour per user",
    )
    rate_limit_gen_starter_per_minute: int = Field(
        default=10,
        ge=1,
        description="Starter tier: generation requests per minute per user",
    )
    rate_limit_gen_starter_per_hour: int = Field(
        default=100,
        ge=1,
        description="Starter tier: generation requests per hour per user",
    )
    rate_limit_gen_pro_per_minute: int = Field(
        default=20,
        ge=1,
        description="Pro tier: generation requests per minute per user",
    )
    rate_limit_gen_pro_per_hour: int = Field(
        default=200,
        ge=1,
        description="Pro tier: generation requests per hour per user",
    )
    rate_limit_gen_business_per_minute: int = Field(
        default=60,
        ge=1,
        description="Business tier: generation requests per minute per user",
    )
    rate_limit_gen_business_per_hour: int = Field(
        default=600,
        ge=1,
        description="Business tier: generation requests per hour per user",
    )


# =============================================================================
# Logging Settings
# =============================================================================


class LoggingSettings(BaseSettings):
    """Configuration for logging."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format_json: bool = Field(
        default=False,
        description="Force JSON log format in development",
    )
    request_logging_enabled: bool = Field(
        default=True,
        description="Enable request logging middleware",
    )


# =============================================================================
# Monitoring Settings (Sentry)
# =============================================================================


class SentrySettings(BaseSettings):
    """Configuration for Sentry error tracking."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment name",
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry transaction sample rate (0.0 to 1.0)",
    )
    sentry_profiles_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry profiling sample rate (0.0 to 1.0)",
    )
    sentry_release: Optional[str] = Field(
        default="blog-ai@1.0.0",
        description="Sentry release version",
    )
    server_name: str = Field(
        default="blog-ai-api",
        description="Server name for Sentry",
    )

    @property
    def is_configured(self) -> bool:
        """Check if Sentry is configured."""
        return bool(self.sentry_dsn)


# =============================================================================
# Storage Settings
# =============================================================================


class StorageSettings(BaseSettings):
    """Configuration for local storage."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    conversation_storage_dir: str = Field(
        default="./data/conversations",
        description="Directory for conversation persistence",
    )
    api_key_storage_path: str = Field(
        default="./data/api_keys.json",
        description="Path for API key storage",
    )
    usage_storage_dir: str = Field(
        default="./data/usage",
        description="Directory for usage tracking data",
    )


# =============================================================================
# Redis Settings (Optional)
# =============================================================================


class KnowledgeBaseSettings(BaseSettings):
    """Configuration for the Knowledge Base / RAG system."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enable_knowledge_base: bool = Field(
        default=True,
        description="Enable the Knowledge Base feature",
    )
    kb_vector_store: Literal["chromadb", "pinecone", "pgvector"] = Field(
        default="pgvector",
        description="Vector store provider for KB embeddings",
    )
    kb_embedding_provider: Literal["openai", "voyage", "cohere"] = Field(
        default="openai",
        description="Embedding provider for KB",
    )
    kb_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )
    kb_chunk_size: int = Field(
        default=512,
        ge=100,
        le=2048,
        description="Target chunk size in tokens",
    )
    kb_chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens",
    )

    # Tier limits: document count
    kb_free_max_docs: int = Field(default=2, ge=0)
    kb_free_max_storage_mb: int = Field(default=5, ge=0)
    kb_starter_max_docs: int = Field(default=20, ge=0)
    kb_starter_max_storage_mb: int = Field(default=50, ge=0)
    # Pro: unlimited (enforced as very large numbers)

    @property
    def is_enabled(self) -> bool:
        """Check if the knowledge base feature is enabled."""
        return self.enable_knowledge_base


class RedisSettings(BaseSettings):
    """Configuration for Redis (optional caching/queuing)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL",
    )

    @property
    def is_configured(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.redis_url)


# =============================================================================
# Main Settings Class
# =============================================================================


class Settings(BaseSettings):
    """
    Main settings class that aggregates all configuration groups.

    This class provides a single entry point for all application configuration
    with validation, type coercion, and feature detection.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Nested settings groups
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    stripe: StripeSettings = Field(default_factory=StripeSettings)
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    images: ImageSettings = Field(default_factory=ImageSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    sentry: SentrySettings = Field(default_factory=SentrySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    knowledge_base: KnowledgeBaseSettings = Field(default_factory=KnowledgeBaseSettings)

    # ==========================================================================
    # Feature Detection Properties
    # ==========================================================================

    @property
    def is_stripe_configured(self) -> bool:
        """Check if Stripe payment processing is available."""
        return self.stripe.is_configured

    @property
    def is_supabase_configured(self) -> bool:
        """Deprecated: kept for backward compatibility."""
        return self.database.is_configured

    @property
    def is_database_configured(self) -> bool:
        """Check if the Postgres database is available."""
        return self.database.is_configured

    @property
    def is_sentry_configured(self) -> bool:
        """Check if Sentry error tracking is available."""
        return self.sentry.is_configured

    @property
    def is_redis_configured(self) -> bool:
        """Check if Redis is available."""
        return self.redis.is_configured

    @property
    def is_knowledge_base_enabled(self) -> bool:
        """Check if the Knowledge Base feature is enabled."""
        return self.knowledge_base.is_enabled

    @property
    def has_llm_provider(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return self.llm.has_any_provider

    @property
    def has_research_api(self) -> bool:
        """Check if any research API is configured."""
        return self.research.has_any_research_api

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.security.is_production

    @property
    def is_dev_mode(self) -> bool:
        """Check if a development API key is configured."""
        return bool(self.security.dev_api_key)

    # ==========================================================================
    # Configuration Summary
    # ==========================================================================

    def get_config_summary(self) -> dict:
        """
        Get a summary of configuration status for logging.

        This method returns a dictionary with configuration status
        WITHOUT exposing any secrets.
        """
        return {
            "environment": self.security.environment,
            "dev_mode": self.is_dev_mode,
            "llm_providers": self.llm.available_providers,
            "default_llm_provider": self.llm.default_provider,
            "database_configured": self.is_database_configured,
            "stripe_configured": self.is_stripe_configured,
            "stripe_webhooks_enabled": self.stripe.has_webhook_secret,
            "sentry_configured": self.is_sentry_configured,
            "redis_configured": self.is_redis_configured,
            "research_apis_configured": self.has_research_api,
            "rate_limiting_enabled": self.rate_limit.rate_limit_enabled,
            "security_enabled": self.security.security_enabled,
            "https_redirect": self.security.https_redirect_enabled,
            "hsts_enabled": self.security.hsts_enabled,
            "allowed_origins": self.security.origins_list,
            "log_level": self.logging.log_level,
            "knowledge_base_enabled": self.is_knowledge_base_enabled,
            "knowledge_base_vector_store": self.knowledge_base.kb_vector_store,
        }


    def validate_production_config(self) -> None:
        """
        Validate configuration for production readiness.

        In production, required services must be configured or the app
        refuses to start.  In development, missing vars are logged as
        warnings so developers can iterate quickly.
        """
        _logger = logging.getLogger(__name__)

        is_prod = (
            self.security.environment == 'production'
            or os.environ.get('SENTRY_ENVIRONMENT', '').lower() == 'production'
            or os.environ.get('ENVIRONMENT', '').lower() == 'production'
            or os.environ.get('PYTHON_ENV', '').lower() == 'production'
        )

        errors: list[str] = []
        warnings: list[str] = []

        # --- LLM provider ---
        if not self.llm.has_any_provider:
            msg = (
                'No LLM provider API key set. '
                'Set at least one of OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY.'
            )
            if is_prod:
                errors.append(msg)
            else:
                _logger.warning(msg)

        # --- Database ---
        if not self.database.is_configured:
            msg = 'DATABASE_URL is not set. Database features will be unavailable.'
            if is_prod:
                errors.append(msg)
            else:
                _logger.warning(msg)

        # --- ALLOWED_ORIGINS ---
        origins = self.security.origins_list
        if not origins:
            msg = 'ALLOWED_ORIGINS is empty. CORS will reject all cross-origin requests.'
            if is_prod:
                errors.append(msg)
            else:
                _logger.warning(msg)
        elif is_prod:
            has_localhost = any(
                'localhost' in o or '127.0.0.1' in o for o in origins
            )
            if has_localhost:
                errors.append(
                    'ALLOWED_ORIGINS contains localhost entries in production. '
                    'Remove localhost/127.0.0.1 origins for production deployments.'
                )

        # --- Redis ---
        if not os.environ.get("REDIS_URL"):
            msg = (
                "REDIS_URL is not set. Bulk jobs and webhooks require Redis in production."
            )
            if is_prod:
                errors.append(msg)
            else:
                _logger.warning(msg)

        # --- Stripe (warn only) ---
        if not self.stripe.stripe_secret_key:
            msg = 'STRIPE_SECRET_KEY is not set. Revenue features will be disabled.'
            if is_prod:
                _logger.warning(msg)
            else:
                _logger.warning(msg)
        if not self.stripe.stripe_webhook_secret:
            msg = 'STRIPE_WEBHOOK_SECRET is not set. Webhook verification will be disabled.'
            if is_prod:
                _logger.warning(msg)
            else:
                _logger.warning(msg)

        # --- Fail hard in production ---
        if is_prod and errors:
            for err in errors:
                _logger.critical('PRODUCTION CONFIG ERROR: %s', err)
            _logger.critical(
                'Application cannot start due to %d configuration error(s). '
                'Fix the above issues and restart.',
                len(errors),
            )
            sys.exit(1)


# =============================================================================
# Settings Singleton
# =============================================================================


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings singleton.

    Uses lru_cache to ensure settings are only loaded once.
    Call get_settings.cache_clear() to reload settings.

    Returns:
        Validated Settings instance

    Raises:
        ValidationError: If required configuration is missing or invalid
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    This clears the cache and returns fresh settings.
    Useful for testing or after environment changes.
    """
    get_settings.cache_clear()
    return get_settings()
