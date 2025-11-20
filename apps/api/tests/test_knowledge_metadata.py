"""Integration tests for the Neon/asyncpg knowledge-base document metadata path.

Skipped unless a reachable Postgres with kb_documents is configured
(TEST_DATABASE_URL or DATABASE_URL). Exercises KnowledgeService's metadata
operations and the kb_usage_stats view consumed by quota.py.
"""

import asyncio
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _reachable_db_url():
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(dsn=url, statement_cache_size=0)
            try:
                return await conn.fetchval("SELECT to_regclass('public.kb_documents')")
            finally:
                await conn.close()

        return url if asyncio.run(_check()) else None
    except Exception:
        return None


_DB_URL = _reachable_db_url()


@unittest.skipUnless(_DB_URL, "no reachable Postgres with kb_documents")
class TestKnowledgeMetadataNeon(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._saved = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _DB_URL

        from src.knowledge.knowledge_service import KnowledgeService
        from src.types.knowledge import Document, DocumentMetadata, DocumentType

        self._Document = Document
        self._DocumentMetadata = DocumentMetadata
        self._DocumentType = DocumentType
        # Only the metadata methods are exercised; the heavy components are unused.
        self.svc = KnowledgeService(None, None, None)
        self.uid = f"kbuser-{os.getpid()}-{id(self)}"

        from src.db import get_pool

        self.pool = await get_pool()
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM kb_documents WHERE user_id = $1", self.uid)

    async def asyncTearDown(self):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM kb_documents WHERE user_id = $1", self.uid)
        from src.db import close_pool

        await close_pool()
        if self._saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved

    def _doc(self, doc_id, **over):
        md = self._DocumentMetadata(
            title=over.get("title", "Doc"),
            source="f.txt",
            file_type=self._DocumentType.TXT,
            file_size_bytes=over.get("size", 100),
            page_count=2,
            custom_metadata=over.get("meta", {"k": "v"}),
        )
        return self._Document(
            id=doc_id,
            user_id=self.uid,
            filename="f.txt",
            content="",
            metadata=md,
            status="ready",
            chunk_count=over.get("chunks", 1),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def test_store_get_roundtrip_with_jsonb(self):
        await self.svc._store_document_metadata(self._doc("d1", meta={"a": 1}))
        got = await self.svc.get_document("d1", self.uid)
        self.assertIsNotNone(got)
        self.assertEqual(got.metadata.custom_metadata, {"a": 1})
        self.assertEqual(got.metadata.file_size_bytes, 100)

    async def test_ownership_isolation(self):
        await self.svc._store_document_metadata(self._doc("d1"))
        self.assertIsNone(await self.svc.get_document("d1", "someone-else"))

    async def test_upsert_updates_in_place(self):
        await self.svc._store_document_metadata(self._doc("d1", chunks=1, title="A"))
        await self.svc._store_document_metadata(self._doc("d1", chunks=7, title="B"))
        got = await self.svc.get_document("d1", self.uid)
        self.assertEqual((got.chunk_count, got.metadata.title), (7, "B"))
        docs = await self.svc.list_documents(self.uid)
        self.assertEqual(len(docs), 1)  # upsert, not duplicate

    async def test_list_and_delete(self):
        await self.svc._store_document_metadata(self._doc("d1"))
        await self.svc._store_document_metadata(self._doc("d2"))
        self.assertEqual(len(await self.svc.list_documents(self.uid)), 2)
        await self.svc._delete_document_metadata("d1", self.uid)
        remaining = await self.svc.list_documents(self.uid)
        self.assertEqual([d.id for d in remaining], ["d2"])

    async def test_kb_usage_stats_view(self):
        await self.svc._store_document_metadata(self._doc("d1", size=400))
        await self.svc._store_document_metadata(self._doc("d2", size=600))
        from src.knowledge.quota import _get_kb_usage

        usage = await _get_kb_usage(self.uid)
        self.assertEqual(usage["document_count"], 2)
        self.assertEqual(usage["total_storage_bytes"], 1000)


if __name__ == "__main__":
    unittest.main()
