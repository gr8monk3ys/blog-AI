#!/usr/bin/env python3
"""Bump version number in pyproject.toml.

This script helps manage semantic versioning.
Run: python scripts/bump-version.py [major|minor|patch]
"""

import re
import sys
from pathlib import Path


def read_pyproject() -> str:
    """Read pyproject.toml content."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        sys.exit(1)

    with open(pyproject_path, encoding="utf-8") as f:
        return f.read()


def write_pyproject(content: str):
    """Write updated pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated {pyproject_path}")


def get_current_version(content: str) -> str:
    """Extract current version from pyproject.toml."""
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.1.0"


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string."""
    try:
        parts = version.split(".")
        return int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        print(f"❌ Invalid version format: {version}")
        sys.exit(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to type."""
    major, minor, patch = parse_version(version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"❌ Invalid bump type: {bump_type}")
        print("Valid types: major, minor, patch")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def update_version_in_content(content: str, new_version: str) -> str:
    """Update version in pyproject.toml content."""
    return re.sub(
        r'version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        count=1,
    )


def interactive_mode():
    """Interactive version bump."""
    print("=" * 70)
    print("🔢 Version Bump Helper")
    print("=" * 70)

    content = read_pyproject()
    current = get_current_version(content)

    print(f"\nCurrent version: {current}")

    major, minor, patch = parse_version(current)
    print("\nAvailable bumps:")
    print(f"  1. Major ({major + 1}.0.0) - Breaking changes")
    print(f"  2. Minor ({major}.{minor + 1}.0) - New features")
    print(f"  3. Patch ({major}.{minor}.{patch + 1}) - Bug fixes")
    print("  4. Custom version")
    print("  5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        bump_type = "major"
        new_version = bump_version(current, bump_type)
    elif choice == "2":
        bump_type = "minor"
        new_version = bump_version(current, bump_type)
    elif choice == "3":
        bump_type = "patch"
        new_version = bump_version(current, bump_type)
    elif choice == "4":
        new_version = input("Enter custom version: ").strip()
        # Validate format
        try:
            parse_version(new_version)
        except SystemExit:
            print("❌ Invalid version format. Must be X.Y.Z")
            sys.exit(1)
    elif choice == "5":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)

    print(f"\nVersion change: {current} → {new_version}")
    confirm = input("Confirm? (y/n): ").strip()

    if confirm.lower() == "y":
        new_content = update_version_in_content(content, new_version)
        write_pyproject(new_content)
        print(f"\n✅ Version bumped to {new_version}")

        print("\nNext steps:")
        print("1. Update CHANGELOG.md: python scripts/update-changelog.py")
        print("2. Review changes")
        print(f"3. Commit: git commit -am 'Bump version to {new_version}'")
        print(f"4. Tag: git tag -a v{new_version} -m 'Version {new_version}'")
        print("5. Push: git push origin main --tags")
    else:
        print("Cancelled")


def main():
    """Main entry point."""
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Run from project root.")
        sys.exit(1)

    if len(sys.argv) > 1:
        # Non-interactive mode
        bump_type = sys.argv[1].lower()
        content = read_pyproject()
        current = get_current_version(content)
        new_version = bump_version(current, bump_type)

        print(f"Bumping version: {current} → {new_version}")

        new_content = update_version_in_content(content, new_version)
        write_pyproject(new_content)
        print(f"✅ Version bumped to {new_version}")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
