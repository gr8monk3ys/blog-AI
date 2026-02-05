"""
Create or reset a local API key for development/testing.

Usage:
  python scripts/create_api_key.py --user-id local_dev
  python scripts/create_api_key.py --user-id local_dev --reset
"""

from __future__ import annotations

import argparse

from app.auth.api_key import api_key_store, get_or_create_api_key


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
        print(key)
        return 0

    print(
        "API key already exists for this user. "
        "Use --reset to revoke and create a new key."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
