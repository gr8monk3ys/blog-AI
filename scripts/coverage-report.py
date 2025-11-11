#!/usr/bin/env python3
"""Generate comprehensive code coverage report for blog-AI.

Runs tests and generates both terminal and HTML coverage reports.
Run: python scripts/coverage-report.py
"""

import subprocess
import sys
import webbrowser
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"📊 {text}")
    print("=" * 70 + "\n")


def run_coverage():
    """Run tests with coverage tracking."""
    print_header("Running Tests with Coverage")

    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
    ]

    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return False


def analyze_coverage():
    """Analyze coverage results and print summary."""
    print_header("Coverage Analysis")

    coverage_file = Path("coverage.xml")
    htmlcov_dir = Path("htmlcov")

    if not coverage_file.exists():
        print("❌ Coverage file not found. Tests may have failed.")
        return False

    # Parse coverage percentage from terminal output
    # (already shown by pytest-cov)

    if htmlcov_dir.exists():
        index_file = htmlcov_dir / "index.html"
        if index_file.exists():
            print(f"✅ HTML coverage report generated: {index_file}")
            print(f"   Open in browser: file://{index_file.absolute()}")
        else:
            print("⚠️  HTML report directory exists but index.html not found")
    else:
        print("⚠️  HTML coverage directory not found")

    if coverage_file.exists():
        print(f"✅ XML coverage report generated: {coverage_file}")
        print("   (Used by CI/CD and code coverage tools)")
    else:
        print("⚠️  XML coverage file not found")

    return True


def show_coverage_tips():
    """Show tips for improving coverage."""
    print_header("Coverage Tips")

    tips = [
        "🎯 Target: Aim for 80%+ overall coverage",
        "📝 Focus on critical paths: generators, formatters, models",
        "🧪 Add edge case tests for error handling",
        "🔧 Use 'pytest --cov-report=html' to see line-by-line coverage",
        "📊 Review htmlcov/index.html for detailed coverage analysis",
        "⚠️  100% coverage is not always necessary (e.g., defensive code)",
        "🔍 Identify untested code: look for 0% coverage files",
    ]

    for tip in tips:
        print(f"  {tip}")


def open_html_report():
    """Open HTML coverage report in browser."""
    htmlcov_dir = Path("htmlcov")
    index_file = htmlcov_dir / "index.html"

    if index_file.exists():
        response = input("\n🌐 Open HTML report in browser? (y/n): ")
        if response.lower() == "y":
            webbrowser.open(f"file://{index_file.absolute()}")
            print("✅ Opened coverage report in browser")
        else:
            print(f"   You can open it manually: file://{index_file.absolute()}")
    else:
        print("❌ HTML report not found")


def main():
    """Main coverage report generation."""
    print("=" * 70)
    print("🧪 blog-AI Code Coverage Report Generator")
    print("=" * 70)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run this from the project root.")
        sys.exit(1)

    # Run coverage
    success = run_coverage()

    if not success:
        print("\n⚠️  Some tests failed. Coverage report may be incomplete.")
        sys.exit(1)

    # Analyze results
    analyze_coverage()

    # Show tips
    show_coverage_tips()

    # Offer to open HTML report
    open_html_report()

    # Summary
    print("\n" + "=" * 70)
    print("✅ Coverage Report Complete")
    print("=" * 70)

    print("\nCoverage files generated:")
    print("  - htmlcov/index.html  (detailed line-by-line coverage)")
    print("  - coverage.xml        (for CI/CD integration)")
    print("\nNext steps:")
    print("  1. Review coverage report")
    print("  2. Identify untested code")
    print("  3. Add tests for critical paths")
    print("  4. Re-run to verify improvements")


if __name__ == "__main__":
    main()
