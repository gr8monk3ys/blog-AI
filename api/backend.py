"""The FastAPI app (`apps/api`) served from the web app's Vercel project.

Vercel turns files under the project root's `api/` directory into functions,
next to the Next.js build. `apps/web/next.config.mjs` rewrites `/backend` and
`/backend/*` to this function, so the browser reaches the API on the web app's
own origin (no second project, URL, CORS or deploy).

The request reaches this function with its original path (`/backend/health`),
so `_StripPrefix` removes `/backend` before FastAPI routes it: the API's routes
stay exactly as they are (`/health`, `/api/v1/...`, `/stream/...`).

`apps/api` is put on `sys.path` and made the working directory because the
API was written to run from there (`from src...` imports, relative data
files), as it does on the standalone `blog-ai-api` project.
"""

import os
import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))
os.chdir(_API_DIR)

from server import app as _api  # noqa: E402

PREFIX = "/backend"


class _StripPrefix:
    """ASGI wrapper: `/backend/x` -> `/x`, with `root_path` set to `/backend`."""

    def __init__(self, inner, prefix: str) -> None:
        self.inner = inner
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            if path == self.prefix or path.startswith(self.prefix + "/"):
                scope = dict(scope)
                scope["path"] = path[len(self.prefix):] or "/"
                raw = scope.get("raw_path")
                if raw:
                    scope["raw_path"] = raw[len(self.prefix):] or b"/"
                scope["root_path"] = scope.get("root_path", "") + self.prefix
        await self.inner(scope, receive, send)


app = _StripPrefix(_api, PREFIX)

__all__ = ["app"]
