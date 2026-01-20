"""
Centralized configuration management.

Loads settings from environment variables with validation and defaults.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", "sqlite:///./data/blog_ai.db"
        )
    )
    pool_size: int = field(
        default_factory=lambda: int(os.environ.get("DB_POOL_SIZE", "5"))
    )
    max_overflow: int = field(
        default_factory=lambda: int(os.environ.get("DB_MAX_OVERFLOW", "10"))
    )
    echo: bool = field(
        default_factory=lambda: os.environ.get("SQL_ECHO", "false").lower() == "true"
    )


@dataclass
class AuthConfig:
    """Authentication configuration."""

    jwt_secret: str = field(
        default_factory=lambda: os.environ.get(
            "JWT_SECRET", "change-me-in-production"
        )
    )
    jwt_expiration_hours: int = field(
        default_factory=lambda: int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))
    )
    jwt_refresh_days: int = field(
        default_factory=lambda: int(os.environ.get("JWT_REFRESH_EXPIRATION_DAYS", "7"))
    )
    api_key_header: str = "X-API-Key"


@dataclass
class CORSConfig:
    """CORS configuration."""

    allowed_origins: List[str] = field(
        default_factory=lambda: os.environ.get(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
    )
    allow_credentials: bool = True
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "OPTIONS", "DELETE", "PUT"])
    allowed_headers: List[str] = field(
        default_factory=lambda: ["Authorization", "Content-Type", "X-API-Key"]
    )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    enabled: bool = field(
        default_factory=lambda: os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    general_limit: int = field(
        default_factory=lambda: int(os.environ.get("RATE_LIMIT_GENERAL", "60"))
    )
    generation_limit: int = field(
        default_factory=lambda: int(os.environ.get("RATE_LIMIT_GENERATION", "10"))
    )
    window_seconds: int = 60


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )
    openai_model: str = field(
        default_factory=lambda: os.environ.get("OPENAI_MODEL", "gpt-4")
    )
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )
    anthropic_model: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    )
    gemini_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY")
    )
    gemini_model: str = field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-latest")
    )


@dataclass
class AppConfig:
    """Main application configuration."""

    # Environment
    environment: str = field(
        default_factory=lambda: os.environ.get("ENVIRONMENT", "development")
    )
    dev_mode: bool = field(
        default_factory=lambda: os.environ.get("DEV_MODE", "false").lower() == "true"
    )
    debug: bool = field(
        default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true"
    )

    # Server
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8000")))

    # Security
    https_redirect: bool = field(
        default_factory=lambda: os.environ.get("HTTPS_REDIRECT_ENABLED", "false").lower() == "true"
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO").upper()
    )
    log_format: str = field(
        default_factory=lambda: os.environ.get("LOG_FORMAT", "json")
    )

    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development" or self.dev_mode

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.
        """
        warnings = []

        # Check JWT secret in production
        if self.is_production and self.auth.jwt_secret == "change-me-in-production":
            warnings.append("CRITICAL: JWT_SECRET must be set in production!")

        # Check LLM API keys
        if not any([self.llm.openai_api_key, self.llm.anthropic_api_key, self.llm.gemini_api_key]):
            warnings.append("WARNING: No LLM API keys configured. Content generation will fail.")

        # Check HTTPS in production
        if self.is_production and not self.https_redirect:
            warnings.append("WARNING: HTTPS redirect is disabled in production.")

        return warnings


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the application configuration.

    Creates the config on first call and caches it.
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """
    Reload the configuration from environment variables.
    """
    global _config
    _config = AppConfig()
    return _config
