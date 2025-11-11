#!/usr/bin/env python3
"""Development environment setup script for blog-AI.

This script helps developers set up their environment quickly.
Run: python scripts/dev-setup.py
"""

import os
import subprocess
import sys
from pathlib import Path


def print_step(step: str, emoji: str = "🔧"):
    """Print a formatted step message."""
    print(f"\n{emoji} {step}")
    print("-" * 60)


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Run development environment setup."""
    print("=" * 60)
    print("🚀 blog-AI Development Environment Setup")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run this from the project root.")
        sys.exit(1)

    # Step 1: Check Python version
    print_step("Checking Python version", "🐍")
    python_version = sys.version_info
    print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 12):
        print("⚠️  Warning: Python 3.12+ is recommended")
    else:
        print("✅ Python version OK")

    # Step 2: Install uv if not present
    print_step("Checking uv package manager", "📦")
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ uv is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  uv not found. Install from: https://github.com/astral-sh/uv")
        response = input("Continue without uv? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)

    # Step 3: Install dependencies
    print_step("Installing dependencies", "📚")
    if not run_command("uv sync --all-extras", "Install all dependencies"):
        print("⚠️  Failed to install dependencies with uv")

    # Step 4: Install pre-commit hooks
    print_step("Setting up pre-commit hooks", "🪝")
    if Path(".pre-commit-config.yaml").exists():
        if run_command("uv run pre-commit install", "Install pre-commit hooks"):
            print("✅ Pre-commit hooks installed")
        else:
            print("⚠️  Pre-commit hooks not installed (optional)")
    else:
        print("⚠️  .pre-commit-config.yaml not found")

    # Step 5: Create .env file if missing
    print_step("Checking environment configuration", "⚙️")
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("Creating .env from .env.example...")
            with open(".env.example") as f:
                content = f.read()
            with open(".env", "w") as f:
                f.write(content)
            print("✅ .env file created")
            print("⚠️  Remember to add your OPENAI_API_KEY to .env")
        else:
            print("⚠️  .env.example not found")
    else:
        print("✅ .env file already exists")

    # Step 6: Run quick validation
    print_step("Running quick validation", "✓")
    if run_command("python test_quick.py", "Quick validation test"):
        print("✅ Quick validation passed")
    else:
        print("⚠️  Quick validation failed (check for API key)")

    # Final summary
    print("\n" + "=" * 60)
    print("✅ Development environment setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add your OPENAI_API_KEY to .env file")
    print("2. Run tests: make test")
    print("3. Run linting: uv run ruff check src/ tests/")
    print("4. Run type checking: uv run mypy src/")
    print("\nHappy coding! 🎉")


if __name__ == "__main__":
    main()
