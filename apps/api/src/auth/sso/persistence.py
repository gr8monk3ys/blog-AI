"""
Postgres-backed persistence helpers for SSO runtime data.

This module stores:
- SSO configurations (org-level)
- SSO auth flow sessions (short-lived)
- SSO user sessions (login session state)
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.db import execute as db_execute, fetch as db_fetch, fetchrow as db_fetchrow, is_database_configured
from src.types.sso import SSOConfiguration, SSOSession

logger = logging.getLogger(__name__)

_db_enabled = is_database_configured()
_schema_ready = False
_schema_lock = asyncio.Lock()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def _payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


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
                CREATE TABLE IF NOT EXISTS app_sso_configurations (
                    organization_id TEXT PRIMARY KEY,
                    config_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            await db_execute(
                """
                CREATE TABLE IF NOT EXISTS app_sso_auth_sessions (
                    session_id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_sso_auth_sessions_expires
                ON app_sso_auth_sessions (expires_at)
                """
            )
            await db_execute(
                """
                CREATE TABLE IF NOT EXISTS app_sso_user_sessions (
                    session_id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_sso_user_sessions_org
                ON app_sso_user_sessions (organization_id, expires_at DESC)
                """
            )
            await db_execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_sso_user_sessions_expires
                ON app_sso_user_sessions (expires_at)
                """
            )
            _schema_ready = True
        except Exception as exc:
            logger.warning(
                "SSO DB persistence unavailable, falling back to cache/memory only: %s",
                exc,
            )
            _db_enabled = False
            return False

    return True


async def save_sso_config(config: SSOConfiguration) -> bool:
    """Persist an SSO configuration."""
    if not await _ensure_schema():
        return False
    try:
        payload = config.model_dump(mode="json", exclude_none=True)
        await db_execute(
            """
            INSERT INTO app_sso_configurations (
                organization_id,
                config_json,
                created_at,
                updated_at
            ) VALUES ($1, $2::jsonb, NOW(), NOW())
            ON CONFLICT (organization_id) DO UPDATE SET
                config_json = EXCLUDED.config_json,
                updated_at = NOW()
            """,
            config.organization_id,
            json.dumps(payload),
        )
        return True
    except Exception as exc:
        logger.warning(
            "Failed persisting SSO config for org %s: %s",
            config.organization_id,
            exc,
        )
        return False


async def load_sso_config(organization_id: str) -> Optional[SSOConfiguration]:
    """Load an SSO configuration for an organization."""
    if not await _ensure_schema():
        return None
    try:
        row = await db_fetchrow(
            """
            SELECT config_json
            FROM app_sso_configurations
            WHERE organization_id = $1
            """,
            organization_id,
        )
        if not row:
            return None
        payload = _payload_dict(row["config_json"])
        if not payload:
            return None
        return SSOConfiguration.model_validate(payload)
    except Exception as exc:
        logger.warning("Failed loading SSO config for org %s: %s", organization_id, exc)
        return None


async def delete_sso_config(organization_id: str) -> bool:
    """Delete an SSO configuration."""
    if not await _ensure_schema():
        return False
    try:
        await db_execute(
            """
            DELETE FROM app_sso_configurations
            WHERE organization_id = $1
            """,
            organization_id,
        )
        return True
    except Exception as exc:
        logger.warning("Failed deleting SSO config for org %s: %s", organization_id, exc)
        return False


async def store_auth_session(session_id: str, data: Dict[str, Any], ttl_seconds: int) -> bool:
    """Store short-lived auth session state."""
    if not await _ensure_schema():
        return False
    try:
        payload = dict(data)
        payload.setdefault("created_at", _utc_now().isoformat())
        expires_at = _utc_now() + timedelta(seconds=ttl_seconds)
        await db_execute(
            """
            INSERT INTO app_sso_auth_sessions (
                session_id, payload, created_at, expires_at
            ) VALUES ($1, $2::jsonb, NOW(), $3::timestamptz)
            ON CONFLICT (session_id) DO UPDATE SET
                payload = EXCLUDED.payload,
                expires_at = EXCLUDED.expires_at
            """,
            session_id,
            json.dumps(payload),
            expires_at.isoformat(),
        )
        return True
    except Exception as exc:
        logger.warning("Failed storing SSO auth session %s: %s", session_id, exc)
        return False


async def get_auth_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get short-lived auth session state."""
    if not session_id or not await _ensure_schema():
        return None
    try:
        row = await db_fetchrow(
            """
            SELECT payload, expires_at
            FROM app_sso_auth_sessions
            WHERE session_id = $1
            """,
            session_id,
        )
        if not row:
            return None
        expires_at = _to_datetime(row["expires_at"])
        if expires_at and expires_at <= _utc_now():
            await delete_auth_session(session_id)
            return None
        return _payload_dict(row["payload"])
    except Exception as exc:
        logger.warning("Failed reading SSO auth session %s: %s", session_id, exc)
        return None


async def delete_auth_session(session_id: str) -> None:
    """Delete auth session state."""
    if not session_id or not await _ensure_schema():
        return
    try:
        await db_execute(
            """
            DELETE FROM app_sso_auth_sessions
            WHERE session_id = $1
            """,
            session_id,
        )
    except Exception as exc:
        logger.warning("Failed deleting SSO auth session %s: %s", session_id, exc)


async def store_user_session(session_id: str, session: SSOSession, ttl_seconds: int) -> bool:
    """Persist logged-in SSO user session."""
    if not await _ensure_schema():
        return False
    try:
        payload = session.model_dump(mode="json", exclude_none=True)
        expires_at = _to_datetime(payload.get("expires_at")) or (_utc_now() + timedelta(seconds=ttl_seconds))
        await db_execute(
            """
            INSERT INTO app_sso_user_sessions (
                session_id,
                organization_id,
                user_id,
                payload,
                created_at,
                expires_at,
                last_activity_at
            ) VALUES (
                $1, $2, $3, $4::jsonb, NOW(), $5::timestamptz, NOW()
            )
            ON CONFLICT (session_id) DO UPDATE SET
                organization_id = EXCLUDED.organization_id,
                user_id = EXCLUDED.user_id,
                payload = EXCLUDED.payload,
                expires_at = EXCLUDED.expires_at,
                last_activity_at = NOW()
            """,
            session_id,
            session.organization_id,
            session.user_id,
            json.dumps(payload),
            expires_at.isoformat(),
        )
        return True
    except Exception as exc:
        logger.warning("Failed storing SSO user session %s: %s", session_id, exc)
        return False


async def get_user_session(session_id: str) -> Optional[SSOSession]:
    """Load a logged-in SSO user session."""
    if not session_id or not await _ensure_schema():
        return None
    try:
        row = await db_fetchrow(
            """
            SELECT payload, expires_at
            FROM app_sso_user_sessions
            WHERE session_id = $1
            """,
            session_id,
        )
        if not row:
            return None
        expires_at = _to_datetime(row["expires_at"])
        if expires_at and expires_at <= _utc_now():
            await delete_user_session(session_id)
            return None
        payload = _payload_dict(row["payload"])
        if not payload:
            return None
        return SSOSession.model_validate(payload)
    except Exception as exc:
        logger.warning("Failed loading SSO user session %s: %s", session_id, exc)
        return None


async def delete_user_session(session_id: str) -> None:
    """Delete a logged-in SSO user session by session id."""
    if not session_id or not await _ensure_schema():
        return
    try:
        await db_execute(
            """
            DELETE FROM app_sso_user_sessions
            WHERE session_id = $1
            """,
            session_id,
        )
    except Exception as exc:
        logger.warning("Failed deleting SSO user session %s: %s", session_id, exc)


async def delete_user_session_for_org(session_id: str, organization_id: str) -> bool:
    """Delete session scoped to a specific organization."""
    if not session_id or not await _ensure_schema():
        return False
    try:
        status = await db_execute(
            """
            DELETE FROM app_sso_user_sessions
            WHERE session_id = $1 AND organization_id = $2
            """,
            session_id,
            organization_id,
        )
        return status is not None and status.endswith("1")
    except Exception as exc:
        logger.warning(
            "Failed deleting SSO user session %s for org %s: %s",
            session_id,
            organization_id,
            exc,
        )
        return False


async def delete_user_sessions_for_org(organization_id: str) -> int:
    """Delete all sessions for an organization and return deleted count."""
    if not await _ensure_schema():
        return 0
    try:
        rows = await db_fetch(
            """
            WITH deleted AS (
                DELETE FROM app_sso_user_sessions
                WHERE organization_id = $1
                RETURNING 1
            )
            SELECT COUNT(*)::int AS deleted_count FROM deleted
            """,
            organization_id,
        )
        if not rows:
            return 0
        return int(rows[0]["deleted_count"] or 0)
    except Exception as exc:
        logger.warning("Failed deleting SSO sessions for org %s: %s", organization_id, exc)
        return 0


async def count_active_user_sessions(organization_id: str) -> Optional[int]:
    """Count active (non-expired) sessions for an org."""
    if not await _ensure_schema():
        return None
    try:
        row = await db_fetchrow(
            """
            SELECT COUNT(*)::int AS session_count
            FROM app_sso_user_sessions
            WHERE organization_id = $1
              AND expires_at > NOW()
            """,
            organization_id,
        )
        if not row:
            return 0
        return int(row["session_count"] or 0)
    except Exception as exc:
        logger.warning(
            "Failed counting active SSO sessions for org %s: %s",
            organization_id,
            exc,
        )
        return None


async def list_active_user_sessions(
    organization_id: str,
    limit: int,
    offset: int,
) -> Optional[Tuple[List[SSOSession], int]]:
    """List active sessions for an org with pagination."""
    if not await _ensure_schema():
        return None

    try:
        rows = await db_fetch(
            """
            SELECT payload
            FROM app_sso_user_sessions
            WHERE organization_id = $1
              AND expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            organization_id,
            limit,
            offset,
        )
        count_row = await db_fetchrow(
            """
            SELECT COUNT(*)::int AS total_count
            FROM app_sso_user_sessions
            WHERE organization_id = $1
              AND expires_at > NOW()
            """,
            organization_id,
        )

        sessions: List[SSOSession] = []
        for row in rows:
            payload = _payload_dict(row["payload"])
            if not payload:
                continue
            try:
                sessions.append(SSOSession.model_validate(payload))
            except Exception:
                continue

        total = int((count_row or {}).get("total_count", 0))
        return sessions, total
    except Exception as exc:
        logger.warning("Failed listing SSO sessions for org %s: %s", organization_id, exc)
        return None

