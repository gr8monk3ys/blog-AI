"""Unit tests for configuration."""

import os

import pytest
from pydantic import ValidationError

from src.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_requires_api_key(self, monkeypatch):
        """Test that OpenAI API key is required."""
        # Remove API key env var
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "openai_api_key" in str(exc_info.value)

    def test_settings_validates_api_key(self, monkeypatch):
        """Test that placeholder API keys are rejected."""
        # Test with placeholder key
        monkeypatch.setenv("OPENAI_API_KEY", "###YOUR KEY HERE")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "placeholder" in str(exc_info.value).lower()

    def test_settings_with_valid_key(self, monkeypatch):
        """Test creating settings with valid API key."""
        test_key = "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        settings = Settings()
        assert settings.openai_api_key == test_key
        assert settings.default_model == "gpt-4"
        assert settings.temperature == 0.9

    def test_settings_default_values(self, monkeypatch):
        """Test default configuration values."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

        settings = Settings()

        # Model settings
        assert settings.default_model == "gpt-4"
        assert settings.temperature == 0.9
        assert settings.max_tokens is None

        # Blog settings
        assert settings.blog_sections == 3
        assert settings.blog_subtopics_min == 2
        assert settings.blog_subtopics_max == 3

        # Book settings
        assert settings.book_chapters == 11
        assert settings.book_topics_per_chapter == 4
        assert settings.book_target_words_per_topic == 2000

        # Output settings
        assert settings.blog_output_dir == "content/blog"
        assert settings.book_output_dir == "content/books"

        # Retry settings
        assert settings.api_retry_attempts == 3
        assert settings.api_retry_delay == 2.0
        assert settings.api_retry_backoff == 2.0

    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")
        monkeypatch.setenv("DEFAULT_MODEL", "gpt-3.5-turbo")
        monkeypatch.setenv("TEMPERATURE", "0.7")
        monkeypatch.setenv("BLOG_SECTIONS", "5")
        monkeypatch.setenv("BOOK_CHAPTERS", "15")

        settings = Settings()

        assert settings.default_model == "gpt-3.5-turbo"
        assert settings.temperature == 0.7
        assert settings.blog_sections == 5
        assert settings.book_chapters == 15

    def test_settings_temperature_validation(self, monkeypatch):
        """Test temperature range validation."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

        # Valid temperatures
        monkeypatch.setenv("TEMPERATURE", "0.0")
        settings = Settings()
        assert settings.temperature == 0.0

        monkeypatch.setenv("TEMPERATURE", "2.0")
        settings = Settings()
        assert settings.temperature == 2.0

        # Invalid (too low)
        monkeypatch.setenv("TEMPERATURE", "-0.1")
        with pytest.raises(ValidationError):
            Settings()

        # Invalid (too high)
        monkeypatch.setenv("TEMPERATURE", "2.1")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_subtopics_range_validation(self, monkeypatch):
        """Test subtopics min/max validation."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

        # Valid range
        monkeypatch.setenv("BLOG_SUBTOPICS_MIN", "2")
        monkeypatch.setenv("BLOG_SUBTOPICS_MAX", "5")
        settings = Settings()
        assert settings.blog_subtopics_min == 2
        assert settings.blog_subtopics_max == 5

        # Invalid (min > max)
        monkeypatch.setenv("BLOG_SUBTOPICS_MIN", "5")
        monkeypatch.setenv("BLOG_SUBTOPICS_MAX", "2")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_output_paths(self, monkeypatch, tmp_path):
        """Test output path methods."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")
        monkeypatch.setenv("BLOG_OUTPUT_DIR", str(tmp_path / "blogs"))
        monkeypatch.setenv("BOOK_OUTPUT_DIR", str(tmp_path / "books"))

        settings = Settings()

        # Get paths (should create directories)
        blog_path = settings.get_blog_output_path()
        book_path = settings.get_book_output_path()

        assert blog_path.exists()
        assert blog_path.is_dir()
        assert book_path.exists()
        assert book_path.is_dir()

    def test_settings_optional_keys(self, monkeypatch):
        """Test optional API keys."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

        # Without optional keys
        settings = Settings()
        assert settings.anthropic_api_key is None
        assert settings.serp_api_key is None

        # With optional keys
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("SERP_API_KEY", "serp-test")

        settings = Settings()
        assert settings.anthropic_api_key == "sk-ant-test"
        assert settings.serp_api_key == "serp-test"

    def test_settings_retry_validation(self, monkeypatch):
        """Test retry settings validation."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

        # Valid retry settings
        monkeypatch.setenv("API_RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("API_RETRY_DELAY", "1.5")
        monkeypatch.setenv("API_RETRY_BACKOFF", "3.0")

        settings = Settings()
        assert settings.api_retry_attempts == 5
        assert settings.api_retry_delay == 1.5
        assert settings.api_retry_backoff == 3.0

        # Invalid (attempts < 1)
        monkeypatch.setenv("API_RETRY_ATTEMPTS", "0")
        with pytest.raises(ValidationError):
            Settings()

        # Invalid (delay too small)
        monkeypatch.setenv("API_RETRY_ATTEMPTS", "3")
        monkeypatch.setenv("API_RETRY_DELAY", "0.05")
        with pytest.raises(ValidationError):
            Settings()
