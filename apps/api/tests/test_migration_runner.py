import pytest
from pathlib import Path

def test_get_pending_migrations_returns_sorted_excluding_rollbacks():
    """Migration runner should return sorted SQL files excluding rollbacks."""
    from server import get_pending_migrations

    migrations = get_pending_migrations("migrations")
    filenames = [m.name for m in migrations]

    assert "001_create_webhook_tables.sql" in filenames
    assert "002_knowledge_base.sql" in filenames
    # Rollback files should be excluded
    assert all("rollback" not in f for f in filenames)
    # Should be sorted
    assert filenames == sorted(filenames)

def test_get_pending_migrations_empty_dir(tmp_path):
    """Should return empty list for non-existent directory."""
    from server import get_pending_migrations

    result = get_pending_migrations(str(tmp_path / "nonexistent"))
    assert result == []
