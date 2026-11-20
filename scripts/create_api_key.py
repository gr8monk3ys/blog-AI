"""
Create or reset a local API key for development/testing.

Usage:
  python scripts/create_api_key.py --user-id local_dev
  python scripts/create_api_key.py --user-id local_dev --reset
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
from collections.abc import Callable
from functools import partial

from app.auth.api_key import api_key_store, get_or_create_api_key


def _to_clipboard(argv: list[str], key: str) -> str:
    subprocess.run(argv, input=key, check=True, text=True)
    return "API key copied to the clipboard."


def _pick_output(user_id: str) -> Callable[[str], str]:
    """Choose where the key goes before any key is created, so it can't be lost."""
    security_cmd = shutil.which("security")
    if security_cmd:
        service_name = f"blog-ai.api-key.{user_id}"

        def to_keychain(key: str) -> str:
            subprocess.run(
                [security_cmd, "add-generic-password", "-U", "-a", user_id,
                 "-s", service_name, "-w", key],
                check=True,
                capture_output=True,
                text=True,
            )
            return (
                "API key stored in the macOS Keychain. "
                f"Service: {service_name}, Account: {user_id}"
            )

        return to_keychain

    for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
        path = shutil.which(cmd[0])
        if path:
            return partial(_to_clipboard, [path, *cmd[1:]])

    raise RuntimeError(
        "No secure output mechanism is available on this machine "
        "(need macOS `security`, pbcopy, wl-copy or xclip). No key was created."
    )


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Create or reset a local API key")
    parser.add_argument("--user-id", default="local_dev", help="User ID for the key")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Revoke existing key before creating a new one",
    )
    args = parser.parse_args()

    try:
        output = _pick_output(args.user_id)
    except RuntimeError as e:
        print(e)
        return 1

    if args.reset:
        await api_key_store.revoke_key(args.user_id)

    key = await get_or_create_api_key(args.user_id)
    if not key:
        print(
            "API key already exists for this user. "
            "Use --reset to revoke and create a new key."
        )
        return 1

    try:
        print(output(key))
    except (OSError, subprocess.CalledProcessError) as e:
        # The plaintext is gone once we return; don't leave an unusable key stored.
        await api_key_store.revoke_key(args.user_id)
        print(f"Could not output the API key ({e}); it was revoked. Nothing is stored.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
