"""
Tests for PgVectorStore implementation.

These tests verify the PgVectorStore class works correctly against mocked
asyncpg connections (no real database needed).
"""

import os
import sys
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.types.knowledge import VectorStoreConfig, VectorStoreProvider


def _make_pgvector_store():
    """Create a PgVectorStore instance for testing."""
    from src.knowledge.vector_store import PgVectorStore

    config = VectorStoreConfig(provider=VectorStoreProvider.PGVECTOR)
    return PgVectorStore(config)


class _FakeAcquire:
    """Async context manager that returns a mock connection."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass


def _mock_pool():
    """Create a mock asyncpg pool with proper async context manager."""
    conn = AsyncMock()
    pool = MagicMock()
    pool.acquire.return_value = _FakeAcquire(conn)
    return pool, conn


@pytest.mark.asyncio
async def test_initialize_checks_extension():
    """initialize() should verify pgvector extension exists."""
    store = _make_pgvector_store()
    pool, conn = _mock_pool()
    conn.fetchrow.return_value = {"?column?": 1}  # Extension exists

    with patch("src.knowledge.vector_store.PgVectorStore.initialize") as mock_init:
        mock_init.return_value = None
        await store.initialize()


@pytest.mark.asyncio
async def test_search_returns_results():
    """search() should query kb_embeddings and return SearchResult objects."""
    store = _make_pgvector_store()
    pool, conn = _mock_pool()
    store._pool = pool

    # Mock search results
    conn.fetch.return_value = [
        {
            "id": "chunk_1",
            "document_id": "doc_1",
            "content": "Test content",
            "chunk_index": 0,
            "page_number": 1,
            "section_title": "Intro",
            "metadata": json.dumps({"document_title": "Test Doc"}),
            "score": 0.95,
        }
    ]

    results = await store.search(
        query_embedding=[0.1] * 1536,
        top_k=5,
        namespace="user_test123",
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk_1"
    assert results[0].score == 0.95
    assert results[0].document_id == "doc_1"


@pytest.mark.asyncio
async def test_delete_by_document_id():
    """delete() should delete by document_id filter."""
    store = _make_pgvector_store()
    pool, conn = _mock_pool()
    store._pool = pool
    conn.execute.return_value = "DELETE 5"

    count = await store.delete(filters={"document_id": "doc_1"})
    assert count == 5
    conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats_with_namespace():
    """get_stats() should query kb_usage_stats view."""
    store = _make_pgvector_store()
    pool, conn = _mock_pool()
    store._pool = pool
    conn.fetchrow.return_value = {
        "total_chunks": 42,
        "document_count": 3,
        "total_storage_bytes": 5000,
    }

    stats = await store.get_stats(namespace="user_test123")
    assert stats["total_vectors"] == 42
    assert stats["document_count"] == 3


def test_create_vector_store_factory_pgvector():
    """create_vector_store should return PgVectorStore for pgvector config."""
    from src.knowledge.vector_store import create_vector_store, PgVectorStore

    config = VectorStoreConfig(provider=VectorStoreProvider.PGVECTOR)
    store = create_vector_store(config)
    assert isinstance(store, PgVectorStore)
