"""api/requirements.txt must list exactly what apps/api/requirements.txt lists.

The repo-root api/backend.py serves this app from the blog-ai web project and
Vercel installs only api/requirements.txt for it (its parser can't follow "-r"
includes, so the file is a copy). A dependency added here but not there would
fail at import time in production only.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _requirement_lines(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return sorted(lines)


def test_web_function_requirements_match_api_requirements() -> None:
    expected = _requirement_lines(REPO_ROOT / "apps" / "api" / "requirements.txt")
    actual = _requirement_lines(REPO_ROOT / "api" / "requirements.txt")
    assert actual == expected
