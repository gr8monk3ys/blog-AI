"""scripts/create_api_key.py must never store a key it cannot hand to the operator."""

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "create_api_key.py"
_spec = importlib.util.spec_from_file_location("create_api_key", _SCRIPT)
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)


class CreateApiKeyScript(unittest.IsolatedAsyncioTestCase):
    async def _run(self, which, run=None):
        store = AsyncMock()
        create = AsyncMock(return_value="blog_ai_plaintext")
        with patch.object(sys, "argv", ["create_api_key.py", "--user-id", "op"]), \
             patch.object(script.shutil, "which", side_effect=which), \
             patch.object(script.subprocess, "run", run or (lambda *a, **k: None)), \
             patch.object(script, "api_key_store", store), \
             patch.object(script, "get_or_create_api_key", create):
            return await script._main(), store, create

    async def test_no_output_mechanism_creates_no_key(self):
        main, store, create = await self._run(lambda name: None)
        self.assertEqual(main, 1)
        create.assert_not_called()
        store.revoke_key.assert_not_called()

    async def test_linux_clipboard_fallback_is_used(self):
        calls = []
        main, store, _ = await self._run(
            lambda name: f"/usr/bin/{name}" if name == "wl-copy" else None,
            run=lambda argv, **k: calls.append((argv, k["input"])),
        )
        self.assertEqual(main, 0)
        self.assertEqual(calls, [(["/usr/bin/wl-copy"], "blog_ai_plaintext")])
        store.revoke_key.assert_not_called()

    async def test_failed_output_revokes_the_new_key(self):
        def fail(argv, **k):
            raise subprocess.CalledProcessError(1, argv)

        main, store, _ = await self._run(
            lambda name: "/usr/bin/xclip" if name == "xclip" else None, run=fail
        )
        self.assertEqual(main, 1)
        store.revoke_key.assert_awaited_once_with("op")


if __name__ == "__main__":
    unittest.main()
