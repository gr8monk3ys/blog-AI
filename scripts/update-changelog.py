#!/usr/bin/env python3
"""Update CHANGELOG.md with new version information.

This script helps maintain the CHANGELOG.md file following Keep a Changelog format.
Run: python scripts/update-changelog.py
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def read_changelog() -> str:
    """Read current CHANGELOG.md content."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("❌ CHANGELOG.md not found")
        sys.exit(1)

    with open(changelog_path, encoding="utf-8") as f:
        return f.read()


def write_changelog(content: str):
    """Write updated CHANGELOG.md."""
    changelog_path = Path("CHANGELOG.md")
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated {changelog_path}")


def get_version_from_pyproject() -> str:
    """Extract current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return "unknown"

    with open(pyproject_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("version"):
                match = re.search(r'"([^"]+)"', line)
                if match:
                    return match.group(1)
    return "unknown"


def add_unreleased_section(content: str) -> str:
    """Add or ensure Unreleased section exists."""
    unreleased_pattern = r"## \[Unreleased\]"

    if re.search(unreleased_pattern, content):
        print("ℹ️  Unreleased section already exists")
        return content

    # Find where to insert (after header, before first version)
    version_pattern = r"## \[\d+\.\d+\.\d+\]"
    match = re.search(version_pattern, content)

    if match:
        insert_pos = match.start()
        unreleased_section = """## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

### Deprecated
-

### Removed
-

### Security
-

"""
        content = content[:insert_pos] + unreleased_section + content[insert_pos:]
        print("✅ Added Unreleased section")
    else:
        print("⚠️  Could not find version pattern to insert Unreleased section")

    return content


def release_unreleased(version: str, content: str) -> str:
    """Convert Unreleased section to a versioned release."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Replace [Unreleased] with [version] - date
    content = re.sub(
        r"## \[Unreleased\]",
        f"## [{version}] - {today}",
        content,
        count=1,
    )

    # Add new Unreleased section at the top
    version_pattern = r"(## \[" + re.escape(version) + r"\])"
    match = re.search(version_pattern, content)

    if match:
        insert_pos = match.start()
        unreleased_section = """## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

"""
        content = content[:insert_pos] + unreleased_section + content[insert_pos:]

    return content


def clean_empty_sections(content: str) -> str:
    """Remove empty changelog sections."""
    # Pattern for section headers with only a dash
    pattern = r"### (Added|Changed|Fixed|Deprecated|Removed|Security)\n-\n\n"
    content = re.sub(pattern, "", content)
    return content


def interactive_mode():
    """Interactive mode for updating changelog."""
    print("=" * 70)
    print("📝 CHANGELOG.md Update Helper")
    print("=" * 70)

    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Run from project root.")
        sys.exit(1)

    current_version = get_version_from_pyproject()
    print(f"\nCurrent version (from pyproject.toml): {current_version}")

    print("\nWhat would you like to do?")
    print("1. Add Unreleased section")
    print("2. Release current Unreleased as new version")
    print("3. Clean empty sections")
    print("4. View current changelog")
    print("5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    content = read_changelog()

    if choice == "1":
        content = add_unreleased_section(content)
        write_changelog(content)

    elif choice == "2":
        new_version = input(f"Enter version to release [{current_version}]: ").strip()
        if not new_version:
            new_version = current_version

        confirm = input(f"Release Unreleased as {new_version}? (y/n): ").strip()
        if confirm.lower() == "y":
            content = release_unreleased(new_version, content)
            content = clean_empty_sections(content)
            write_changelog(content)
            print(f"\n✅ Released version {new_version}")
            print("\nNext steps:")
            print(f"1. Review CHANGELOG.md")
            print(f"2. Update version in pyproject.toml to {new_version}")
            print(f"3. Commit changes: git commit -m 'Release v{new_version}'")
            print(f"4. Tag release: git tag -a v{new_version} -m 'Version {new_version}'")
        else:
            print("Cancelled")

    elif choice == "3":
        content = clean_empty_sections(content)
        write_changelog(content)
        print("✅ Cleaned empty sections")

    elif choice == "4":
        print("\n" + "=" * 70)
        print("Current CHANGELOG.md:")
        print("=" * 70)
        print(content)

    elif choice == "5":
        print("Exiting...")
        sys.exit(0)

    else:
        print("Invalid choice")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--release":
        # Non-interactive mode
        if len(sys.argv) < 3:
            print("Usage: python scripts/update-changelog.py --release VERSION")
            sys.exit(1)

        version = sys.argv[2]
        content = read_changelog()
        content = release_unreleased(version, content)
        content = clean_empty_sections(content)
        write_changelog(content)
        print(f"✅ Released version {version}")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
