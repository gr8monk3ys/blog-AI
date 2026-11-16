"""
Usage recording against Postgres.

`increment_usage` handed asyncpg a dict (or None) for the `usage_records.metadata`
jsonb column. asyncpg rejects a dict for jsonb, None violates NOT NULL, and the
error was logged and swallowed -- so with a database configured no generation
was ever counted and no quota was ever reached. The file-backed fallback the
rest of the suite exercises never touched that statement.

The first test pins the statement's argument without a database; the rest run
only where a Postgres with the schema is reachable (the `Backend DB Tests` job).
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.types.usage import SubscriptionTier, get_tier_config
from src.usage.quota_service import QuotaExceeded, QuotaService


class UsageMetadataSerialization(unittest.IsolatedAsyncioTestCase):
    async def _recorded_metadata(self, metadata):
        service = QuotaService()
        service._use_db = True
        execute = AsyncMock()
        # Patch the globals the method actually reads: other test modules reload
        # `src.usage.quota_service`, after which a patch by module path would
        # land on a different module object than this class came from.
        with (
            patch.dict(
                QuotaService.increment_usage.__globals__, {"db_execute": execute}
            ),
            patch.object(service, "get_usage_stats", AsyncMock()),
        ):
            await service.increment_usage("user_1", "blog", 4000, metadata)
        query, *args = execute.await_args.args
        self.assertIn("$5::jsonb", query)
        return args[4]

    async def test_dict_metadata_is_sent_as_json_text(self):
        sent = await self._recorded_metadata({"topic": "x", "research": True})
        self.assertIsInstance(sent, str)
        self.assertEqual(json.loads(sent), {"topic": "x", "research": True})

    async def test_missing_metadata_is_an_empty_object_not_null(self):
        self.assertEqual(await self._recorded_metadata(None), "{}")


def _reachable_db_url():
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(dsn=url, statement_cache_size=0)
            try:
                return await conn.fetchval("SELECT to_regclass('public.usage_records')")
            finally:
                await conn.close()

        return url if asyncio.run(_check()) else None
    except Exception:
        return None


_DB_URL = _reachable_db_url()


@unittest.skipUnless(_DB_URL, "no reachable Postgres with the usage tables")
class UsageRecordingPostgres(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._saved = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _DB_URL
        self.user_id = f"quota-{os.getpid()}-{id(self)}"
        from src.db import get_pool

        self.pool = await get_pool()
        await self._cleanup()
        self.service = QuotaService()

    async def asyncTearDown(self):
        await self._cleanup()
        from src.db import close_pool

        await close_pool()
        if self._saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved

    async def _cleanup(self):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM usage_records WHERE user_id = $1", self.user_id
            )
            await conn.execute(
                "DELETE FROM user_quotas WHERE user_id = $1", self.user_id
            )

    async def test_each_generation_is_counted(self):
        await self.service.increment_usage(self.user_id, "blog", 4000, {"topic": "x"})
        stats = await self.service.increment_usage(self.user_id, "blog", 4000, None)

        self.assertEqual(stats.current_usage, 2)
        async with self.pool.acquire() as conn:
            stored = await conn.fetchval(
                "SELECT metadata->>'topic' FROM usage_records "
                "WHERE user_id = $1 AND metadata ? 'topic'",
                self.user_id,
            )
        self.assertEqual(stored, "x")

    async def test_free_tier_is_stopped_at_its_daily_limit(self):
        limit = get_tier_config(SubscriptionTier.FREE).daily_limit
        for _ in range(limit):
            await self.service.check_quota(self.user_id)
            await self.service.increment_usage(self.user_id, "blog", 4000, {})

        with self.assertRaises(QuotaExceeded):
            await self.service.check_quota(self.user_id)

    async def test_paid_tier_set_by_billing_raises_the_limit(self):
        limit = get_tier_config(SubscriptionTier.FREE).daily_limit
        for _ in range(limit):
            await self.service.increment_usage(self.user_id, "blog", 4000, {})

        await self.service.set_user_tier(self.user_id, SubscriptionTier.PRO)

        self.assertTrue(await self.service.check_quota(self.user_id))


if __name__ == "__main__":
    unittest.main()
