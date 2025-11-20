"""
Create or reset a local API key for development/testing.

Usage:
  python scripts/create_api_key.py --user-id local_dev
  python scripts/create_api_key.py --user-id local_dev --reset
"""

from __future__ import annotations

import argparse
import shutil
import subprocess

from app.auth.api_key import api_key_store, get_or_create_api_key


def _store_key_securely(user_id: str, key: str) -> str:
    security_cmd = shutil.which("security")
    if security_cmd:
        service_name = f"blog-ai.api-key.{user_id}"
        subprocess.run(
            [
                security_cmd,
                "add-generic-password",
                "-U",
                "-a",
                user_id,
                "-s",
                service_name,
                "-w",
                key,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return (
            "API key stored in the macOS Keychain. "
            f"Service: {service_name}, Account: {user_id}"
        )

    clipboard_cmd = shutil.which("pbcopy")
    if clipboard_cmd:
        subprocess.run(
            [clipboard_cmd],
            input=key,
            check=True,
            text=True,
        )
        return "API key copied to the clipboard."

    raise RuntimeError("No secure output mechanism is available on this machine.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or reset a local API key")
    parser.add_argument("--user-id", default="local_dev", help="User ID for the key")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Revoke existing key before creating a new one",
    )
    args = parser.parse_args()

    if args.reset:
        api_key_store.revoke_key(args.user_id)

    key = get_or_create_api_key(args.user_id)
    if key:
        print(_store_key_securely(args.user_id, key))
        return 0

    print(
        "API key already exists for this user. "
        "Use --reset to revoke and create a new key."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
