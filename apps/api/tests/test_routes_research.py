"""Tests for research API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.research import router
from app.dependencies.authorization import require_content_creation
from src.types.research import (
    CredibilityTier,
    DeepResearchResult,
    QualityRatedSource,
    ResearchDepth,
    SourceQuality,
)


def _mock_auth_ctx():
    ctx = MagicMock()
    ctx.user_id = "test-user-123"
    ctx.organization_id = None
    return ctx


@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1")
    _app.dependency_overrides[require_content_creation] = _mock_auth_ctx
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestResearchEndpoint:
    @patch("app.routes.research.save_research", new_callable=AsyncMock)
    @patch("app.routes.research.get_cached_research", new_callable=AsyncMock)
    @patch("app.routes.research.conduct_deep_research")
    def test_basic_research(self, mock_conduct, mock_cache, mock_save, client):
        mock_cache.return_value = None
        mock_save.return_value = "query-123"

        source = QualityRatedSource(
            title="Test Source",
            url="https://example.com",
            snippet="Test snippet",
            provider="google",
            quality=SourceQuality(
                domain_authority=50,
                recency=60,
                relevance=70,
                credibility_tier=CredibilityTier.MEDIUM,
                overall=58,
            ),
        )
        mock_conduct.return_value = DeepResearchResult(
            query="test",
            depth=ResearchDepth.BASIC,
            sources=[source],
            summary="Test summary",
            total_sources_found=1,
            sources_after_quality_filter=1,
        )

        response = client.post(
            "/api/v1/research",
            json={"query": "test topic", "depth": "basic"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["sources"]) == 1

    @patch("app.routes.research.get_cached_research", new_callable=AsyncMock)
    def test_cached_result(self, mock_cache, client):
        mock_cache.return_value = {
            "id": "cached-1",
            "query": "test",
            "depth": "basic",
            "sources": [],
            "summary": "",
            "total_sources": 0,
        }

        response = client.post(
            "/api/v1/research",
            json={"query": "test", "depth": "basic"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True

    def test_invalid_depth(self, client):
        response = client.post(
            "/api/v1/research",
            json={"query": "test", "depth": "invalid"},
        )
        assert response.status_code == 400


class TestResearchHistory:
    @patch("app.routes.research.list_research_history", new_callable=AsyncMock)
    def test_list_history(self, mock_list, client):
        mock_list.return_value = [
            {"id": "q1", "query": "AI", "depth": "basic", "total_sources": 3, "summary": "", "created_at": None},
        ]

        response = client.get("/api/v1/research/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
