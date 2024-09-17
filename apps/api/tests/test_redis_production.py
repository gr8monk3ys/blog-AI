"""
Tests for Redis production-mode enforcement in RedisClient.

Because src/storage/redis_client.py creates a module-level singleton
(redis_client = RedisClient()) that runs at import time, in production mode
without REDIS_URL the module itself raises RuntimeError on import.

We load the submodule in isolation (bypassing the package __init__ to avoid
the package-level singleton instantiation) and assert the correct behaviour.
"""

import importlib
import importlib.util
import os
import sys
import types
import pytest
from pathlib import Path
from unittest.mock import patch

_REDIS_CLIENT_PATH = (
    Path(__file__).parent.parent / "src" / "storage" / "redis_client.py"
)


def _load_redis_client_module(env: dict) -> types.ModuleType:
    """
    Load src.storage.redis_client in isolation (skipping package __init__)
    under the given environment dictionary.

    Raises whatever the module raises during loading (e.g. RuntimeError in
    production without REDIS_URL).
    """
    module_name = "src.storage.redis_client"

    # Remove any cached copy so we start fresh.
    for key in list(sys.modules):
        if key in (module_name, "src.storage"):
            del sys.modules[key]

    # Insert a stub for the package so Python won't run __init__.py.
    stub_pkg = types.ModuleType("src.storage")
    stub_pkg.__path__ = [str(_REDIS_CLIENT_PATH.parent)]
    stub_pkg.__package__ = "src.storage"
    sys.modules["src.storage"] = stub_pkg

    with patch.dict(os.environ, env, clear=True):
        spec = importlib.util.spec_from_file_location(
            module_name,
            str(_REDIS_CLIENT_PATH),
            submodule_search_locations=[],
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # may raise if env is misconfigured

    return mod


def test_redis_raises_in_production_without_url():
    """
    In production, importing the redis_client module (which creates the
    singleton at module level) must raise RuntimeError when REDIS_URL is unset.
    """
    env = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
    env["APP_ENV"] = "production"

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        _load_redis_client_module(env)


def test_redis_allows_localhost_in_development():
    """In development, localhost fallback is used when REDIS_URL is unset."""
    env = {k: v for k, v in os.environ.items() if k != "REDIS_URL"}
    env.pop("APP_ENV", None)

    mod = _load_redis_client_module(env)

    # The class should be importable and default to localhost
    client = mod.RedisClient()
    assert "localhost" in client.redis_url
