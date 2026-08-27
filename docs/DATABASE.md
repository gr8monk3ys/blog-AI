# Database

Postgres on Neon, reached two ways:

- `apps/web/lib/db.ts` — `@neondatabase/serverless` from Next.js route handlers.
- `apps/api/src/**` — `asyncpg` from FastAPI services. A few services still carry an
  optional `supabase-py` fallback (used only if `SUPABASE_URL` is set and `DATABASE_URL`
  is not; `supabase` is not in `requirements.txt`). It is legacy and unprovisioned.

## Migrations

There are two runner-applied sets. Both are plain SQL applied in filename order and
recorded in a tracking table so re-runs are no-ops.

| Directory | Applied by | Tracking table |
| --- | --- | --- |
| `db/migrations/` | `bun run db:migrate` (`scripts/migrate_db.mjs`); CI `schema-smoke` and `backend-db-tests` jobs | `schema_migrations` |
| `apps/api/migrations/` | `cd apps/api && python server.py --migrate` | `_migrations` |

`db/migrations/` is the schema: core tables, brand voice, workflows/SSO, research,
organizations, Stripe webhook events, content versions, knowledge base, analytics.
`apps/api/migrations/` adds the webhook delivery tables and knowledge-base columns
the API creates on its own. `rollback/` subdirectories hold the matching down scripts
and are skipped by both runners.

A former `supabase/migrations/` tree (20 files) was removed in 2026-08: nothing applied
it, and its table names no longer matched what the code queries.

`scripts/schema_smoke.sql` asserts every table and column the backend references exists
after a fresh install; CI runs it against `postgres:16` on every PR.
