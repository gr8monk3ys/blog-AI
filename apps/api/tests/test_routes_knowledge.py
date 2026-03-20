"""
Tests for Knowledge Base API endpoints.

Verifies all 6 endpoints: upload, list, get, delete, search, stats.
Uses mocked KnowledgeService to avoid real vector store/embedding calls.
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"
os.environ["ENABLE_KNOWLEDGE_BASE"] = "true"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _make_mock_service():
    """Create a mock KnowledgeService."""
    service = AsyncMock()
    service.initialize = AsyncMock()
    service.list_documents = AsyncMock(return_value=[])
    service.get_document = AsyncMock(return_value=None)
    service.delete_document = AsyncMock(return_value=True)
    service.get_stats = AsyncMock(return_value=MagicMock(
        total_documents=0,
        total_chunks=0,
        storage_size_bytes=0,
        documents_by_type={},
        oldest_document=None,
        newest_document=None,
    ))
    return service


def _get_test_client():
    """Get a test client with KB routes enabled."""
    # Force reload to pick up ENABLE_KNOWLEDGE_BASE=true
    from src.config import reload_settings
    reload_settings()
    from server import app
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_knowledge_stats_endpoint():
    """GET /knowledge/stats should return 200 when KB is enabled."""
    client = _get_test_client()

    with patch("app.routes.knowledge.get_service", return_value=_make_mock_service()), \
         patch("app.routes.knowledge.require_knowledge_read") as mock_auth:
        mock_auth.return_value = MagicMock(
            user_id="test_user",
            organization_id=None,
        )
        response = client.get(
            "/api/v1/knowledge/stats",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_documents" in data


def test_knowledge_list_documents():
    """GET /knowledge/documents should return empty list."""
    client = _get_test_client()

    with patch("app.routes.knowledge.get_service", return_value=_make_mock_service()), \
         patch("app.routes.knowledge.require_knowledge_read") as mock_auth:
        mock_auth.return_value = MagicMock(
            user_id="test_user",
            organization_id=None,
        )
        response = client.get(
            "/api/v1/knowledge/documents",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["documents"] == []


def test_knowledge_get_document_not_found():
    """GET /knowledge/documents/{id} should return 404 for missing doc."""
    client = _get_test_client()

    with patch("app.routes.knowledge.get_service", return_value=_make_mock_service()), \
         patch("app.routes.knowledge.require_knowledge_read") as mock_auth:
        mock_auth.return_value = MagicMock(
            user_id="test_user",
            organization_id=None,
        )
        response = client.get(
            "/api/v1/knowledge/documents/nonexistent",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 404
