"""
Persistent storage for deep research queries and results.

Primary storage is Postgres. In-memory fallback for local dev.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from src.db import execute as db_execute, fetch as db_fetch, fetchrow as db_fetchrow, is_database_configured

logger = logging.getLogger(__name__)

_queries: dict[str, dict[str, Any]] = {}
_db_enabled = is_database_configured()
_schema_ready = False
_schema_lock = asyncio.Lock()

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS research_queries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    depth TEXT NOT NULL DEFAULT 'basic',
    results_json JSONB,
    summary TEXT DEFAULT '',
    total_sources INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL REFERENCES research_queries(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    quality_score REAL DEFAULT 0,
    credibility_tier TEXT DEFAULT 'unknown',
    quality_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


async def _ensure_schema() -> None:
    global _schema_ready
    if _schema_ready or not _db_enabled:
        return
    async with _schema_lock:
        if _schema_ready:
            return
        try:
            for statement in _SCHEMA_SQL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    await db_execute(statement + ";")
            _schema_ready = True
            logger.info("Research store schema initialized")
        except Exception as e:
            logger.warning("Failed to initialize research schema: %s", e)


async def save_research(
    user_id: str,
    query: str,
    keywords: list[str],
    depth: str,
    sources: list[dict[str, Any]],
    summary: str = "",
) -> str:
    """Save a research query and its sources. Returns the query ID."""
    query_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": query_id,
        "user_id": user_id,
        "query": query,
        "keywords": keywords,
        "depth": depth,
        "sources": sources,
        "summary": summary,
        "total_sources": len(sources),
        "created_at": now,
    }
    _queries[query_id] = record

    if _db_enabled:
        await _ensure_schema()
        try:
            await db_execute(
                """INSERT INTO research_queries (id, user_id, query, keywords, depth, results_json, summary, total_sources)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                query_id, user_id, query, keywords, depth,
                json.dumps(sources), summary, len(sources),
            )
            for src in sources:
                src_id = str(uuid.uuid4())
                quality = src.get("quality", {})
                await db_execute(
                    """INSERT INTO research_sources (id, query_id, url, title, snippet, provider, quality_score, credibility_tier, quality_json)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    src_id, query_id,
                    src.get("url", ""), src.get("title", ""),
                    src.get("snippet", ""), src.get("provider", ""),
                    quality.get("overall", 0), quality.get("credibility_tier", "unknown"),
                    json.dumps(quality),
                )
        except Exception as e:
            logger.warning("Failed to persist research to DB: %s", e)

    return query_id


async def get_cached_research(
    query: str,
    depth: str,
    max_age_hours: int = 24,
) -> Optional[dict[str, Any]]:
    """Return cached research if a recent matching query exists."""
    # Check in-memory first
    for record in _queries.values():
        if record["query"] == query and record["depth"] == depth:
            return record

    if not _db_enabled:
        return None

    await _ensure_schema()
    try:
        row = await db_fetchrow(
            """SELECT * FROM research_queries
               WHERE query = $1 AND depth = $2
                 AND created_at > NOW() - INTERVAL '1 hour' * $3
               ORDER BY created_at DESC LIMIT 1""",
            query, depth, max_age_hours,
        )
        if row:
            results = row["results_json"]
            if isinstance(results, str):
                results = json.loads(results)
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "query": row["query"],
                "depth": row["depth"],
                "sources": results or [],
                "summary": row["summary"] or "",
                "total_sources": row["total_sources"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
    except Exception as e:
        logger.warning("Failed to check research cache: %s", e)

    return None


async def list_research_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List past research queries for a user."""
    if _db_enabled:
        await _ensure_schema()
        try:
            rows = await db_fetch(
                """SELECT id, query, depth, total_sources, summary, created_at
                   FROM research_queries
                   WHERE user_id = $1
                   ORDER BY created_at DESC
                   LIMIT $2 OFFSET $3""",
                user_id, limit, offset,
            )
            return [
                {
                    "id": r["id"],
                    "query": r["query"],
                    "depth": r["depth"],
                    "total_sources": r["total_sources"],
                    "summary": (r["summary"] or "")[:200],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning("Failed to list research history: %s", e)

    # Fallback: in-memory records for this user
    user_records = [
        r for r in _queries.values() if r["user_id"] == user_id
    ]
    user_records.sort(key=lambda r: r["created_at"], reverse=True)
    return user_records[offset:offset + limit]
