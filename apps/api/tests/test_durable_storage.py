"""
API keys and conversations survive a cold start when DATABASE_URL is set.

On Vercel the file stores (API_KEY_STORAGE_PATH, CONVERSATION_STORAGE_DIR) sit
on an ephemeral disk. With a database configured both stores now live in
Postgres (db/migrations/010); without one they fall back to the files, the same
split usage/quota uses. The Postgres tests run only where a migrated database is
reachable (the `Backend DB Tests` job, `bun run verify:api:db`).
"""

import asyncio
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _fresh(module_name):
    for name in [
        m for m in sys.modules if m == module_name or m.startswith(module_name + ".")
    ]:
        del sys.modules[name]
    parent = module_name.rsplit(".", 1)[0]
    sys.modules.pop(parent, None)
    return importlib.import_module(module_name)


class StoreSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {
            "API_KEY_STORAGE_PATH": os.path.join(self.tmp.name, "keys.json"),
            "CONVERSATION_STORAGE_DIR": os.path.join(self.tmp.name, "conversations"),
        }

    def tearDown(self):
        self.tmp.cleanup()
        # Leave the real modules importable for the rest of the suite.
        _fresh("app.auth.api_key")
        _fresh("app.storage.conversations")

    def _load(self, env):
        with patch.dict(os.environ, env, clear=False):
            for var in ("DATABASE_URL", "DATABASE_URL_DIRECT"):
                if var not in env:
                    os.environ.pop(var, None)
            keys = _fresh("app.auth.api_key")
            convs = _fresh("app.storage.conversations")
        return keys, convs

    def test_without_database_url_the_file_stores_are_used(self):
        keys, convs = self._load(self.env)
        self.assertIsInstance(keys.api_key_store, keys.APIKeyStore)
        self.assertIsInstance(convs.conversations, convs.ConversationStore)

    def test_with_database_url_the_postgres_stores_are_used(self):
        keys, convs = self._load(
            {**self.env, "DATABASE_URL": "postgresql://x@127.0.0.1:1/x"}
        )
        self.assertIsInstance(keys.api_key_store, keys.PostgresAPIKeyStore)
        self.assertIsInstance(convs.conversations, convs.PostgresConversationStore)


class FileKeyStoreHashing(unittest.IsolatedAsyncioTestCase):
    async def test_plaintext_key_is_never_written_to_disk(self):
        from app.auth.api_key import APIKeyStore

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "keys.json")
            key = await APIKeyStore(storage_path=path).create_key("u1")
            on_disk = Path(path).read_text()
        self.assertNotIn(key, on_disk)
        self.assertIn("$2", on_disk)


class FileConversationStore(unittest.IsolatedAsyncioTestCase):
    async def test_round_trip_and_ownership_survive_a_restart(self):
        from app.storage.conversations import ConversationStore

        with tempfile.TemporaryDirectory() as tmp:
            await ConversationStore(tmp).append(
                "c1", {"role": "user", "content": "hi"}, user_id="u1"
            )
            store = ConversationStore(tmp)
            self.assertEqual(await store.get("c1"), [{"role": "user", "content": "hi"}])
            self.assertTrue(await store.verify_ownership("c1", "u1"))
            self.assertFalse(await store.verify_ownership("c1", "u2"))
            self.assertTrue(await store.delete("c1"))
            self.assertEqual(await ConversationStore(tmp).get("c1"), [])

    async def test_append_by_another_user_is_rejected(self):
        from app.storage.conversations import ConversationStore

        with tempfile.TemporaryDirectory() as tmp:
            await ConversationStore(tmp).append("c1", {"content": "alice"}, user_id="alice")
            store = ConversationStore(tmp)
            with self.assertRaises(PermissionError):
                await store.append("c1", {"content": "injected by bob"}, user_id="bob")
            self.assertEqual(await ConversationStore(tmp).get("c1"), [{"content": "alice"}])

    async def test_postgres_store_rejects_bad_ids_before_querying(self):
        from app.storage.conversations import PostgresConversationStore

        with self.assertRaises(ValueError):
            await PostgresConversationStore().get("../etc")


def _reachable_db_url():
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(dsn=url, statement_cache_size=0)
            try:
                return await conn.fetchval(
                    "SELECT to_regclass('public.api_keys') IS NOT NULL"
                    " AND to_regclass('public.conversations') IS NOT NULL"
                )
            finally:
                await conn.close()

        return url if asyncio.run(_check()) else None
    except (ImportError, OSError, ValueError, asyncpg.PostgresError):
        return None


_DB_URL = _reachable_db_url()


@unittest.skipUnless(
    _DB_URL, "no reachable Postgres with the api_keys/conversations tables"
)
class PostgresStores(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._saved = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _DB_URL
        self.tag = f"durable-{os.getpid()}-{id(self)}"
        from src.db import get_pool

        self.pool = await get_pool()
        await self._cleanup()

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
                "DELETE FROM api_keys WHERE user_id LIKE $1", self.tag + "%"
            )
            await conn.execute(
                "DELETE FROM conversations WHERE id LIKE $1", self.tag + "%"
            )

    async def test_api_key_round_trip(self):
        from app.auth.api_key import PostgresAPIKeyStore

        user = self.tag + "-u1"
        key = await PostgresAPIKeyStore().create_key(user)

        # A new instance stands in for a cold start: nothing is held in memory.
        store = PostgresAPIKeyStore()
        self.assertTrue(await store.user_has_key(user))
        self.assertEqual(await store.verify_key(key), user)
        self.assertIsNone(await store.verify_key(key + "x"))
        self.assertIsNone(await store.get_or_create_key(user))

        rotated = await store.create_key(user)
        self.assertIsNone(await store.verify_key(key))
        self.assertEqual(await store.verify_key(rotated), user)

        self.assertTrue(await store.revoke_key(user))
        self.assertIsNone(await store.verify_key(rotated))
        self.assertFalse(await store.revoke_key(user))
        self.assertIsNotNone(await store.get_or_create_key(user))

    async def test_api_key_is_stored_hashed(self):
        from app.auth.api_key import PostgresAPIKeyStore

        user = self.tag + "-hashed"
        key = await PostgresAPIKeyStore().create_key(user)
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM api_keys WHERE user_id = $1", user)
        self.assertNotIn(key, [str(v) for v in row.values()])
        self.assertTrue(row["key_hash"].startswith("$2"))

    async def test_conversation_round_trip_and_ownership(self):
        from app.storage.conversations import PostgresConversationStore

        cid = self.tag + "-c1"
        first = {"role": "user", "content": "hi", "timestamp": "2026-11-15T00:00:00"}
        second = {"role": "assistant", "content": "hello"}
        store = PostgresConversationStore()
        self.assertTrue(await store.verify_ownership(cid, "anyone"))
        await store.append(cid, first, user_id="u1")
        await store.append(cid, second, user_id="u1")

        store = PostgresConversationStore()
        self.assertEqual(await store.get(cid), [first, second])
        self.assertTrue(await store.verify_ownership(cid, "u1"))
        self.assertFalse(await store.verify_ownership(cid, "u2"))
        self.assertTrue(await store.delete(cid))
        self.assertFalse(await store.delete(cid))
        self.assertEqual(await store.get(cid), [])

    async def test_append_by_another_user_is_rejected(self):
        from app.storage.conversations import PostgresConversationStore

        cid = self.tag + "-idor"
        await PostgresConversationStore().append(cid, {"content": "alice"}, user_id="alice")
        with self.assertRaises(PermissionError):
            await PostgresConversationStore().append(
                cid, {"content": "injected by bob"}, user_id="bob"
            )
        self.assertEqual(
            await PostgresConversationStore().get(cid), [{"content": "alice"}]
        )

    async def test_conversation_without_owner_is_denied(self):
        from app.storage.conversations import PostgresConversationStore

        cid = self.tag + "-orphan"
        await PostgresConversationStore().append(cid, {"role": "user", "content": "x"})
        self.assertFalse(await PostgresConversationStore().verify_ownership(cid, "u1"))


if __name__ == "__main__":
    unittest.main()
