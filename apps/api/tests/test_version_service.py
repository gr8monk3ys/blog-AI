"""Tests for the content version service: factory selection + the Neon/asyncpg
backend.

The integration tests exercise NeonVersionService against a real Postgres and are
skipped unless a reachable database is configured (TEST_DATABASE_URL or
DATABASE_URL) with db/migrations applied. The factory-selection tests run
everywhere (construction does not open a connection).
"""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.content.version_service import (  # noqa: E402
    ContentVersionService,
    InMemoryVersionService,
    NeonVersionService,
    SupabaseVersionService,
)
from src.types.version import ChangeType  # noqa: E402


class _EnvGuard:
    """Temporarily set/unset env vars and reset the service singleton."""

    KEYS = (
        "DATABASE_URL",
        "DATABASE_URL_DIRECT",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_KEY",
    )

    def __init__(self, **overrides):
        self.overrides = overrides

    def __enter__(self):
        self._saved = {k: os.environ.get(k) for k in self.KEYS}
        for k in self.KEYS:
            os.environ.pop(k, None)
        for k, v in self.overrides.items():
            os.environ[k] = v
        ContentVersionService.reset()
        return self

    def __exit__(self, *exc):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        ContentVersionService.reset()


class TestFactorySelection(unittest.TestCase):
    def test_prefers_neon_when_database_url_set(self):
        with _EnvGuard(DATABASE_URL="postgresql://x@/db"):
            self.assertIsInstance(
                ContentVersionService.get_service(), NeonVersionService
            )

    def test_uses_supabase_when_only_supabase_configured(self):
        with _EnvGuard(SUPABASE_URL="https://x.supabase.co", SUPABASE_KEY="k"):
            self.assertIsInstance(
                ContentVersionService.get_service(), SupabaseVersionService
            )

    def test_falls_back_to_in_memory_when_nothing_configured(self):
        with _EnvGuard():
            self.assertIsInstance(
                ContentVersionService.get_service(), InMemoryVersionService
            )


def _reachable_db_url():
    """Return a DB URL with content_versions present, or None to skip.

    Evaluated once at import time (no running event loop), so it can safely spin
    up its own loop via asyncio.run.
    """
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(dsn=url, statement_cache_size=0)
            try:
                return await conn.fetchval(
                    "SELECT to_regclass('public.content_versions')"
                )
            finally:
                await conn.close()

        return url if asyncio.run(_check()) else None
    except Exception:
        return None


_DB_URL = _reachable_db_url()


@unittest.skipUnless(_DB_URL, "no reachable Postgres with content_versions")
class TestNeonVersionServiceIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._saved_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _DB_URL
        ContentVersionService.reset()
        from src.db import get_pool

        self.pool = await get_pool()
        self.cid = f"itest-{os.getpid()}-{id(self)}"
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM content_versions WHERE content_id = $1", self.cid
            )
            await conn.execute(
                "DELETE FROM content_version_organizations WHERE content_id = $1",
                self.cid,
            )
        self.svc = ContentVersionService.get_service()

    async def asyncTearDown(self):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM content_versions WHERE content_id = $1", self.cid
            )
            await conn.execute(
                "DELETE FROM content_version_organizations WHERE content_id = $1",
                self.cid,
            )
        # Each IsolatedAsyncioTestCase runs on its own event loop; close the
        # cached pool so the next test rebuilds one bound to its loop.
        from src.db import close_pool

        await close_pool()
        ContentVersionService.reset()
        if self._saved_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved_db_url

    async def test_create_dedup_list_and_current_flag(self):
        _, n1, _, dup1 = await self.svc.create_version(
            self.cid, "alpha", ChangeType.INITIAL
        )
        self.assertEqual((n1, dup1), (1, False))
        _, n2, _, dup2 = await self.svc.create_version(self.cid, "alpha")
        self.assertEqual((n2, dup2), (1, True))  # identical -> no new version
        await self.svc.create_version(self.cid, "alpha beta gamma")
        versions, total = await self.svc.get_versions(self.cid)
        self.assertEqual(total, 2)
        self.assertEqual([v.version_number for v in versions], [2, 1])  # newest first
        self.assertEqual([v.version_number for v in versions if v.is_current], [2])

    async def test_restore_and_statistics(self):
        await self.svc.create_version(self.cid, "one", ChangeType.INITIAL)
        await self.svc.create_version(self.cid, "one two three")
        ok, _, new_no, frm, _ = await self.svc.restore_version(self.cid, 1)
        self.assertTrue(ok)
        self.assertEqual((new_no, frm), (3, 1))
        stats = await self.svc.get_statistics(self.cid)
        self.assertEqual(stats.total_versions, 3)
        self.assertEqual(stats.current_version, 3)
        self.assertEqual(stats.restores, 1)

    async def test_ownership_register_and_conflict(self):
        await self.svc.create_version(self.cid, "x", ChangeType.INITIAL)
        self.assertFalse(await self.svc.is_content_in_organization(self.cid, "org1"))
        self.assertTrue(await self.svc.register_content_organization(self.cid, "org1"))
        self.assertTrue(await self.svc.is_content_in_organization(self.cid, "org1"))
        self.assertFalse(await self.svc.register_content_organization(self.cid, "org2"))


if __name__ == "__main__":
    unittest.main()
