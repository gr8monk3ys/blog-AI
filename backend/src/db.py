"""
Async Postgres helpers for Neon (or any Postgres).

This project previously used Supabase's PostgREST client for persistence.
For a Neon-only setup we connect directly to Postgres.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


def get_database_url() -> Optional[str]:
    """
    Prefer a direct (non-pooler) URL for long-lived backends if provided.

    Vercel/serverless should typically use a pooler URL.
    """
    return os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")


def is_database_configured() -> bool:
    return bool(get_database_url())


async def get_pool() -> Optional[asyncpg.Pool]:
    global _pool
    if _pool is not None:
        return _pool

    dsn = get_database_url()
    if not dsn:
        return None

    min_size = int(os.environ.get("DATABASE_POOL_MIN_SIZE", "1"))
    max_size = int(os.environ.get("DATABASE_POOL_MAX_SIZE", "5"))

    # If you're connecting via a PgBouncer pooler, prepared statements can break.
    # Disabling the statement cache keeps behavior consistent for both direct and pooled URLs.
    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
        statement_cache_size=0,
    )

    logger.info("Postgres pool initialized (min=%s max=%s)", min_size, max_size)
    return _pool


async def fetchrow(query: str, *args):
    pool = await get_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch(query: str, *args):
    pool = await get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args):
    pool = await get_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def close_pool() -> None:
    """Close the global asyncpg pool (used during graceful shutdown)."""
    global _pool
    if _pool is None:
        return
    try:
        await _pool.close()
    finally:
        _pool = None
