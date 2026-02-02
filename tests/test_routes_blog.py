"""
Tests for blog generation route.

Tests cover:
- Successful blog generation
- Blog generation with research
- Post-processing (proofread/humanize)
- Error handling for various failure modes
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.types.content import BlogPost, Section, SubTopic


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
def sample_blog_post():
    """Create a sample blog post for testing."""
    return BlogPost(
        title="Test Blog Post",
        description="A test blog post description",
        date="2024-01-24",
        image=None,
        tags=["test", "blog"],
        sections=[
            Section(
                title="Introduction",
                subtopics=[
                    SubTopic(title="Overview", content="This is the overview content.")
                ],
            ),
            Section(
                title="Main Content",
                subtopics=[
                    SubTopic(title="Topic 1", content="Content for topic 1.")
                ],
            ),
        ],
    )


@pytest.fixture
def mock_dependencies():
    """Mock common dependencies for blog route tests."""
    with patch("app.routes.blog.verify_api_key") as mock_auth, \
         patch("app.routes.blog.require_quota") as mock_quota, \
         patch("app.routes.blog.increment_usage_for_operation") as mock_usage, \
         patch("app.routes.blog.conversations") as mock_conv, \
         patch("app.routes.blog.manager") as mock_ws:

        # Configure mocks
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
# Tests for Successful Blog Generation
# =============================================================================


class TestBlogGenerationSuccess:
    """Tests for successful blog generation."""

    def test_generate_blog_basic(self, client, sample_blog_post, mock_dependencies):
        """Test basic blog generation without options."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "keywords": ["test", "blog"],
                    "tone": "informative",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["type"] == "blog"
            assert data["content"]["title"] == "Test Blog Post"
            assert len(data["content"]["sections"]) == 2

    def test_generate_blog_with_research(self, client, sample_blog_post, mock_dependencies):
        """Test blog generation with research enabled."""
        with patch("app.routes.blog.generate_blog_post_with_research") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "research": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            mock_gen.assert_called_once()

    def test_generate_blog_with_proofread(self, client, sample_blog_post, mock_dependencies):
        """Test blog generation with proofreading."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen, \
             patch("app.routes.blog.post_process_blog_post") as mock_post, \
             patch("app.routes.blog.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_blog_post
            mock_post.return_value = sample_blog_post
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "proofread": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            mock_post.assert_called_once()

    def test_generate_blog_with_humanize(self, client, sample_blog_post, mock_dependencies):
        """Test blog generation with humanization."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen, \
             patch("app.routes.blog.post_process_blog_post") as mock_post, \
             patch("app.routes.blog.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_blog_post
            mock_post.return_value = sample_blog_post
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "humanize": True,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201


# =============================================================================
# Tests for Error Handling
# =============================================================================


class TestBlogGenerationErrors:
    """Tests for blog generation error handling."""

    def test_validation_error_returns_400(self, client, mock_dependencies):
        """Test that validation errors return 400."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.side_effect = ValueError("Invalid topic length")

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "",  # Invalid empty topic
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 400

    def test_rate_limit_error_returns_429(self, client, mock_dependencies):
        """Test that rate limit errors return 429."""
        from src.text_generation.core import RateLimitError

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            error = RateLimitError("Rate limit exceeded", wait_time=30.0)
            mock_gen.side_effect = error

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 429
            assert "30" in response.json()["detail"]

    def test_text_generation_error_returns_502(self, client, mock_dependencies):
        """Test that text generation errors return 502."""
        from src.text_generation.core import TextGenerationError

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.side_effect = TextGenerationError("Provider error")

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 502
            assert "AI provider" in response.json()["detail"]

    def test_blog_generation_error_returns_500(self, client, mock_dependencies):
        """Test that blog generation errors return 500."""
        from src.blog.make_blog import BlogGenerationError

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.side_effect = BlogGenerationError("Blog creation failed")

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 500

    def test_unexpected_error_returns_500(self, client, mock_dependencies):
        """Test that unexpected errors return 500."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.side_effect = RuntimeError("Unexpected error")

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 500


# =============================================================================
# Tests for Request Validation
# =============================================================================


class TestBlogRequestValidation:
    """Tests for blog request validation."""

    def test_missing_topic_returns_422(self, client, mock_dependencies):
        """Test that missing topic returns validation error."""
        response = client.post(
            "/generate-blog",
            json={
                "conversation_id": "test-conv-123",
            },
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 422

    def test_invalid_tone_handled(self, client, sample_blog_post, mock_dependencies):
        """Test that invalid tone is handled gracefully."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "tone": "invalid_tone",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            # Should still work or return validation error
            assert response.status_code in [201, 422]
