"""
Tests for KnowledgeService with Neon metadata storage.

Verifies the service can be instantiated from settings and that
metadata operations use asyncpg instead of Supabase.
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_knowledge_service_from_env_uses_settings():
    """from_env() should read KnowledgeBaseSettings, not raw env vars."""
    with patch("src.knowledge.knowledge_service.create_vector_store") as mock_vs, \
         patch("src.knowledge.knowledge_service.DocumentProcessor"), \
         patch("src.knowledge.knowledge_service.EmbeddingGenerator") as mock_eg:

        mock_eg_instance = MagicMock()
        mock_eg_instance.dimensions = 1536
        mock_eg.return_value = mock_eg_instance
        mock_vs.return_value = MagicMock()

        from src.knowledge.knowledge_service import KnowledgeService
        service = KnowledgeService.from_env()

        assert service is not None
        # Should not have a supabase attribute — only _db_pool
        assert not hasattr(service, "supabase")
        assert hasattr(service, "_db_pool")


def test_knowledge_service_has_no_supabase_dependency():
    """KnowledgeService should not reference Supabase client."""
    import inspect
    from src.knowledge.knowledge_service import KnowledgeService

    source = inspect.getsource(KnowledgeService.__init__)
    assert "supabase" not in source.lower(), "KnowledgeService.__init__ should not reference Supabase"


class _FakeAcquire:
    """Async context manager that returns a mock connection."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_list_documents_uses_asyncpg():
    """list_documents() should query Postgres, not Supabase."""
    from src.knowledge.knowledge_service import KnowledgeService

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = _FakeAcquire(mock_conn)

    with patch("src.knowledge.knowledge_service.create_vector_store") as mock_vs, \
         patch("src.knowledge.knowledge_service.DocumentProcessor"), \
         patch("src.knowledge.knowledge_service.EmbeddingGenerator") as mock_eg:

        mock_eg_instance = MagicMock()
        mock_eg_instance.dimensions = 1536
        mock_eg.return_value = mock_eg_instance
        mock_vs.return_value = MagicMock()

        service = KnowledgeService.from_env()
        service._db_pool = mock_pool

        docs = await service.list_documents("user_123")
        assert docs == []
        mock_conn.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_list_documents_falls_back_to_cache():
    """list_documents() should use in-memory cache when DB unavailable."""
    from src.knowledge.knowledge_service import KnowledgeService

    with patch("src.knowledge.knowledge_service.create_vector_store") as mock_vs, \
         patch("src.knowledge.knowledge_service.DocumentProcessor"), \
         patch("src.knowledge.knowledge_service.EmbeddingGenerator") as mock_eg:

        mock_eg_instance = MagicMock()
        mock_eg_instance.dimensions = 1536
        mock_eg.return_value = mock_eg_instance
        mock_vs.return_value = MagicMock()

        service = KnowledgeService.from_env()
        service._db_pool = None  # No DB available

        # Mock _get_db_pool to return None
        service._get_db_pool = AsyncMock(return_value=None)

        docs = await service.list_documents("user_123")
        assert docs == []
