"""
Pytest configuration and shared fixtures for Blog AI tests.

This module provides common fixtures used across all test files:
- Test client setup
- Mock configurations for external services
- Sample data generators
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Environment setup before any imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
# Set a mock API key to satisfy config validation (tests mock actual calls)
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    from fastapi.testclient import TestClient
    from server import app

    return TestClient(app)


@pytest.fixture
def async_client():
    """Async FastAPI test client fixture."""
    from httpx import ASGITransport, AsyncClient
    from server import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("src.text_generation.core.OpenAI") as mock:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Generated content"))]
        )
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API calls."""
    with patch("src.text_generation.core.Anthropic") as mock:
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Generated content")]
        )
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch("stripe.checkout.Session") as session_mock, \
         patch("stripe.Account") as account_mock:
        account_mock.retrieve.return_value = MagicMock(id="acct_test123")
        yield {"session": session_mock, "account": account_mock}


@pytest.fixture
def mock_supabase():
    """Mock Supabase database calls."""
    with patch("supabase.create_client") as mock:
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"tier": "free"}]
        )
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client calls."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.info.return_value = {"redis_version": "7.0.0"}

    with patch("src.storage.redis_client", mock_client):
        yield mock_client


@pytest.fixture
def mock_sentry():
    """Mock Sentry SDK."""
    with patch("sentry_sdk.capture_exception") as capture_mock, \
         patch("sentry_sdk.get_client") as client_mock:
        mock_client = MagicMock()
        mock_client.is_active.return_value = True
        client_mock.return_value = mock_client
        yield {"capture": capture_mock, "client": client_mock}


@pytest.fixture
def sample_blog_request():
    """Sample blog generation request data."""
    return {
        "topic": "Introduction to Machine Learning",
        "keywords": ["AI", "machine learning", "data science"],
        "tone": "informative",
        "num_sections": 3,
        "conversation_id": "test-conv-123",
    }


@pytest.fixture
def sample_book_request():
    """Sample book generation request data."""
    return {
        "title": "Understanding AI",
        "chapters": 3,
        "sections_per_chapter": 2,
        "conversation_id": "test-book-456",
    }


@pytest.fixture
def sample_export_request():
    """Sample export request data."""
    return {
        "title": "Test Article",
        "content": "# Test\n\nThis is test content with **bold** and *italic* text.",
        "content_type": "blog",
        "metadata": {"author": "Test Author"},
    }


@pytest.fixture
def sample_blog_content():
    """Sample blog content for testing."""
    return {
        "title": "Test Blog Post",
        "description": "This is a test blog post",
        "sections": [
            {
                "title": "Introduction",
                "subtopics": [{"title": "", "content": "Introduction content here."}],
            },
            {
                "title": "Main Section",
                "subtopics": [{"title": "", "content": "Main content here."}],
            },
        ],
        "tags": ["test", "blog"],
    }


@pytest.fixture
def mock_cache():
    """Mock cache utilities."""
    mock_content_cache = MagicMock()
    mock_content_cache.stats = {"hits": 10, "misses": 5, "size": 15}
    mock_content_cache.cleanup_expired.return_value = 2

    mock_voice_cache = MagicMock()
    mock_voice_cache.stats = {"hits": 5, "misses": 2, "size": 7}
    mock_voice_cache.cleanup_expired.return_value = 1

    with patch("src.utils.cache.get_content_analysis_cache", return_value=mock_content_cache), \
         patch("src.utils.cache.get_voice_analysis_cache", return_value=mock_voice_cache):
        yield {"content": mock_content_cache, "voice": mock_voice_cache}


# Test environment cleanup
@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
