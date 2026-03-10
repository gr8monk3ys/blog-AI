"""
Database initialization for organization tables.

On startup, ensures the organization schema exists.
"""

import asyncio
import logging

from src.db import execute as db_execute, is_database_configured

logger = logging.getLogger(__name__)

_schema_ready = False
_schema_lock = asyncio.Lock()

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    plan_tier TEXT NOT NULL DEFAULT 'free',
    stripe_customer_id TEXT,
    settings JSONB DEFAULT '{}',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS organization_members (
    org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by TEXT,
    PRIMARY KEY (org_id, user_id)
);
CREATE TABLE IF NOT EXISTS organization_invites (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by TEXT
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    changes JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


async def ensure_org_schema() -> bool:
    """Ensure organization tables exist. Returns True if ready."""
    global _schema_ready
    if _schema_ready:
        return True
    if not is_database_configured():
        logger.warning("DATABASE_URL not set -- organization features require a database")
        return False

    async with _schema_lock:
        if _schema_ready:
            return True
        try:
            for statement in _SCHEMA_SQL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    await db_execute(statement + ";")
            _schema_ready = True
            logger.info("Organization schema initialized")
            return True
        except Exception as e:
            logger.error("Failed to initialize organization schema: %s", e)
            return False
