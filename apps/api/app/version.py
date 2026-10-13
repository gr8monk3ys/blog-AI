"""
The API's version, read from the one place release-please writes it.

`/health` and `/` used to report a hard-coded ``"1.0.0"`` while
``pyproject.toml`` said ``0.0.0`` and the GitHub release said something else
again. release-please bumps ``[project] version`` in ``apps/api/pyproject.toml``
on every release, so that file is the source of truth.

Resolution order:

1. ``importlib.metadata.version("blog-ai-api")`` -- present when the project is
   installed as a distribution.
2. ``[project] version`` in ``pyproject.toml`` -- the normal case: the API is
   ``package = false`` under uv (an application, never built), so there is no
   distribution metadata on a laptop, in CI or on Vercel, and the file is read
   directly instead.
3. ``"unknown"`` -- the file is missing or malformed. Never raises at import.
"""

from __future__ import annotations

import importlib.metadata
import tomllib
from pathlib import Path

DISTRIBUTION_NAME = "blog-ai-api"
UNKNOWN_VERSION = "unknown"

# apps/api/app/version.py -> apps/api/pyproject.toml
PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


def read_pyproject_version(path: Path = PYPROJECT_PATH) -> str | None:
    """Return ``[project] version`` from *path*, or None if it cannot be read."""
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    version = data.get("project", {}).get("version")
    return version if isinstance(version, str) and version.strip() else None


def resolve_version(
    distribution: str = DISTRIBUTION_NAME, pyproject: Path = PYPROJECT_PATH
) -> str:
    """Resolve the running API's version without ever raising."""
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        pass
    return read_pyproject_version(pyproject) or UNKNOWN_VERSION


__version__ = resolve_version()
