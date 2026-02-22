"""
Persistent storage helpers for workflow definitions and executions.

Primary storage is Postgres (Neon). In-memory mirrors are kept as a fallback
for local development/tests when DATABASE_URL is not configured.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.db import execute as db_execute, fetchrow as db_fetchrow, is_database_configured

logger = logging.getLogger(__name__)

# In-memory fallback mirrors.
_workflows: Dict[str, Dict[str, Any]] = {}
_executions: Dict[str, Dict[str, Any]] = {}

_db_enabled = is_database_configured()
_schema_ready = False
_schema_lock = asyncio.Lock()


def _as_iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _normalize_workflow(row: Any) -> Dict[str, Any]:
    steps = row["steps"] if row["steps"] is not None else []
    if isinstance(steps, str):
        try:
            steps = json.loads(steps)
        except json.JSONDecodeError:
            steps = []

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "steps": steps,
        "created_by": row["user_id"],
        "created_at": _as_iso(row["created_at"]),
    }


def _normalize_execution(row: Any) -> Dict[str, Any]:
    results = row["results"] if row["results"] is not None else {}
    if isinstance(results, str):
        try:
            results = json.loads(results)
        except json.JSONDecodeError:
            results = {}

    return {
        "execution_id": row["execution_id"],
        "workflow_id": row["workflow_id"],
        "workflow_name": row["workflow_name"],
        "status": row["status"],
        "current_step": row["current_step"],
        "started_at": _as_iso(row["started_at"]),
        "completed_at": _as_iso(row["completed_at"]),
        "error": row["error"],
        "results": results,
        "user_id": row["user_id"],
    }


async def _ensure_schema() -> bool:
    global _schema_ready, _db_enabled

    if not _db_enabled:
        return False
    if _schema_ready:
        return True

    async with _schema_lock:
        if _schema_ready:
            return True
        if not _db_enabled:
            return False

        try:
            await db_execute(
                """
                CREATE TABLE IF NOT EXISTS app_workflows (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_workflows_user_id
                ON app_workflows (user_id)
                """
            )
            await db_execute(
                """
                CREATE TABLE IF NOT EXISTS app_workflow_executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    completed_at TIMESTAMPTZ,
                    error TEXT,
                    results JSONB NOT NULL DEFAULT '{}'::jsonb,
                    provider TEXT,
                    variables JSONB NOT NULL DEFAULT '{}'::jsonb
                )
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_workflow_exec_workflow_started
                ON app_workflow_executions (workflow_id, started_at DESC)
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_workflow_exec_user_started
                ON app_workflow_executions (user_id, started_at DESC)
                """
            )
            _schema_ready = True
        except Exception as exc:
            logger.warning(
                "Workflow DB persistence unavailable, falling back to in-memory only: %s",
                exc,
            )
            _db_enabled = False
            return False

    return True


async def save_workflow(workflow_data: Dict[str, Any]) -> None:
    """Persist a custom workflow definition."""
    _workflows[workflow_data["id"]] = dict(workflow_data)

    if not await _ensure_schema():
        return

    try:
        await db_execute(
            """
            INSERT INTO app_workflows (
                id, user_id, name, description, steps, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::timestamptz, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                steps = EXCLUDED.steps,
                updated_at = NOW()
            """,
            workflow_data["id"],
            workflow_data["created_by"],
            workflow_data["name"],
            workflow_data.get("description", ""),
            json.dumps(workflow_data.get("steps", [])),
            workflow_data["created_at"],
        )
    except Exception as exc:
        logger.warning("Failed to persist workflow %s: %s", workflow_data["id"], exc)


async def get_workflow(workflow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get a workflow by id (optionally scoped to a user)."""
    wf = _workflows.get(workflow_id)
    if wf and (user_id is None or wf.get("created_by") == user_id):
        return wf

    if not await _ensure_schema():
        return wf if user_id is None or (wf and wf.get("created_by") == user_id) else None

    try:
        if user_id:
            row = await db_fetchrow(
                """
                SELECT id, user_id, name, description, steps, created_at
                FROM app_workflows
                WHERE id = $1 AND user_id = $2
                """,
                workflow_id,
                user_id,
            )
        else:
            row = await db_fetchrow(
                """
                SELECT id, user_id, name, description, steps, created_at
                FROM app_workflows
                WHERE id = $1
                """,
                workflow_id,
            )
    except Exception as exc:
        logger.warning("Failed loading workflow %s from DB: %s", workflow_id, exc)
        return wf if user_id is None or (wf and wf.get("created_by") == user_id) else None

    if not row:
        return wf if user_id is None or (wf and wf.get("created_by") == user_id) else None

    normalized = _normalize_workflow(row)
    _workflows[workflow_id] = normalized
    return normalized


async def create_execution(record: Dict[str, Any], variables: Optional[Dict[str, Any]] = None, provider: Optional[str] = None) -> None:
    """Persist a workflow execution record."""
    _executions[record["execution_id"]] = dict(record)

    if not await _ensure_schema():
        return

    try:
        await db_execute(
            """
            INSERT INTO app_workflow_executions (
                execution_id,
                workflow_id,
                workflow_name,
                user_id,
                status,
                current_step,
                started_at,
                completed_at,
                error,
                results,
                provider,
                variables
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::timestamptz, $8::timestamptz, $9, $10::jsonb, $11, $12::jsonb
            )
            ON CONFLICT (execution_id) DO NOTHING
            """,
            record["execution_id"],
            record["workflow_id"],
            record["workflow_name"],
            record["user_id"],
            record["status"],
            record.get("current_step"),
            record.get("started_at"),
            record.get("completed_at"),
            record.get("error"),
            json.dumps(record.get("results", {})),
            provider,
            json.dumps(variables or {}),
        )
    except Exception as exc:
        logger.warning("Failed to persist execution %s: %s", record["execution_id"], exc)


async def get_execution(execution_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get an execution by id (optionally scoped to user)."""
    record = _executions.get(execution_id)
    if record and (user_id is None or record.get("user_id") == user_id):
        return record

    if not await _ensure_schema():
        return record if user_id is None or (record and record.get("user_id") == user_id) else None

    try:
        if user_id:
            row = await db_fetchrow(
                """
                SELECT execution_id, workflow_id, workflow_name, user_id, status, current_step,
                       started_at, completed_at, error, results
                FROM app_workflow_executions
                WHERE execution_id = $1 AND user_id = $2
                """,
                execution_id,
                user_id,
            )
        else:
            row = await db_fetchrow(
                """
                SELECT execution_id, workflow_id, workflow_name, user_id, status, current_step,
                       started_at, completed_at, error, results
                FROM app_workflow_executions
                WHERE execution_id = $1
                """,
                execution_id,
            )
    except Exception as exc:
        logger.warning("Failed loading execution %s from DB: %s", execution_id, exc)
        return record if user_id is None or (record and record.get("user_id") == user_id) else None

    if not row:
        return record if user_id is None or (record and record.get("user_id") == user_id) else None

    normalized = _normalize_execution(row)
    _executions[execution_id] = normalized
    return normalized


async def get_latest_execution_for_workflow(
    workflow_id: str,
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get most recent execution for a workflow id."""
    # Prefer in-memory lookup first (covers currently running executions).
    for exec_record in reversed(list(_executions.values())):
        if exec_record.get("workflow_id") != workflow_id:
            continue
        if user_id and exec_record.get("user_id") != user_id:
            continue
        return exec_record

    if not await _ensure_schema():
        return None

    try:
        if user_id:
            row = await db_fetchrow(
                """
                SELECT execution_id, workflow_id, workflow_name, user_id, status, current_step,
                       started_at, completed_at, error, results
                FROM app_workflow_executions
                WHERE workflow_id = $1 AND user_id = $2
                ORDER BY started_at DESC
                LIMIT 1
                """,
                workflow_id,
                user_id,
            )
        else:
            row = await db_fetchrow(
                """
                SELECT execution_id, workflow_id, workflow_name, user_id, status, current_step,
                       started_at, completed_at, error, results
                FROM app_workflow_executions
                WHERE workflow_id = $1
                ORDER BY started_at DESC
                LIMIT 1
                """,
                workflow_id,
            )
    except Exception as exc:
        logger.warning(
            "Failed loading latest execution for workflow %s from DB: %s",
            workflow_id,
            exc,
        )
        return None

    if not row:
        return None

    normalized = _normalize_execution(row)
    _executions[normalized["execution_id"]] = normalized
    return normalized


async def update_execution(execution_id: str, **updates: Any) -> Optional[Dict[str, Any]]:
    """Update execution fields and persist."""
    current = await get_execution(execution_id)
    if not current:
        return None

    current.update(updates)
    _executions[execution_id] = current

    if not await _ensure_schema():
        return current

    try:
        await db_execute(
            """
            UPDATE app_workflow_executions
            SET
                status = $2,
                current_step = $3,
                completed_at = $4::timestamptz,
                error = $5,
                results = $6::jsonb
            WHERE execution_id = $1
            """,
            execution_id,
            current.get("status"),
            current.get("current_step"),
            current.get("completed_at"),
            current.get("error"),
            json.dumps(current.get("results", {})),
        )
    except Exception as exc:
        logger.warning("Failed updating execution %s in DB: %s", execution_id, exc)

    return current

