#!/usr/bin/env python3
"""Code quality check script for blog-AI.

Runs all quality checks in one command.
Run: python scripts/quality-check.py
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    """Result of a quality check."""

    name: str
    passed: bool
    output: str
    duration: float


def run_check(name: str, command: str) -> CheckResult:
    """Run a quality check command."""
    print(f"\n{'='*70}")
    print(f"🔍 {name}")
    print(f"{'='*70}")
    print(f"Command: {command}\n")

    import time

    start = time.time()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        duration = time.time() - start

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        passed = result.returncode == 0

        if passed:
            print(f"✅ {name} PASSED ({duration:.1f}s)")
        else:
            print(f"❌ {name} FAILED ({duration:.1f}s)")

        return CheckResult(
            name=name,
            passed=passed,
            output=result.stdout + result.stderr,
            duration=duration,
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        print(f"⏱️  {name} TIMEOUT ({duration:.1f}s)")
        return CheckResult(
            name=name, passed=False, output="Timeout", duration=duration
        )
    except Exception as e:
        duration = time.time() - start
        print(f"❌ {name} ERROR: {e}")
        return CheckResult(
            name=name, passed=False, output=str(e), duration=duration
        )


def main():
    """Run all quality checks."""
    print("=" * 70)
    print("🚀 blog-AI Code Quality Checks")
    print("=" * 70)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run this from the project root.")
        sys.exit(1)

    results: list[CheckResult] = []

    # 1. Code formatting check
    results.append(
        run_check(
            "Code Formatting (ruff format)",
            "uv run ruff format --check src/ tests/",
        )
    )

    # 2. Linting
    results.append(
        run_check(
            "Linting (ruff check)",
            "uv run ruff check src/ tests/",
        )
    )

    # 3. Type checking
    results.append(
        run_check(
            "Type Checking (mypy)",
            "uv run mypy src/",
        )
    )

    # 4. Security check
    results.append(
        run_check(
            "Security Scan (bandit)",
            "uv run bandit -r src/ -c pyproject.toml",
        )
    )

    # 5. Tests
    results.append(
        run_check(
            "Unit Tests (pytest)",
            "uv run pytest tests/unit/ -v --tb=short",
        )
    )

    # 6. Import sorting (check only)
    results.append(
        run_check(
            "Import Sorting",
            "uv run ruff check --select I src/ tests/",
        )
    )

    # Summary
    print("\n" + "=" * 70)
    print("📊 Quality Check Summary")
    print("=" * 70)

    total_duration = sum(r.duration for r in results)
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)

    print(f"\nTotal checks: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Total time: {total_duration:.1f}s\n")

    # Detailed results
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} {result.name:30} ({result.duration:.1f}s)")

    print("\n" + "=" * 70)

    if passed_count == total_count:
        print("🎉 All quality checks passed!")
        print("=" * 70)
        return 0
    else:
        print("⚠️  Some quality checks failed. Please fix the issues above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
