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

from fastapi import HTTPException
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

    def test_retry_channel_ids_are_rejected(self):
        resp, service = self._start("retry-abc")
        self.assertEqual(resp.status_code, 422)
        service.start_stream.assert_not_called()

    def test_streaming_into_a_fresh_id_binds_it(self):
        self.user = "alice"
        service = MagicMock()
        service.start_stream = AsyncMock(
            return_value=SimpleNamespace(session_id="s1", conversation_id="fresh-conv")
        )
        with patch("app.routes.streaming.get_streaming_service", return_value=service), patch(
            "app.routes.streaming.increment_usage_for_operation", new=AsyncMock()
        ):
            resp = self.client.post(
                "/stream/generate", json={"prompt": "hi", "conversation_id": "fresh-conv"}
            )
        self.assertEqual(resp.status_code, 202)

        self.user = "bob"
        resp, service = self._start("fresh-conv")
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

    def test_retry_channel_ids_are_rejected(self):
        csv = b"topic,keywords,tone,content_type\nAI in Healthcare,ai,professional,blog\n"
        with (
            patch("app.routes.batch._process_enhanced_batch", new=AsyncMock()) as run,
            patch("app.routes.batch._validate_configured_providers"),
        ):
            body = self.client.post(
                "/batch", json={"items": [ITEM], "conversation_id": "retry-abc"}
            )
            upload = self.client.post(
                "/batch/import/csv",
                params={"conversation_id": "retry-abc"},
                files={"file": ("t.csv", csv, "text/csv")},
            )
        self.assertEqual((body.status_code, upload.status_code), (422, 422))
        run.assert_not_called()

    def test_batch_on_a_fresh_id_binds_it(self):
        csv = b"topic,keywords,tone,content_type\nAI in Healthcare,ai,professional,blog\n"
        with patch("app.routes.batch._process_enhanced_batch", new=AsyncMock()):
            self.user = "alice"
            first = self.client.post("/batch", json={"items": [ITEM], "conversation_id": "b1"})
            self.user = "bob"
            second = self.client.post("/batch", json={"items": [ITEM], "conversation_id": "b1"})
            third = self.client.post(
                "/batch/import/csv",
                params={"conversation_id": "b1"},
                files={"file": ("t.csv", csv, "text/csv")},
            )
        self.assertNotEqual(first.status_code, 403)
        self.assertEqual((second.status_code, third.status_code), (403, 403))


class TestBatchRetryOwnership(OwnershipTestCase):
    JOB = "job-1"

    def setUp(self):
        super().setUp()
        from src.types.batch import JobStatus

        job = SimpleNamespace(can_retry_failed=True, name="j")
        failed = SimpleNamespace(status=JobStatus.FAILED, index=0, topic="AI in Healthcare")
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            side_effect=lambda job_id, scope: job if scope == "alice" else None
        )
        store.get_results = AsyncMock(return_value=[failed])
        store.save_job = AsyncMock()
        store.set_cancel_flag = AsyncMock()
        for p in (
            patch("app.routes.batch._job_store", store),
            patch("app.routes.batch._validate_configured_providers"),
        ):
            p.start()
            self.patches.append(p)

    def _retry(self, user):
        self.user = user
        with patch("app.routes.batch._process_enhanced_batch", new=AsyncMock()) as run:
            resp = self.client.post(f"/batch/{self.JOB}/retry", json={})
        return resp, run

    def test_bob_cannot_retry_alices_job(self):
        resp, run = self._retry("bob")
        self.assertEqual(resp.status_code, 404)
        run.assert_not_called()

    def test_retry_gets_a_fresh_channel_bound_to_the_retrying_user(self):
        resp, run = self._retry("alice")
        self.assertEqual(resp.status_code, 202, resp.text)
        channel = f"retry-{resp.json()['retry_job_id']}"
        self.assertEqual(run.call_args.args[1].conversation_id, channel)
        with self.assertRaises(PermissionError):
            asyncio.run(self.store.claim(channel, "bob"))

    def test_squatting_the_old_job_scoped_channel_does_nothing(self):
        asyncio.run(self.store.claim(f"retry-{self.JOB}", "bob"))
        resp, run = self._retry("alice")
        self.assertEqual(resp.status_code, 202, resp.text)
        self.assertNotEqual(run.call_args.args[1].conversation_id, f"retry-{self.JOB}")


class TestRemixOwnership(OwnershipTestCase):
    BODY = {
        "source_content": {"title": "t", "body": "b"},
        "target_formats": ["twitter_thread"],
        "conversation_id": "alice-conv",
    }

    def _post(self, path, json):
        service = MagicMock()
        service.remix = AsyncMock(side_effect=HTTPException(status_code=502))
        with patch("app.routes.remix.get_remix_service", return_value=service):
            resp = self.client.post(path, json=json)
        return resp, service

    def test_bob_cannot_remix_into_alices_conversation(self):
        resp, service = self._post("/remix/transform", self.BODY)
        self.assertEqual(resp.status_code, 403)
        service.remix.assert_not_called()

    def test_remix_on_a_fresh_id_binds_it(self):
        self.user = "alice"
        first, _ = self._post("/remix/transform", {**self.BODY, "conversation_id": "r1"})
        self.assertNotEqual(first.status_code, 403)
        self.user = "bob"
        resp, service = self._post("/remix/transform", {**self.BODY, "conversation_id": "r1"})
        self.assertEqual(resp.status_code, 403)
        service.remix.assert_not_called()

    def test_retry_channel_ids_are_rejected(self):
        resp, service = self._post("/remix/transform", {**self.BODY, "conversation_id": "retry-abc"})
        self.assertEqual(resp.status_code, 422)
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
