"""Pytest configuration and shared fixtures."""

import os

# Set dummy API key for testing BEFORE importing src modules
# This prevents ValidationError when Settings() is instantiated at module level
# Note: Must be 20+ chars and not match invalid patterns in settings.py
os.environ.setdefault("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.config import Settings
from src.repositories import FileRepository
from src.services import BlogGenerator, BookGenerator, DOCXFormatter, MDXFormatter, OpenAIProvider
from tests.fixtures.sample_data import SAMPLE_BLOG_POST, SAMPLE_BOOK


@pytest.fixture
def mock_settings(monkeypatch):
    """Create mock settings with test API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-fake1234567890abcdefghijklmnopqrstuvwxyz")
    return Settings()


@pytest.fixture
def mock_llm_provider():
    """Create a mocked LLM provider."""
    provider = Mock(spec=OpenAIProvider)
    provider.generate.return_value = "Generated text content"
    provider.generate_structured.return_value = SAMPLE_BLOG_POST
    return provider


@pytest.fixture
def blog_generator(mock_llm_provider, mock_settings):
    """Create blog generator with mocked dependencies."""
    return BlogGenerator(mock_llm_provider, mock_settings)


@pytest.fixture
def book_generator(mock_llm_provider, mock_settings):
    """Create book generator with mocked dependencies."""
    return BookGenerator(mock_llm_provider, mock_settings)


@pytest.fixture
def mdx_formatter():
    """Create MDX formatter."""
    return MDXFormatter()


@pytest.fixture
def docx_formatter():
    """Create DOCX formatter."""
    return DOCXFormatter()


@pytest.fixture
def file_repository(tmp_path):
    """Create file repository with temporary directory."""
    return FileRepository(tmp_path)


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory for tests."""
    output = tmp_path / "test_output"
    output.mkdir()
    return output


@pytest.fixture
def sample_blog_post():
    """Return sample blog post for testing."""
    return SAMPLE_BLOG_POST


@pytest.fixture
def sample_book():
    """Return sample book for testing."""
    return SAMPLE_BOOK


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (slower)")
    config.addinivalue_line("markers", "unit: mark test as unit test (faster)")
    config.addinivalue_line("markers", "requires_api: mark test as requiring real API key")
