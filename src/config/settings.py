"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables.
    Example: OPENAI_API_KEY, DEFAULT_MODEL, BLOG_SECTIONS, etc.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for GPT models",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key (optional)",
    )
    serp_api_key: str | None = Field(
        default=None,
        description="SerpAPI key for search (optional)",
    )

    # Model Configuration
    default_model: str = Field(
        default="gpt-4",
        description="Default OpenAI model to use",
    )
    temperature: float = Field(
        default=0.9,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0-2.0)",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Maximum tokens per request",
    )

    # Blog Generation Settings
    blog_sections: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of sections per blog post",
    )
    blog_subtopics_min: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Minimum subtopics per section",
    )
    blog_subtopics_max: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum subtopics per section",
    )

    # Book Generation Settings
    book_chapters: int = Field(
        default=11,
        ge=1,
        le=100,
        description="Number of chapters per book",
    )
    book_topics_per_chapter: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Number of topics per chapter",
    )
    book_target_words_per_topic: int = Field(
        default=2000,
        ge=100,
        description="Target word count per topic",
    )

    # Output Settings
    blog_output_dir: str = Field(
        default="content/blog",
        description="Directory for blog output",
    )
    book_output_dir: str = Field(
        default="content/books",
        description="Directory for book output",
    )

    # Rate Limiting & Retry
    api_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed API calls",
    )
    api_retry_delay: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        description="Delay between API calls (seconds)",
    )
    api_retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff multiplier",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose LLM chain output",
    )

    # Environment
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Application environment",
    )

    # Caching
    cache_enabled: bool = Field(
        default=True,
        description="Enable LLM response caching",
    )
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds (1 hour default, max 24 hours)",
    )
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Maximum number of cached entries",
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key is properly set."""
        if not v:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file.")

        # Check for common placeholder patterns
        v_stripped = v.strip()
        invalid_patterns = [
            "###",
            "YOUR",
            "REPLACE",
            "XXX",
            "your_",
            "sk-your-",
            "sk-test-",
            "placeholder",
            "example",
            "insert",
        ]

        v_lower = v_stripped.lower()
        if any(pattern.lower() in v_lower for pattern in invalid_patterns):
            raise ValueError(
                "API key appears to be a placeholder. "
                "Please set a valid OpenAI API key in .env file. "
                "Get your key at: https://platform.openai.com/api-keys"
            )

        # OpenAI keys are typically at least 20 characters
        if len(v_stripped) < 20:
            raise ValueError(
                f"API key is too short ({len(v_stripped)} chars). "
                "Valid OpenAI keys are typically 48+ characters. "
                "Please verify your key at: https://platform.openai.com/api-keys"
            )

        return v_stripped

    @model_validator(mode="after")
    def validate_subtopics_range(self) -> "Settings":
        """Ensure min <= max for subtopics."""
        if self.blog_subtopics_min > self.blog_subtopics_max:
            raise ValueError(
                f"blog_subtopics_min ({self.blog_subtopics_min}) cannot be greater than "
                f"blog_subtopics_max ({self.blog_subtopics_max})"
            )
        return self

    def get_blog_output_path(self) -> Path:
        """
        Get Path object for blog output directory.

        Creates directory if it doesn't exist and verifies it's writable.

        Returns:
            Path: Validated output directory path

        Raises:
            PermissionError: If directory is not writable
        """
        path = Path(self.blog_output_dir)
        path.mkdir(parents=True, exist_ok=True)

        # Verify directory is writable
        if not path.is_dir() or not path.exists():
            raise PermissionError(f"Cannot create blog output directory: {path}")

        # Test write permission
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise PermissionError(f"Blog output directory is not writable: {path}") from e

        return path

    def get_book_output_path(self) -> Path:
        """
        Get Path object for book output directory.

        Creates directory if it doesn't exist and verifies it's writable.

        Returns:
            Path: Validated output directory path

        Raises:
            PermissionError: If directory is not writable
        """
        path = Path(self.book_output_dir)
        path.mkdir(parents=True, exist_ok=True)

        # Verify directory is writable
        if not path.is_dir() or not path.exists():
            raise PermissionError(f"Cannot create book output directory: {path}")

        # Test write permission
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise PermissionError(f"Book output directory is not writable: {path}") from e

        return path


# Singleton instance - import this throughout the application
# Settings loads from environment variables via pydantic-settings
try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    import sys

    print(f"\n❌ Configuration Error: {e}", file=sys.stderr)
    print("\n💡 Troubleshooting:", file=sys.stderr)
    print("   1. Create a .env file: cp .env.example .env", file=sys.stderr)
    print("   2. Add your OpenAI API key: OPENAI_API_KEY=sk-...", file=sys.stderr)
    print("   3. Get a key at: https://platform.openai.com/api-keys\n", file=sys.stderr)
    sys.exit(1)
