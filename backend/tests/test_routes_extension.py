"""
Route-level regression tests for the Chrome Extension API endpoints.

These tests exercise API behavior (status codes + payloads) for:
- POST /api/v1/extension/auth   -- API key validation
- GET  /api/v1/extension/user   -- user info + quota
- GET  /api/v1/extension/usage  -- usage statistics
- POST /api/v1/extension/generate -- content generation (blog, outline, summary, expand)

Mocking strategy: we patch `api_key_store.verify_key`, `get_usage_stats`,
generation helpers, and `increment_usage_for_operation` so that tests never
touch real storage, LLMs, or network.

The generate endpoint uses `Depends(require_pro_tier)` which internally calls
`service_get_usage_stats` from the quota_check middleware, so we must patch
BOTH `app.routes.extension.get_usage_stats` (used inside the route handler)
AND `app.middleware.quota_check.service_get_usage_stats` (used by the
require_pro_tier dependency).
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Environment setup (must happen before any app import)
# ---------------------------------------------------------------------------
os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.text_generation.core import RateLimitError
from src.types.usage import SubscriptionTier, UsageStats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Patch targets used throughout the tests
_ROUTE_USAGE = "app.routes.extension.get_usage_stats"
_MIDDLEWARE_USAGE = "app.middleware.quota_check.service_get_usage_stats"
_ROUTE_INCREMENT = "app.routes.extension.increment_usage_for_operation"


def _make_usage_stats(
    user_id: str = "user_ext_test",
    tier: SubscriptionTier = SubscriptionTier.PRO,
    current_usage: int = 10,
    quota_limit: int = 200,
    remaining: int = 190,
    tokens_used: int = 5000,
) -> UsageStats:
    """Build a realistic UsageStats fixture."""
    now = datetime.now(timezone.utc)
    return UsageStats(
        user_id=user_id,
        tier=tier,
        current_usage=current_usage,
        quota_limit=quota_limit,
        remaining=remaining,
        daily_usage=3,
        daily_limit=50,
        daily_remaining=47,
        reset_date=now,
        period_start=now,
        tokens_used=tokens_used,
    )


def detail_text(response) -> str:
    """Normalize API error detail into a lowercase string for assertions."""
    detail = response.json().get("detail")
    if isinstance(detail, dict):
        return str(detail.get("error", detail)).lower()
    return str(detail).lower()


# ============================================================================
# POST /api/v1/extension/auth
# ============================================================================


class TestExtensionAuthRoute(unittest.TestCase):
    """Tests for POST /api/v1/extension/auth."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(
        _ROUTE_USAGE,
        new_callable=AsyncMock,
        return_value=_make_usage_stats(),
    )
    @patch(
        "app.routes.extension.api_key_store.verify_key",
        return_value="user_ext_test",
    )
    def test_auth_valid_key_returns_200(self, _mock_verify, _mock_usage):
        """Valid API key must return 200 with success=True, user_id, tier, email."""
        response = self.client.post(
            "/api/v1/extension/auth",
            json={"api_key": "valid-key-abc123"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user_id"], "user_ext_test")
        self.assertIsInstance(data["tier"], str)
        self.assertIsNone(data["email"])

    @patch(
        "app.routes.extension.api_key_store.verify_key",
        return_value=None,
    )
    def test_auth_invalid_key_returns_401(self, _mock_verify):
        """Invalid API key must return 401."""
        response = self.client.post(
            "/api/v1/extension/auth",
            json={"api_key": "bad-key"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid", detail_text(response))

    def test_auth_missing_body_returns_422(self):
        """Empty body (missing required api_key) must return 422."""
        response = self.client.post(
            "/api/v1/extension/auth",
            json={},
        )
        self.assertEqual(response.status_code, 422)

    def test_auth_empty_api_key_returns_422(self):
        """Empty-string api_key violates min_length=1 and must return 422."""
        response = self.client.post(
            "/api/v1/extension/auth",
            json={"api_key": ""},
        )
        self.assertEqual(response.status_code, 422)


# ============================================================================
# GET /api/v1/extension/user
# ============================================================================


class TestExtensionUserRoute(unittest.TestCase):
    """Tests for GET /api/v1/extension/user."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(
        _ROUTE_USAGE,
        new_callable=AsyncMock,
        return_value=_make_usage_stats(),
    )
    def test_user_with_auth_returns_200(self, _mock_usage):
        """Authenticated request must return 200 with quota fields."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.get("/api/v1/extension/user")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("user_id", data)
        self.assertIn("tier", data)
        # All quota fields must be present and numeric
        for field in ("quota_used", "quota_limit", "quota_remaining"):
            self.assertIn(field, data)
            self.assertIsInstance(data[field], (int, float))

    def test_user_without_auth_returns_401(self):
        """Request without auth must return 401."""
        response = self.client.get("/api/v1/extension/user")
        self.assertEqual(response.status_code, 401)

    @patch(
        _ROUTE_USAGE,
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    )
    def test_user_internal_error_returns_500(self, _mock_usage):
        """Internal errors must return 500."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.get("/api/v1/extension/user")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve user information", detail_text(response))


# ============================================================================
# GET /api/v1/extension/usage
# ============================================================================


class TestExtensionUsageRoute(unittest.TestCase):
    """Tests for GET /api/v1/extension/usage."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(
        _ROUTE_USAGE,
        new_callable=AsyncMock,
        return_value=_make_usage_stats(),
    )
    def test_usage_with_auth_returns_200(self, _mock_usage):
        """Authenticated request must return 200 with usage statistics."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.get("/api/v1/extension/usage")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        # reset_date must be a string (ISO format)
        self.assertIn("reset_date", data)
        self.assertIsInstance(data["reset_date"], str)
        # Numeric counts
        for field in ("generations_used", "generations_limit", "generations_remaining", "tokens_used"):
            self.assertIn(field, data)
            self.assertIsInstance(data[field], (int, float))

    def test_usage_without_auth_returns_401(self):
        """Request without auth must return 401."""
        response = self.client.get("/api/v1/extension/usage")
        self.assertEqual(response.status_code, 401)

    @patch(
        _ROUTE_USAGE,
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    )
    def test_usage_internal_error_returns_500(self, _mock_usage):
        """Internal errors must return 500."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.get("/api/v1/extension/usage")
        self.assertEqual(response.status_code, 500)
        self.assertIn("failed to retrieve usage statistics", detail_text(response))


# ============================================================================
# POST /api/v1/extension/generate  --  action=summary
# ============================================================================


class TestExtensionGenerateSummary(unittest.TestCase):
    """Tests for POST /api/v1/extension/generate with action=summary."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(_ROUTE_INCREMENT, new_callable=AsyncMock)
    @patch(
        "app.routes.extension.generate_text",
        return_value="This is a concise summary of the text.",
    )
    @patch(
        "app.routes.extension.create_provider_from_env",
        return_value=MagicMock(),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_summary_returns_200_with_content(
        self, _mock_mw_usage, _mock_usage, _mock_provider, _mock_gen, _mock_incr
    ):
        """action=summary with valid auth must return 200 with data.content as a string."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={
                "topic": "Some text that needs to be summarized for testing purposes.",
                "action": "summary",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("content", data["data"])
        self.assertIsInstance(data["data"]["content"], str)
        self.assertTrue(len(data["data"]["content"]) > 0)


# ============================================================================
# POST /api/v1/extension/generate  --  action=outline
# ============================================================================


class TestExtensionGenerateOutline(unittest.TestCase):
    """Tests for POST /api/v1/extension/generate with action=outline."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(_ROUTE_INCREMENT, new_callable=AsyncMock)
    @patch("app.routes.extension.generate_content_outline")
    @patch(
        "app.routes.extension.create_provider_from_env",
        return_value=MagicMock(),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_outline_returns_200_with_sections(
        self, _mock_mw_usage, _mock_usage, _mock_provider, mock_outline, _mock_incr
    ):
        """action=outline with valid auth must return 200 with data.sections as a list."""
        # Build a mock outline object with sections
        mock_subtopic = MagicMock()
        mock_subtopic.title = "Subtopic 1"
        mock_subtopic.description = "Description of subtopic"

        mock_section = MagicMock()
        mock_section.title = "Section 1"
        mock_section.subtopics = [mock_subtopic]

        mock_outline_result = MagicMock()
        mock_outline_result.sections = [mock_section]
        mock_outline.return_value = mock_outline_result

        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={
                "topic": "How to test Chrome extensions",
                "action": "outline",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("sections", data["data"])
        self.assertIsInstance(data["data"]["sections"], list)
        self.assertTrue(len(data["data"]["sections"]) > 0)


# ============================================================================
# POST /api/v1/extension/generate  --  auth + validation
# ============================================================================


class TestExtensionGenerateAuth(unittest.TestCase):
    """Auth and validation tests for POST /api/v1/extension/generate."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    def test_generate_without_auth_returns_401(self):
        """Request without auth must return 401."""
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"topic": "Test topic", "action": "summary"},
        )
        self.assertEqual(response.status_code, 401)

    @patch(
        _MIDDLEWARE_USAGE,
        new_callable=AsyncMock,
        return_value=_make_usage_stats(tier=SubscriptionTier.FREE),
    )
    def test_generate_free_tier_returns_403(self, _mock_usage):
        """Free-tier user must be rejected with 403 (requires pro tier)."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"topic": "Test topic", "action": "summary"},
        )
        self.assertEqual(response.status_code, 403)

    def test_generate_empty_body_returns_error(self):
        """Empty body must return validation error (422) or tier gate (401/403)."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={},
        )
        self.assertIn(response.status_code, (403, 422))

    def test_generate_missing_topic_returns_422(self):
        """Missing required 'topic' field must return 422."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"action": "summary"},
        )
        # Either 422 (validation) or 403 (tier gate checked first)
        self.assertIn(response.status_code, (403, 422))


# ============================================================================
# POST /api/v1/extension/generate  --  action=blog
# ============================================================================


class TestExtensionGenerateBlog(unittest.TestCase):
    """Tests for POST /api/v1/extension/generate with action=blog."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(_ROUTE_INCREMENT, new_callable=AsyncMock)
    @patch("app.routes.extension.post_process_blog_post")
    @patch("app.routes.extension.generate_blog_post")
    @patch(
        "app.routes.extension.create_provider_from_env",
        return_value=MagicMock(),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_blog_returns_200_with_sections(
        self, _mock_mw_usage, _mock_usage, _mock_provider, mock_gen_blog, mock_post_process, _mock_incr
    ):
        """action=blog with valid auth must return 200 with blog data."""
        # Build mock blog post
        mock_subtopic = MagicMock()
        mock_subtopic.title = "Subtopic"
        mock_subtopic.content = "Content here."

        mock_section = MagicMock()
        mock_section.title = "Section"
        mock_section.subtopics = [mock_subtopic]

        mock_blog = MagicMock()
        mock_blog.title = "Test Blog"
        mock_blog.description = "A test blog post"
        mock_blog.date = "2026-02-22"
        mock_blog.tags = ["testing"]
        mock_blog.sections = [mock_section]

        mock_gen_blog.return_value = mock_blog
        mock_post_process.return_value = mock_blog

        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={
                "topic": "How to write tests",
                "action": "blog",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("sections", data["data"])
        self.assertIsInstance(data["data"]["sections"], list)
        self.assertIn("title", data["data"])


# ============================================================================
# POST /api/v1/extension/generate  --  action=expand
# ============================================================================


class TestExtensionGenerateExpand(unittest.TestCase):
    """Tests for POST /api/v1/extension/generate with action=expand."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)

    @patch(_ROUTE_INCREMENT, new_callable=AsyncMock)
    @patch(
        "app.routes.extension.generate_text",
        return_value="Expanded content paragraph one.\n\nParagraph two with details.",
    )
    @patch(
        "app.routes.extension.create_provider_from_env",
        return_value=MagicMock(),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_expand_returns_200_with_sections(
        self, _mock_mw_usage, _mock_usage, _mock_provider, _mock_gen, _mock_incr
    ):
        """action=expand with valid auth must return 200 with sections."""
        self.client.headers.update({"X-API-Key": "test-key"})
        response = self.client.post(
            "/api/v1/extension/generate",
            json={
                "topic": "Short text to expand.",
                "action": "expand",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("sections", data["data"])
        self.assertIsInstance(data["data"]["sections"], list)


# ============================================================================
# POST /api/v1/extension/generate  --  error handling
# ============================================================================


class TestExtensionGenerateErrorHandling(unittest.TestCase):
    """Error-handling tests for POST /api/v1/extension/generate."""

    def setUp(self):
        from server import app

        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    @patch(
        "app.routes.extension._generate_summary",
        new_callable=AsyncMock,
        side_effect=Exception("unexpected"),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_generate_unexpected_error_returns_500(self, _mock_mw_usage, _mock_usage, _mock_gen):
        """Unexpected errors during generation must return 500."""
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"topic": "Test topic", "action": "summary"},
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("unexpected error", detail_text(response))

    @patch(
        "app.routes.extension._generate_summary",
        new_callable=AsyncMock,
        side_effect=ValueError("Bad input"),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_generate_value_error_returns_400(self, _mock_mw_usage, _mock_usage, _mock_gen):
        """ValueError during generation must return 400."""
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"topic": "Test topic", "action": "summary"},
        )
        self.assertEqual(response.status_code, 400)

    @patch(
        "app.routes.extension._generate_summary",
        new_callable=AsyncMock,
        side_effect=RateLimitError("rate limited"),
    )
    @patch(_ROUTE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    @patch(_MIDDLEWARE_USAGE, new_callable=AsyncMock, return_value=_make_usage_stats())
    def test_generate_rate_limit_returns_429(self, _mock_mw_usage, _mock_usage, _mock_gen):
        """RateLimitError during generation must return 429."""
        response = self.client.post(
            "/api/v1/extension/generate",
            json={"topic": "Test topic", "action": "summary"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit", detail_text(response))


if __name__ == "__main__":
    unittest.main()
