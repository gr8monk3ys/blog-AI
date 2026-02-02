"""
Tests for book generation route.

Tests cover:
- Successful book generation
- Book generation with research
- Post-processing (proofread/humanize)
- Error handling for various failure modes
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.types.content import Book, Chapter, Topic


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create test client."""
    from server import app
    return TestClient(app)


@pytest.fixture
def sample_book():
    """Create a sample book for testing."""
    return Book(
        title="Test Book",
        description="A test book description",
        date="2024-01-24",
        image=None,
        tags=["test", "book"],
        chapters=[
            Chapter(
                number=1,
                title="Chapter 1: Introduction",
                topics=[
                    Topic(title="Topic 1.1", content="Content for topic 1.1"),
                    Topic(title="Topic 1.2", content="Content for topic 1.2"),
                ],
            ),
            Chapter(
                number=2,
                title="Chapter 2: Main Content",
                topics=[
                    Topic(title="Topic 2.1", content="Content for topic 2.1"),
                ],
            ),
        ],
    )


@pytest.fixture
def mock_dependencies():
    """Mock common dependencies for book route tests."""
    with patch("app.routes.book.verify_api_key") as mock_auth, \
         patch("app.routes.book.require_quota") as mock_quota, \
         patch("app.routes.book.increment_usage_for_operation") as mock_usage, \
         patch("app.routes.book.conversations") as mock_conv, \
         patch("app.routes.book.manager") as mock_ws:

        mock_auth.return_value = "test-user-id"
        mock_quota.return_value = "test-user-id"
        mock_usage.return_value = AsyncMock()
        mock_conv.append = MagicMock()
        mock_ws.send_message = AsyncMock()

        yield {
            "auth": mock_auth,
            "quota": mock_quota,
            "usage": mock_usage,
            "conversations": mock_conv,
            "websocket": mock_ws,
        }


# =============================================================================
# Tests for Successful Book Generation
# =============================================================================


class TestBookGenerationSuccess:
    """Tests for successful book generation."""

    def test_generate_book_basic(self, client, sample_book, mock_dependencies):
        """Test basic book generation."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book Title",
                    "num_chapters": 2,
                    "sections_per_chapter": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["type"] == "book"
            assert data["content"]["title"] == "Test Book"
            assert len(data["content"]["chapters"]) == 2

    def test_generate_book_with_research(self, client, sample_book, mock_dependencies):
        """Test book generation with research enabled."""
        with patch("app.routes.book.generate_book_with_research") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 3,
                    "research": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            mock_gen.assert_called_once()

    def test_generate_book_with_post_processing(self, client, sample_book, mock_dependencies):
        """Test book generation with post-processing."""
        with patch("app.routes.book.generate_book") as mock_gen, \
             patch("app.routes.book.post_process_book") as mock_post, \
             patch("app.routes.book.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_book
            mock_post.return_value = sample_book
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "proofread": True,
                    "humanize": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            mock_post.assert_called_once()

    def test_generate_book_with_keywords_and_tone(self, client, sample_book, mock_dependencies):
        """Test book generation with keywords and tone."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "keywords": ["AI", "ML", "tech"],
                    "tone": "technical",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201


# =============================================================================
# Tests for Error Handling
# =============================================================================


class TestBookGenerationErrors:
    """Tests for book generation error handling."""

    def test_validation_error_returns_400(self, client, mock_dependencies):
        """Test that validation errors return 400."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.side_effect = ValueError("Invalid title")

            response = client.post(
                "/generate-book",
                json={
                    "title": "",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 400

    def test_rate_limit_error_returns_429(self, client, mock_dependencies):
        """Test that rate limit errors return 429."""
        from src.text_generation.core import RateLimitError

        with patch("app.routes.book.generate_book") as mock_gen:
            error = RateLimitError("Rate limit exceeded", wait_time=60.0)
            mock_gen.side_effect = error

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 429

    def test_text_generation_error_returns_502(self, client, mock_dependencies):
        """Test that text generation errors return 502."""
        from src.text_generation.core import TextGenerationError

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.side_effect = TextGenerationError("Provider error")

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 502

    def test_book_generation_error_returns_500(self, client, mock_dependencies):
        """Test that book generation errors return 500."""
        from src.book.make_book import BookGenerationError

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.side_effect = BookGenerationError("Book creation failed")

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 500

    def test_unexpected_error_returns_500(self, client, mock_dependencies):
        """Test that unexpected errors return 500."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.side_effect = RuntimeError("Unexpected error")

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 500


# =============================================================================
# Tests for Request Validation
# =============================================================================


class TestBookRequestValidation:
    """Tests for book request validation."""

    def test_missing_title_returns_422(self, client, mock_dependencies):
        """Test that missing title returns validation error."""
        response = client.post(
            "/generate-book",
            json={
                "num_chapters": 2,
                "conversation_id": "test-conv-123",
            },
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 422

    def test_invalid_chapter_count_handled(self, client, sample_book, mock_dependencies):
        """Test that chapter count validation works."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            # Test with minimum chapters
            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 1,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code in [201, 422]
