"""
Routes that push to a conversation's WebSocket must refuse another user's
conversation before doing any work. Alice owns `alice-conv` in a real file
store; bob tries to stream, batch and remix into it.
"""

import asyncio
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DEV_API_KEY", "test-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-unit-tests-only")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.storage.conversations import ConversationStore

BOB = SimpleNamespace(user_id="bob", organization_id=None)
ITEM = {"topic": "AI in Healthcare", "keywords": ["ai"], "tone": "professional"}


class OwnershipTestCase(unittest.TestCase):
    def setUp(self):
        from app.dependencies import require_content_creation
        from app.middleware import require_pro_tier, require_quota
        from server import app

        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConversationStore(self._tmp.name)
        asyncio.run(self.store.append("alice-conv", {"content": "alice"}, user_id="alice"))

        self.app = app
        self.user = "bob"
        app.dependency_overrides[require_quota] = lambda: self.user
        app.dependency_overrides[require_pro_tier] = lambda: self.user
        app.dependency_overrides[require_content_creation] = lambda: SimpleNamespace(
            user_id=self.user, organization_id=None
        )
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

        self.patches = [
            patch(f"app.routes.{mod}.conversations", self.store)
            for mod in ("streaming", "batch", "remix", "websocket", "blog")
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.app.dependency_overrides.clear()
        self._tmp.cleanup()


class TestStreamOwnership(OwnershipTestCase):
    def _start(self, conversation_id):
        service = MagicMock()
        service.start_stream = AsyncMock()
        with patch("app.routes.streaming.get_streaming_service", return_value=service):
            resp = self.client.post(
                "/stream/generate",
                json={"prompt": "hi", "conversation_id": conversation_id},
            )
        return resp, service

    def test_bob_cannot_stream_into_alices_conversation(self):
        resp, service = self._start("alice-conv")
        self.assertEqual(resp.status_code, 403)
        service.start_stream.assert_not_called()


class TestBatchOwnership(OwnershipTestCase):
    def test_bob_cannot_create_a_batch_on_alices_conversation(self):
        with patch("app.routes.batch._process_enhanced_batch", new=AsyncMock()) as run:
            resp = self.client.post(
                "/batch", json={"items": [ITEM], "conversation_id": "alice-conv"}
            )
        self.assertEqual(resp.status_code, 403)
        run.assert_not_called()

    def test_bob_cannot_import_csv_into_alices_conversation(self):
        csv = b"topic,keywords,tone,content_type\nAI in Healthcare,ai,professional,blog\n"
        with patch("app.routes.batch._process_enhanced_batch", new=AsyncMock()) as run:
            resp = self.client.post(
                "/batch/import/csv",
                params={"conversation_id": "alice-conv"},
                files={"file": ("t.csv", csv, "text/csv")},
            )
        self.assertEqual(resp.status_code, 403)
        run.assert_not_called()


class TestRemixOwnership(OwnershipTestCase):
    BODY = {
        "source_content": {"title": "t", "body": "b"},
        "target_formats": ["twitter_thread"],
        "conversation_id": "alice-conv",
    }

    def _post(self, path, json):
        service = MagicMock()
        service.remix = AsyncMock()
        with patch("app.routes.remix.get_remix_service", return_value=service):
            resp = self.client.post(path, json=json)
        return resp, service

    def test_bob_cannot_remix_into_alices_conversation(self):
        resp, service = self._post("/remix/transform", self.BODY)
        self.assertEqual(resp.status_code, 403)
        service.remix.assert_not_called()

    def test_bob_cannot_remix_single_format_into_alices_conversation(self):
        resp, service = self._post("/remix/transform/twitter_thread", self.BODY)
        self.assertEqual(resp.status_code, 403)
        service.remix.assert_not_called()

    def test_batch_remix_refuses_alices_conversation_per_item(self):
        resp, service = self._post("/remix/batch", [self.BODY])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["failed"], 1)
        service.remix.assert_not_called()


class TestWebSocketPreSquat(OwnershipTestCase):
    def test_first_connect_binds_the_owner(self):
        # dev_user connects to an unused id and keeps the socket open...
        with self.client.websocket_connect("/ws/conversation/fresh-conv") as ws:
            ws.send_json({"type": "auth", "api_key": "test-key"})
            self.assertTrue(ws.receive_json()["success"])
            # ...so alice can no longer pick that id and have it broadcast to them.
            self.user = "alice"
            resp, service = TestStreamOwnership._start(self, "fresh-conv")
            self.assertEqual(resp.status_code, 403)
            service.start_stream.assert_not_called()

    def test_reconnecting_owner_is_allowed(self):
        for _ in range(2):
            with self.client.websocket_connect("/ws/conversation/fresh-conv") as ws:
                ws.send_json({"type": "auth", "api_key": "test-key"})
                self.assertTrue(ws.receive_json()["success"])
                ws.send_json({"role": "user", "content": "Hello"})
                self.assertEqual(ws.receive_json()["content"], "Hello")

    def test_connect_to_a_conversation_owned_by_someone_else_closes_4003(self):
        with self.client.websocket_connect("/ws/conversation/alice-conv") as ws:
            ws.send_json({"type": "auth", "api_key": "test-key"})
            self.assertTrue(ws.receive_json()["success"])
            with self.assertRaises(WebSocketDisconnect) as closed:
                ws.receive_json()
        self.assertEqual(closed.exception.code, 4003)


class TestFileStoreClaim(unittest.IsolatedAsyncioTestCase):
    async def test_claim_binds_owner_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            await ConversationStore(tmp).claim("c1", "bob")
            await ConversationStore(tmp).claim("c1", "bob")
            store = ConversationStore(tmp)
            with self.assertRaises(PermissionError):
                await store.claim("c1", "alice")
            with self.assertRaises(PermissionError):
                await store.append("c1", {"content": "alice"}, user_id="alice")
            await store.append("c1", {"content": "bob"}, user_id="bob")
            self.assertEqual(await ConversationStore(tmp).get("c1"), [{"content": "bob"}])


if __name__ == "__main__":
    unittest.main()
