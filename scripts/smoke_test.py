"""
Minimal smoke test for the Blog AI API.

Usage:
  python scripts/smoke_test.py

Environment:
  BLOGAI_BASE_URL (default: http://localhost:8000)
  BLOGAI_API_KEY (optional; required for generation endpoints)
  BLOGAI_ORG_ID (optional; for org-scoped access)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _request(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict | None = None,
    timeout: int = 15,
):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main() -> int:
    base_url = os.environ.get("BLOGAI_BASE_URL", "http://localhost:8000").rstrip("/")
    timeout = int(os.environ.get("BLOGAI_TIMEOUT_SECONDS", "60"))
    api_key = os.environ.get("BLOGAI_API_KEY")
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    org_id = os.environ.get("BLOGAI_ORG_ID")

    print(f"Smoke test against {base_url}")

    status, body = _request("GET", f"{base_url}/health", timeout=timeout)
    print(f"/health -> {status}")
    if status >= 400:
        print(body)
        return 1

    if not api_key and not dev_mode:
        print("No BLOGAI_API_KEY set; skipping generation endpoints.")
        return 0

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    elif dev_mode:
        print("DEV_MODE enabled; running generation endpoints without API key.")
    if org_id:
        headers["X-Organization-ID"] = org_id

    blog_payload = {
        "topic": "Smoke Test Blog",
        "keywords": ["smoke", "test"],
        "tone": "informative",
        "research": False,
        "proofread": False,
        "humanize": False,
        "conversation_id": "smoke-test-blog",
    }
    status, body = _request(
        "POST", f"{base_url}/generate-blog", blog_payload, headers, timeout=timeout
    )
    if status == 404:
        status, body = _request(
            "POST",
            f"{base_url}/api/v1/generate-blog",
            blog_payload,
            headers,
            timeout=timeout,
        )
        print(f"/api/v1/generate-blog -> {status}")
    else:
        print(f"/generate-blog -> {status}")
    if status >= 400:
        print(body)
        return 1

    book_payload = {
        "title": "Smoke Test Book",
        "keywords": ["smoke", "test"],
        "num_chapters": 2,
        "sections_per_chapter": 2,
        "tone": "informative",
        "research": False,
        "proofread": False,
        "humanize": False,
        "conversation_id": "smoke-test-book",
    }
    status, body = _request(
        "POST", f"{base_url}/generate-book", book_payload, headers, timeout=timeout
    )
    if status == 404:
        status, body = _request(
            "POST",
            f"{base_url}/api/v1/generate-book",
            book_payload,
            headers,
            timeout=timeout,
        )
        print(f"/api/v1/generate-book -> {status}")
    else:
        print(f"/generate-book -> {status}")
    if status >= 400:
        print(body)
        return 1

    print("Smoke test complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
