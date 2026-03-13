"""
Create or reset a local API key for development/testing.

Usage:
  python scripts/create_api_key.py --user-id local_dev
  python scripts/create_api_key.py --user-id local_dev --reset
  python scripts/create_api_key.py --user-id local_dev --output-file .local/local_dev.api-key
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.auth.api_key import api_key_store, get_or_create_api_key


def _default_output_file(user_id: str) -> Path:
    return Path(".local/api-keys") / f"{user_id}.txt"


def _write_key_file(path: Path, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{key}\n", encoding="utf-8")
    path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or reset a local API key")
    parser.add_argument("--user-id", default="local_dev", help="User ID for the key")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Revoke existing key before creating a new one",
    )
    parser.add_argument(
        "--output-file",
        help="Write the generated API key to this file with 0600 permissions",
    )
    args = parser.parse_args()

    if args.reset:
        api_key_store.revoke_key(args.user_id)

    key = get_or_create_api_key(args.user_id)
    if key:
        output_path = Path(args.output_file) if args.output_file else _default_output_file(args.user_id)
        _write_key_file(output_path, key)
        print(f"API key written to {output_path} with 0600 permissions.")
        return 0

    print(
        "API key already exists for this user. "
        "Use --reset to revoke and create a new key."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
