"""
The version the API reports must be the one release-please maintains.

/health and / used to answer a hard-coded "1.0.0" while pyproject.toml said
0.0.0, so the one field an operator would compare against a GitHub release was
wrong on every deploy.

Environment for importing `server` (DEV_API_KEY, a mock LLM key, ...) is set
by tests/conftest.py before this module is collected.
"""

import importlib.metadata
import sys
import tomllib
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

from app.version import (
    PYPROJECT_PATH,
    UNKNOWN_VERSION,
    __version__,
    read_pyproject_version,
    resolve_version,
)


def _pyproject_version() -> str:
    with (API_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_pyproject_path_points_at_the_api_project():
    assert PYPROJECT_PATH == API_ROOT / "pyproject.toml"
    assert PYPROJECT_PATH.is_file()


def test_version_matches_pyproject():
    assert __version__ == _pyproject_version()


def test_resolve_version_prefers_installed_metadata(monkeypatch):
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "9.8.7")
    assert resolve_version() == "9.8.7"


def test_resolve_version_falls_back_to_pyproject_when_not_installed(monkeypatch):
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    assert resolve_version() == _pyproject_version()


def test_resolve_version_never_raises(monkeypatch, tmp_path):
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)

    assert resolve_version(pyproject=tmp_path / "absent.toml") == UNKNOWN_VERSION

    broken = tmp_path / "broken.toml"
    broken.write_text("[project\nversion = ", encoding="utf-8")
    assert read_pyproject_version(broken) is None

    no_version = tmp_path / "no-version.toml"
    no_version.write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert read_pyproject_version(no_version) is None


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from server import app

    return TestClient(app)


def test_health_and_root_report_the_pyproject_version(client):
    expected = _pyproject_version()

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == expected

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["version"] == expected

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert openapi.json()["info"]["version"] == expected
