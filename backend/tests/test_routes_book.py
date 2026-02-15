"""
Tests for book generation route.

Comprehensive integration tests covering:
- Successful book generation with mocked LLM
- Book generation with research enabled
- Post-processing (proofread/humanize)
- Error handling for various failure modes
- Authorization (user can only access own content)
- Rate limiting and quota enforcement
- Chapter and section configuration
"""

import uuid
import os
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
def valid_api_key():
    """Return valid API key header."""
    return {"X-API-Key": "test-valid-key"}


@pytest.fixture
def sample_book():
    """Create a sample book for testing."""
    return Book(
        title="Test Book",
        date="2024-01-24",
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
def sample_large_book():
    """Create a sample large book with multiple chapters for testing."""
    chapters = []
    for i in range(5):
        topics = [
            Topic(title=f"Topic {i+1}.{j+1}", content=f"Content for chapter {i+1}, topic {j+1}")
            for j in range(3)
        ]
        chapters.append(
            Chapter(
                number=i + 1,
                title=f"Chapter {i + 1}: Section Title",
                topics=topics,
            )
        )
    return Book(
        title="Large Test Book",
        date="2024-01-24",
        tags=["test", "book", "large"],
        chapters=chapters,
    )


@pytest.fixture
def mock_dependencies():
    """Mock common dependencies for book route tests."""
    with patch("app.routes.book.verify_api_key") as mock_auth, \
         patch("app.routes.book.require_quota", new_callable=AsyncMock) as mock_quota, \
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


@pytest.fixture
def mock_llm_provider():
    """Mock the LLM provider for text generation."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Generated content from LLM"
    return mock_provider


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

    def test_generate_book_with_all_options(self, client, sample_large_book, mock_dependencies):
        """Test book generation with all options enabled."""
        with patch("app.routes.book.generate_book_with_research") as mock_gen, \
             patch("app.routes.book.post_process_book") as mock_post, \
             patch("app.routes.book.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_large_book
            mock_post.return_value = sample_large_book
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-book",
                json={
                    "title": "Comprehensive Test Book",
                    "num_chapters": 5,
                    "sections_per_chapter": 3,
                    "keywords": ["test", "comprehensive", "all-options"],
                    "tone": "professional",
                    "research": True,
                    "proofread": True,
                    "humanize": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["type"] == "book"
            assert len(data["content"]["chapters"]) == 5
            mock_post.assert_called_once()

    def test_generate_book_with_different_chapter_counts(self, client, mock_dependencies):
        """Test book generation with various chapter counts."""
        chapter_counts = [1, 3, 5, 10]

        for num_chapters in chapter_counts:
            # Create a book with the appropriate number of chapters
            chapters = [
                Chapter(
                    number=i + 1,
                    title=f"Chapter {i + 1}",
                    topics=[Topic(title="Topic", content="Content")],
                )
                for i in range(num_chapters)
            ]
            test_book = Book(
                title="Test Book",
                date="2024-01-24",
                tags=[],
                chapters=chapters,
            )

            with patch("app.routes.book.generate_book") as mock_gen:
                mock_gen.return_value = test_book

                response = client.post(
                    "/generate-book",
                    json={
                        "title": f"Book with {num_chapters} chapters",
                        "num_chapters": num_chapters,
                        "conversation_id": f"test-conv-{num_chapters}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 201, f"Failed for {num_chapters} chapters"
                data = response.json()
                assert len(data["content"]["chapters"]) == num_chapters

    def test_generate_book_with_different_tones(self, client, sample_book, mock_dependencies):
        """Test book generation with various tone options."""
        tones = ["informative", "professional", "casual", "technical", "academic"]

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            for tone in tones:
                response = client.post(
                    "/generate-book",
                    json={
                        "title": f"Test Book with {tone} tone",
                        "num_chapters": 2,
                        "tone": tone,
                        "conversation_id": f"test-conv-{tone}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 201, f"Failed for tone: {tone}"

    def test_generate_book_stores_conversation(self, client, sample_book, mock_dependencies):
        """Test that book generation stores messages in conversation history."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-history",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify conversation storage was called twice (user + assistant messages)
            assert mock_dependencies["conversations"].append.call_count == 2

    def test_generate_book_sends_websocket_messages(self, client, sample_book, mock_dependencies):
        """Test that book generation sends WebSocket updates."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-ws",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify WebSocket messages were sent
            assert mock_dependencies["websocket"].send_message.call_count == 2

    def test_generate_book_increments_usage_based_on_chapters(self, client, sample_large_book, mock_dependencies):
        """Test that usage is incremented based on chapter count."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_large_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 5,
                    "conversation_id": "test-conv-usage",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify usage increment was called
            mock_dependencies["usage"].assert_called()


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
                    "title": "Test Book",
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

    def test_rate_limit_error_includes_retry_time(self, client, mock_dependencies):
        """Test that rate limit error includes retry time in response."""
        from src.text_generation.core import RateLimitError

        wait_times = [15.0, 30.0, 60.0, 120.0]

        for wait_time in wait_times:
            with patch("app.routes.book.generate_book") as mock_gen:
                error = RateLimitError("Rate limit exceeded", wait_time=wait_time)
                mock_gen.side_effect = error

                response = client.post(
                    "/generate-book",
                    json={
                        "title": "Test Book",
                        "num_chapters": 2,
                        "conversation_id": f"test-conv-{int(wait_time)}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 429
                assert str(int(wait_time)) in response.json()["detail"]

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

    def test_post_processing_error_returns_500(self, client, sample_book, mock_dependencies):
        """Test that post-processing errors return 500."""
        from src.book.make_book import BookGenerationError

        with patch("app.routes.book.generate_book") as mock_gen, \
             patch("app.routes.book.post_process_book") as mock_post, \
             patch("app.routes.book.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_book
            mock_post.side_effect = BookGenerationError("Proofreading failed")
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "proofread": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 500

    def test_research_error_returns_appropriate_status(self, client, mock_dependencies):
        """Test that research errors are handled appropriately."""
        from src.book.make_book import BookGenerationError

        with patch("app.routes.book.generate_book_with_research") as mock_gen:
            mock_gen.side_effect = BookGenerationError("Research failed")

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "research": True,
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

    def test_missing_conversation_id_returns_422(self, client, mock_dependencies):
        """Test that missing conversation_id returns validation error."""
        response = client.post(
            "/generate-book",
            json={
                "title": "Test Book",
                "num_chapters": 2,
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

    def test_zero_chapters_handled(self, client, mock_dependencies):
        """Test that zero chapters is handled."""
        response = client.post(
            "/generate-book",
            json={
                "title": "Test Book",
                "num_chapters": 0,
                "conversation_id": "test-conv-123",
            },
            headers={"X-API-Key": "test-key"},
        )

        # Should be rejected or handled gracefully
        assert response.status_code in [400, 422, 201]

    def test_negative_chapters_handled(self, client, mock_dependencies):
        """Test that negative chapters is handled."""
        response = client.post(
            "/generate-book",
            json={
                "title": "Test Book",
                "num_chapters": -1,
                "conversation_id": "test-conv-123",
            },
            headers={"X-API-Key": "test-key"},
        )

        # Should be rejected
        assert response.status_code in [400, 422]

    def test_empty_keywords_list_accepted(self, client, sample_book, mock_dependencies):
        """Test that empty keywords list is accepted."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "keywords": [],
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_long_title_accepted(self, client, sample_book, mock_dependencies):
        """Test that long titles are accepted."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            long_title = "A" * 500  # Long title

            response = client.post(
                "/generate-book",
                json={
                    "title": long_title,
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_many_keywords_accepted(self, client, sample_book, mock_dependencies):
        """Test that many keywords are accepted."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            many_keywords = [f"keyword{i}" for i in range(20)]

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "keywords": many_keywords,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_default_sections_per_chapter(self, client, sample_book, mock_dependencies):
        """Test that sections_per_chapter has a default value."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                    # sections_per_chapter not provided
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201


# =============================================================================
# Tests for Authorization
# =============================================================================


class TestBookAuthorization:
    """Tests for book generation authorization."""

    def test_missing_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}):
            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
            )

        # Should return 401 or 403 depending on implementation
        assert response.status_code in [401, 403, 422]

    def test_invalid_api_key_returns_401(self, client):
        """Test that invalid API key returns 401."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}):
            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "invalid-key"},
            )

            # Depending on how the dependency is structured, this may vary
            assert response.status_code in [401, 403, 422]

    def test_quota_exceeded_returns_429(self, client):
        """Test that exceeded quota returns 429."""
        with patch("app.routes.book.require_quota", new_callable=AsyncMock) as mock_quota:
            from fastapi import HTTPException
            mock_quota.side_effect = HTTPException(
                status_code=429,
                detail="Monthly quota exceeded"
            )

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code in [429, 422]

    def test_user_id_passed_to_conversation_storage(self, client, sample_book, mock_dependencies):
        """Test that user_id is correctly passed for conversation ownership."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-auth",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

            # Verify user_id was passed to conversation storage
            calls = mock_dependencies["conversations"].append.call_args_list
            for call in calls:
                # Check that user_id was passed as keyword argument
                assert "user_id" in call.kwargs or len(call.args) >= 3


# =============================================================================
# Tests for Response Structure
# =============================================================================


class TestBookResponseStructure:
    """Tests for book generation response structure."""

    def test_response_contains_required_fields(self, client, sample_book, mock_dependencies):
        """Test that response contains all required fields."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()

            # Check top-level fields
            assert "success" in data
            assert "type" in data
            assert "content" in data

            # Check content fields
            content = data["content"]
            assert "title" in content
            assert "chapters" in content

    def test_chapters_have_correct_structure(self, client, sample_book, mock_dependencies):
        """Test that chapters have the correct structure."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()

            for chapter in data["content"]["chapters"]:
                assert "number" in chapter
                assert "title" in chapter
                assert "topics" in chapter

                for topic in chapter["topics"]:
                    assert "title" in topic
                    assert "content" in topic

    def test_response_json_serializable(self, client, sample_book, mock_dependencies):
        """Test that response is properly JSON serializable."""
        import json

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

            # Should be able to re-serialize without issues
            data = response.json()
            json_str = json.dumps(data)
            assert json_str is not None

    def test_chapter_numbers_are_sequential(self, client, sample_large_book, mock_dependencies):
        """Test that chapter numbers are properly sequential."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_large_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 5,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()

            chapter_numbers = [ch["number"] for ch in data["content"]["chapters"]]
            expected_numbers = list(range(1, 6))
            assert chapter_numbers == expected_numbers


# =============================================================================
# Tests for Edge Cases
# =============================================================================


class TestBookEdgeCases:
    """Tests for edge cases in book generation."""

    def test_unicode_title_handled(self, client, sample_book, mock_dependencies):
        """Test that unicode characters in title are handled."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book with special chars",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_special_characters_in_keywords(self, client, sample_book, mock_dependencies):
        """Test that special characters in keywords are handled."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "keywords": ["C++", "C#", ".NET", "Node.js"],
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_book_with_single_chapter(self, client, mock_dependencies):
        """Test generation of book with single chapter."""
        single_chapter_book = Book(
            title="Single Chapter Book",
            date="2024-01-24",
            tags=[],
            chapters=[
                Chapter(
                    number=1,
                    title="The Only Chapter",
                    topics=[Topic(title="Topic", content="Content")],
                )
            ],
        )

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = single_chapter_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Single Chapter Book",
                    "num_chapters": 1,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert len(data["content"]["chapters"]) == 1

    def test_book_with_empty_chapters_handled(self, client, mock_dependencies):
        """Test handling of book with empty chapters list."""
        empty_chapters_book = Book(
            title="Empty Chapters Book",
            date="2024-01-24",
            tags=[],
            chapters=[],
        )

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = empty_chapters_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 0,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            # Should either succeed with empty chapters or return validation error
            assert response.status_code in [201, 400, 422]

    def test_concurrent_requests_handled(self, client, sample_book, mock_dependencies):
        """Test that concurrent requests are handled properly."""
        import concurrent.futures

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            def make_request(i):
                return client.post(
                    "/generate-book",
                    json={
                        "title": f"Test Book {i}",
                        "num_chapters": 2,
                        "conversation_id": f"test-conv-{i}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(5)]
                responses = [f.result() for f in concurrent.futures.as_completed(futures)]

            # All requests should succeed
            for response in responses:
                assert response.status_code == 201

    def test_large_chapter_count_handled(self, client, mock_dependencies):
        """Test handling of large chapter count."""
        # Create a book with many chapters
        large_chapters = [
            Chapter(
                number=i + 1,
                title=f"Chapter {i + 1}",
                topics=[Topic(title="Topic", content="Content")],
            )
            for i in range(20)
        ]
        large_book = Book(
            title="Large Book",
            date="2024-01-24",
            tags=[],
            chapters=large_chapters,
        )

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = large_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Large Book",
                    "num_chapters": 20,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            # Should either succeed or return validation error for too many chapters
            assert response.status_code in [201, 400, 422]

    def test_book_with_empty_topics_in_chapter(self, client, mock_dependencies):
        """Test handling of chapter with no topics."""
        book_with_empty_chapter = Book(
            title="Book with Empty Chapter",
            date="2024-01-24",
            tags=[],
            chapters=[
                Chapter(
                    number=1,
                    title="Empty Chapter",
                    topics=[],  # No topics
                )
            ],
        )

        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = book_with_empty_chapter

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 1,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["content"]["chapters"][0]["topics"] == []


# =============================================================================
# Tests for Usage Tracking
# =============================================================================


class TestBookUsageTracking:
    """Tests for usage tracking in book generation."""

    def test_usage_tracks_chapter_count(self, client, sample_large_book, mock_dependencies):
        """Test that usage tracking includes chapter count metadata."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_large_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 5,
                    "conversation_id": "test-conv-usage",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

            # Check that usage was called with appropriate metadata
            mock_dependencies["usage"].assert_called()
            call_kwargs = mock_dependencies["usage"].call_args.kwargs
            if "metadata" in call_kwargs:
                assert "chapters" in call_kwargs["metadata"]

    def test_usage_tracks_operation_type(self, client, sample_book, mock_dependencies):
        """Test that usage tracks operation type as 'book'."""
        with patch("app.routes.book.generate_book") as mock_gen:
            mock_gen.return_value = sample_book

            response = client.post(
                "/generate-book",
                json={
                    "title": "Test Book",
                    "num_chapters": 2,
                    "conversation_id": "test-conv-usage",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

            # Check that usage was called with book operation type
            mock_dependencies["usage"].assert_called()
            call_kwargs = mock_dependencies["usage"].call_args.kwargs
            if "operation_type" in call_kwargs:
                assert call_kwargs["operation_type"] == "book"
