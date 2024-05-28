"""Async asyncpg-backed query adapter that mirrors the subset of the Supabase
query-builder API used by the analytics services.

This lets those services move off supabase-py onto Neon with minimal changes:
each `self._get_supabase()` returns a NeonQueryClient (when DATABASE_URL is set)
and the existing `...execute()` chains are simply awaited. A pg_catalog jsonb
codec is registered per connection so jsonb columns (shares_by_platform,
metadata, data) round-trip as dict/list automatically; ISO-8601 string bounds
(e.g. ``start_date.isoformat()``) are coerced to datetime so comparisons against
timestamptz columns work.

Only the surface the services actually use is implemented: table/select/insert/
update/delete + eq/gte/lte/lt/is_ + order/limit/range, and an awaitable
execute() returning an object with a ``.data`` list.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple

_ISO_DT = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _coerce(value: Any) -> Any:
    """Coerce ISO-8601 date/datetime strings to date/datetime objects.

    asyncpg requires real date/datetime instances for date/timestamptz columns
    and comparisons, whereas the services pass ``.isoformat()`` strings (as the
    Supabase/PostgREST client accepted). Non-ISO strings (ids, titles, keywords)
    and non-string values (dict→jsonb, list→array) pass through untouched.
    """
    if isinstance(value, str):
        if _ISO_DT.match(value):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return value
        if _ISO_DATE.match(value):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return value
    return value


def _normalize_row(row: dict) -> dict:
    """Match the Supabase/PostgREST output shape the services parse against:
    date/datetime values become ISO-8601 strings (jsonb already decodes to
    dict/list via the connection codec). The services call
    ``datetime.fromisoformat(...)`` on timestamp fields, so they expect strings.
    """
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            row[key] = value.isoformat()
        elif isinstance(value, Decimal):
            # NUMERIC columns return Decimal from asyncpg; the services expect
            # plain floats (as Supabase's JSON delivered), and mix them with
            # floats in score calculations.
            row[key] = float(value)
    return row


class _Result:
    __slots__ = ("data",)

    def __init__(self, data: List[dict]):
        self.data = data


class _Query:
    """A single chainable query against one table."""

    def __init__(self, client: "NeonQueryClient", table: str):
        self._client = client
        self._table = table
        self._op = "select"
        self._columns = "*"
        self._payload: Any = None
        self._filters: List[Tuple[str, str, Any]] = []
        self._orders: List[Tuple[str, bool]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._single = False

    # -- builder verbs -------------------------------------------------------
    def select(self, columns: str = "*") -> "_Query":
        self._op = "select"
        self._columns = columns
        return self

    def insert(self, payload: Any) -> "_Query":
        self._op = "insert"
        self._payload = payload
        return self

    def upsert(self, payload: Any, on_conflict: Optional[str] = None) -> "_Query":
        self._op = "upsert"
        self._payload = payload
        self._on_conflict = on_conflict or "id"
        return self

    def update(self, payload: dict) -> "_Query":
        self._op = "update"
        self._payload = payload
        return self

    def delete(self) -> "_Query":
        self._op = "delete"
        return self

    def eq(self, column: str, value: Any) -> "_Query":
        self._filters.append(("=", column, _coerce(value)))
        return self

    def gte(self, column: str, value: Any) -> "_Query":
        self._filters.append((">=", column, _coerce(value)))
        return self

    def lte(self, column: str, value: Any) -> "_Query":
        self._filters.append(("<=", column, _coerce(value)))
        return self

    def lt(self, column: str, value: Any) -> "_Query":
        self._filters.append(("<", column, _coerce(value)))
        return self

    def gt(self, column: str, value: Any) -> "_Query":
        self._filters.append((">", column, _coerce(value)))
        return self

    def is_(self, column: str, value: Any) -> "_Query":
        self._filters.append(("IS", column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "_Query":
        self._orders.append((column, desc))
        return self

    def limit(self, count: int) -> "_Query":
        self._limit = count
        return self

    def range(self, start: int, end: int) -> "_Query":
        self._offset = start
        self._limit = end - start + 1
        return self

    def single(self) -> "_Query":
        self._single = True
        return self

    # -- SQL building --------------------------------------------------------
    def _where(self, params: List[Any]) -> str:
        if not self._filters:
            return ""
        clauses = []
        for op, col, val in self._filters:
            if op == "IS":
                if val is None or (isinstance(val, str) and val.lower() == "null"):
                    clauses.append(f'"{col}" IS NULL')
                else:
                    params.append(val)
                    clauses.append(f'"{col}" IS ${len(params)}')
            else:
                params.append(val)
                clauses.append(f'"{col}" {op} ${len(params)}')
        return " WHERE " + " AND ".join(clauses)

    def _build(self) -> Tuple[str, List[Any]]:
        params: List[Any] = []
        if self._op in ("insert", "upsert"):
            rows = self._payload if isinstance(self._payload, list) else [self._payload]
            cols = list(rows[0].keys())
            col_sql = ", ".join(f'"{c}"' for c in cols)
            value_groups = []
            for row in rows:
                placeholders = []
                for c in cols:
                    params.append(_coerce(row.get(c)))
                    placeholders.append(f"${len(params)}")
                value_groups.append("(" + ", ".join(placeholders) + ")")
            sql = f'INSERT INTO "{self._table}" ({col_sql}) VALUES ' + ", ".join(
                value_groups
            )
            if self._op == "upsert":
                updates = ", ".join(
                    f'"{c}" = EXCLUDED."{c}"' for c in cols if c != self._on_conflict
                )
                sql += f' ON CONFLICT ("{self._on_conflict}") DO UPDATE SET {updates}'
            sql += " RETURNING *"
            return sql, params

        if self._op == "update":
            set_parts = []
            for col, val in self._payload.items():
                params.append(_coerce(val))
                set_parts.append(f'"{col}" = ${len(params)}')
            sql = f'UPDATE "{self._table}" SET ' + ", ".join(set_parts)
            sql += self._where(params) + " RETURNING *"
            return sql, params

        if self._op == "delete":
            sql = f'DELETE FROM "{self._table}"' + self._where(params)
            return sql, params

        # select
        sql = f'SELECT {self._columns} FROM "{self._table}"' + self._where(params)
        if self._orders:
            order_sql = ", ".join(
                f'"{c}" DESC' if desc else f'"{c}" ASC' for c, desc in self._orders
            )
            sql += " ORDER BY " + order_sql
        if self._limit is not None:
            params.append(self._limit)
            sql += f" LIMIT ${len(params)}"
        if self._offset:
            params.append(self._offset)
            sql += f" OFFSET ${len(params)}"
        return sql, params

    async def execute(self) -> _Result:
        sql, params = self._build()
        rows = await self._client._fetch(sql, params)
        data = [_normalize_row(dict(r)) for r in rows]
        if self._single:
            return _Result(data[0] if data else None)
        return _Result(data)


class NeonQueryClient:
    """Supabase-client-shaped facade over the shared asyncpg pool."""

    async def _fetch(self, sql: str, params: List[Any]):
        from ..db import get_pool

        pool = await get_pool()
        if pool is None:
            raise RuntimeError(
                "NeonQueryClient requires a database pool (DATABASE_URL)."
            )
        async with pool.acquire() as conn:
            await conn.set_type_codec(
                "jsonb",
                encoder=json.dumps,
                decoder=json.loads,
                schema="pg_catalog",
            )
            return await conn.fetch(sql, *params)

    def table(self, name: str) -> _Query:
        return _Query(self, name)
