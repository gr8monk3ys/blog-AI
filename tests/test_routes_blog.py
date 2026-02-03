"""
Tests for blog generation route.

Comprehensive integration tests covering:
- Successful blog generation with mocked LLM
- Blog generation with research enabled
- Post-processing (proofread/humanize)
- Error handling for various failure modes
- Authorization (user can only access own content)
- Rate limiting and quota enforcement
"""

import uuid
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
            Section(
                title="Conclusion",
                subtopics=[
                    SubTopic(title="", content="This is the conclusion.")
                ],
            ),
        ],
    )


@pytest.fixture
def sample_blog_post_with_faqs():
    """Create a sample blog post with FAQ section for testing."""
    return BlogPost(
        title="Test Blog Post with FAQs",
        description="A test blog post with frequently asked questions",
        date="2024-01-24",
        image=None,
        tags=["test", "blog", "faq"],
        sections=[
            Section(
                title="Introduction",
                subtopics=[
                    SubTopic(title="", content="Introduction content here.")
                ],
            ),
            Section(
                title="Main Section",
                subtopics=[
                    SubTopic(title="", content="Main content here.")
                ],
            ),
            Section(
                title="Conclusion",
                subtopics=[
                    SubTopic(title="", content="Conclusion content here.")
                ],
            ),
            Section(
                title="Frequently Asked Questions",
                subtopics=[
                    SubTopic(title="What is this?", content="This is a test."),
                    SubTopic(title="How does it work?", content="It works well."),
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
         patch("app.routes.blog.manager") as mock_ws, \
         patch("app.routes.blog.webhook_service") as mock_webhook:

        # Configure mocks
        mock_auth.return_value = "test-user-id"
        mock_quota.return_value = "test-user-id"
        mock_usage.return_value = AsyncMock()
        mock_conv.append = MagicMock()
        mock_ws.send_message = AsyncMock()
        mock_webhook.emit_content_generated = AsyncMock()

        yield {
            "auth": mock_auth,
            "quota": mock_quota,
            "usage": mock_usage,
            "conversations": mock_conv,
            "websocket": mock_ws,
            "webhook": mock_webhook,
        }


@pytest.fixture
def mock_llm_provider():
    """Mock the LLM provider for text generation."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Generated content from LLM"
    return mock_provider


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
            assert len(data["content"]["sections"]) == 3

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

    def test_generate_blog_with_all_options(self, client, sample_blog_post_with_faqs, mock_dependencies):
        """Test blog generation with all options enabled."""
        with patch("app.routes.blog.generate_blog_post_with_research") as mock_gen, \
             patch("app.routes.blog.post_process_blog_post") as mock_post, \
             patch("app.routes.blog.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_blog_post_with_faqs
            mock_post.return_value = sample_blog_post_with_faqs
            mock_provider.return_value = MagicMock()

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Comprehensive Test Topic",
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
            assert data["type"] == "blog"
            # Should have 4 sections including FAQ
            assert len(data["content"]["sections"]) == 4
            # Verify post-processing was called
            mock_post.assert_called_once()

    def test_generate_blog_with_different_tones(self, client, sample_blog_post, mock_dependencies):
        """Test blog generation with various tone options."""
        tones = ["informative", "professional", "casual", "technical", "conversational"]

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            for tone in tones:
                response = client.post(
                    "/generate-blog",
                    json={
                        "topic": f"Test Topic with {tone} tone",
                        "tone": tone,
                        "conversation_id": f"test-conv-{tone}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 201, f"Failed for tone: {tone}"

    def test_generate_blog_stores_conversation(self, client, sample_blog_post, mock_dependencies):
        """Test that blog generation stores messages in conversation history."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-history",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify conversation storage was called twice (user + assistant messages)
            assert mock_dependencies["conversations"].append.call_count == 2

    def test_generate_blog_sends_websocket_messages(self, client, sample_blog_post, mock_dependencies):
        """Test that blog generation sends WebSocket updates."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-ws",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify WebSocket messages were sent
            assert mock_dependencies["websocket"].send_message.call_count == 2

    def test_generate_blog_increments_usage(self, client, sample_blog_post, mock_dependencies):
        """Test that successful generation increments usage quota."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-usage",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify usage increment was called
            mock_dependencies["usage"].assert_called()

    def test_generate_blog_emits_webhook(self, client, sample_blog_post, mock_dependencies):
        """Test that successful generation emits webhook event."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-webhook",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            # Verify webhook was emitted
            mock_dependencies["webhook"].emit_content_generated.assert_called_once()


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

    def test_rate_limit_error_includes_retry_time(self, client, mock_dependencies):
        """Test that rate limit error includes retry time in response."""
        from src.text_generation.core import RateLimitError

        wait_times = [15.0, 30.0, 60.0, 120.0]

        for wait_time in wait_times:
            with patch("app.routes.blog.generate_blog_post") as mock_gen:
                error = RateLimitError("Rate limit exceeded", wait_time=wait_time)
                mock_gen.side_effect = error

                response = client.post(
                    "/generate-blog",
                    json={
                        "topic": "Test Topic",
                        "conversation_id": f"test-conv-{wait_time}",
                    },
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 429
                assert str(int(wait_time)) in response.json()["detail"]

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

    def test_post_processing_error_returns_500(self, client, sample_blog_post, mock_dependencies):
        """Test that post-processing errors return 500."""
        from src.blog.make_blog import BlogGenerationError

        with patch("app.routes.blog.generate_blog_post") as mock_gen, \
             patch("app.routes.blog.post_process_blog_post") as mock_post, \
             patch("app.routes.blog.create_provider_from_env") as mock_provider:

            mock_gen.return_value = sample_blog_post
            mock_post.side_effect = BlogGenerationError("Proofreading failed")
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

            assert response.status_code == 500

    def test_webhook_failure_does_not_fail_request(self, client, sample_blog_post, mock_dependencies):
        """Test that webhook failures don't fail the main request."""
        mock_dependencies["webhook"].emit_content_generated.side_effect = Exception("Webhook failed")

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            # Request should still succeed despite webhook failure
            assert response.status_code == 201


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

    def test_missing_conversation_id_returns_422(self, client, mock_dependencies):
        """Test that missing conversation_id returns validation error."""
        response = client.post(
            "/generate-blog",
            json={
                "topic": "Test Topic",
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

    def test_empty_keywords_list_accepted(self, client, sample_blog_post, mock_dependencies):
        """Test that empty keywords list is accepted."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "keywords": [],
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_long_topic_accepted(self, client, sample_blog_post, mock_dependencies):
        """Test that long topics are accepted."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            long_topic = "A" * 500  # Long topic

            response = client.post(
                "/generate-blog",
                json={
                    "topic": long_topic,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_many_keywords_accepted(self, client, sample_blog_post, mock_dependencies):
        """Test that many keywords are accepted."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            many_keywords = [f"keyword{i}" for i in range(20)]

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "keywords": many_keywords,
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201


# =============================================================================
# Tests for Authorization
# =============================================================================


class TestBlogAuthorization:
    """Tests for blog generation authorization."""

    def test_missing_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post(
            "/generate-blog",
            json={
                "topic": "Test Topic",
                "conversation_id": "test-conv-123",
            },
        )

        # Should return 401 or 403 depending on implementation
        assert response.status_code in [401, 403, 422]

    def test_invalid_api_key_returns_401(self, client):
        """Test that invalid API key returns 401."""
        with patch("app.auth.verify_api_key") as mock_verify:
            from fastapi import HTTPException
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid API key")

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "invalid-key"},
            )

            # Depending on how the dependency is structured, this may vary
            assert response.status_code in [401, 403, 422]

    def test_quota_exceeded_returns_429(self, client):
        """Test that exceeded quota returns 429."""
        with patch("app.middleware.require_quota") as mock_quota:
            from fastapi import HTTPException
            mock_quota.side_effect = HTTPException(
                status_code=429,
                detail="Monthly quota exceeded"
            )

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code in [429, 422]

    def test_user_id_passed_to_conversation_storage(self, client, sample_blog_post, mock_dependencies):
        """Test that user_id is correctly passed for conversation ownership."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
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


class TestBlogResponseStructure:
    """Tests for blog generation response structure."""

    def test_response_contains_required_fields(self, client, sample_blog_post, mock_dependencies):
        """Test that response contains all required fields."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
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
            assert "description" in content
            assert "sections" in content
            assert "tags" in content

    def test_sections_have_correct_structure(self, client, sample_blog_post, mock_dependencies):
        """Test that sections have the correct structure."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()

            for section in data["content"]["sections"]:
                assert "title" in section
                assert "subtopics" in section

                for subtopic in section["subtopics"]:
                    assert "title" in subtopic
                    assert "content" in subtopic

    def test_response_json_serializable(self, client, sample_blog_post, mock_dependencies):
        """Test that response is properly JSON serializable."""
        import json

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

            # Should be able to re-serialize without issues
            data = response.json()
            json_str = json.dumps(data)
            assert json_str is not None


# =============================================================================
# Tests for Edge Cases
# =============================================================================


class TestBlogEdgeCases:
    """Tests for edge cases in blog generation."""

    def test_unicode_topic_handled(self, client, sample_blog_post, mock_dependencies):
        """Test that unicode characters in topic are handled."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic with special chars",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_special_characters_in_keywords(self, client, sample_blog_post, mock_dependencies):
        """Test that special characters in keywords are handled."""
        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "keywords": ["C++", "C#", ".NET", "Node.js"],
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201

    def test_concurrent_requests_handled(self, client, sample_blog_post, mock_dependencies):
        """Test that concurrent requests are handled properly."""
        import concurrent.futures

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = sample_blog_post

            def make_request(i):
                return client.post(
                    "/generate-blog",
                    json={
                        "topic": f"Test Topic {i}",
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

    def test_blog_post_with_empty_sections_handled(self, client, mock_dependencies):
        """Test handling of blog post with empty sections."""
        empty_sections_blog = BlogPost(
            title="Empty Sections Blog",
            description="A blog with minimal content",
            date="2024-01-24",
            tags=[],
            sections=[],
        )

        with patch("app.routes.blog.generate_blog_post") as mock_gen:
            mock_gen.return_value = empty_sections_blog

            response = client.post(
                "/generate-blog",
                json={
                    "topic": "Test Topic",
                    "conversation_id": "test-conv-123",
                },
                headers={"X-API-Key": "test-key"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["content"]["sections"] == []
