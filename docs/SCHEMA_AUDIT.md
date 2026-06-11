# Schema Source-of-Truth Audit (P0.1)

> **Status:** Analysis complete. **Money-path gap closed** — the Stripe webhook
> idempotency log (`stripe_webhook_events`) and the `stripe_subscriptions.payment_status`
> column, previously only in the never-applied `supabase/migrations/019`, are now in the
> runner-applied set (`db/migrations/006_stripe_webhook_events.sql`). A CI **schema-smoke**
> gate (`scripts/schema_smoke.sql`, run by the `schema-smoke` job) now boots a fresh
> Postgres, applies `db/migrations/`, and fails if any code-referenced table/column is
> missing — so a fresh install is verified deterministically and the schema can't silently
> re-fragment. The full multi-source *runner cutover* (folding the supabase-only analytics/
> social/seo/plagiarism domains and the pgvector knowledge-base tables) remains gated on
> validating against a live/staging database — see "Cutover plan" below. Do **not** repoint
> the runner onto the supabase set in production until that validation passes.
>
> **Fresh-install correctness fix:** `src/knowledge/quota.py` queried a non-existent
> `user_subscriptions` table (silently falling back to the `free` tier); it now reads the
> real, populated `stripe_subscriptions` table.

## Problem

Database schema is currently produced by **four** independent mechanisms with
**overlapping `001…` numbering** and no single source of truth:

| Mechanism | Files | Numbering | Applied by |
|-----------|-------|-----------|------------|
| `db/migrations/` | 5 (`001_init` → `005_organizations`) | 001–005 | ✅ `bun run db:migrate` (`scripts/migrate_db.mjs`) — the **only** automated runner |
| `supabase/migrations/` | 19 (`001` → `019`) | 001–019 | ❌ Nothing runs these; yet `docs/DATABASE.md` documents them as canonical |
| `apps/api/migrations/` | 3 (webhooks, knowledge_base) | 001–002 | ❌ Orphaned |
| Runtime `CREATE TABLE IF NOT EXISTS` in Python | ≥5 modules | n/a | App code at import/startup |

Runtime DDL lives in: `src/auth/sso/persistence.py`, `src/research/research_store.py`,
`src/workflows/workflow_store.py`, `src/organizations/db_init.py`.

## Key finding: the sets are **divergent**, not duplicated

The two large sets target **different schemas** for the same domains, and each is
**missing** tables the other defines:

- **SSO naming conflict.** `db/` + the Python runtime use `app_sso_configurations`,
  `app_sso_auth_sessions`, `app_sso_user_sessions`. `supabase/` instead defines
  `sso_configurations`, `sso_sessions`, `sso_attribute_mappings`, `sso_used_assertions`.
  **The application code references the `app_sso_*` names** → the `supabase/` SSO tables
  are legacy/dead.
- **Workflows / research / organizations:** defined in `db/` **and** created again at
  runtime by Python (`app_workflows`, `app_workflow_executions`, `research_queries`,
  `research_sources`, `organizations`, `organization_members`, `audit_logs`). The code
  uses these `db/`-lineage names.
- **~20 domain tables exist ONLY in `supabase/`:** `conversations`, `tool_usage`,
  `users`, `content_versions`, `content_feedback`, `voice_scores`, `tier_limits`,
  `templates` (richer), `plagiarism_checks`, `plagiarism_sources`, `content_performance`,
  `content_recommendations`, `performance_events`, `performance_snapshots`,
  `post_analytics`, `seo_rankings`, `social_accounts`, `social_campaigns`,
  `social_oauth_state`, `scheduled_posts`, `organization_plan_limits`, `role_permissions`,
  `kb_chunks`. The corresponding route modules (`analytics`, `social`, `seo`,
  `fact_check`/plagiarism, `knowledge`, `versions`) ship in `apps/api/app/routes/`.
- **Knowledge base is a third variant:** `apps/api/migrations/` defines
  `kb_documents` + `kb_embeddings`; `supabase/` defines `kb_documents` + `kb_chunks`.

### Consequence

`bun run db:migrate` applies **only** the 5-file `db/` set. A fresh Neon/Postgres
environment provisioned via the documented command is therefore **missing the social,
analytics, SEO, plagiarism, knowledge-base, conversations, and content-version tables**.
Those features only work if `supabase/` migrations were applied out-of-band (e.g. the
Supabase CLI) or if a table happens to be lazily created by runtime DDL. Provisioning is
non-deterministic and depends on deploy lineage and Python import order.

## Target: the schema the **code** needs = the UNION

The consolidated schema must contain:

1. The `db/`-lineage tables (core content, brand voice, payments, quotas, blog_posts).
2. The runtime-DDL tables, **folded into migrations** and removed from app startup:
   `app_sso_*`, `app_workflows`, `app_workflow_executions`, `research_queries`,
   `research_sources`, `organizations`, `organization_members`, `organization_invites`,
   `audit_logs`.
3. The `supabase/`-only domain tables (analytics, social, seo, plagiarism, knowledge,
   conversations, tool_usage, content_versions, content_feedback, tier_limits, etc.) —
   **using the `kb_chunks` knowledge-base variant or the `kb_embeddings` variant,
   whichever the `knowledge` route code actually queries** (confirm during consolidation).
4. **Dropped:** the legacy `sso_*` tables from `supabase/` (superseded by `app_sso_*`).

## Cutover plan (NEEDS-STAGING)

1. **Snapshot the live prod schema** (`pg_dump --schema-only`) — this is ground truth for
   what already exists in production.
2. **Diff** the live schema against each of the four sources to learn which lineage prod
   actually ran.
3. **Build a single ordered `db/migrations/` sequence** = union above, renumbered with no
   collisions, each migration written idempotently (`CREATE TABLE IF NOT EXISTS`,
   guarded `ALTER`) so it is safe to run against an already-populated prod DB.
4. **Convert runtime DDL** in the four Python modules into migrations; replace the
   in-code `CREATE TABLE` with a startup assertion (or a `DEV_MODE`-only bootstrap).
5. **Archive** `supabase/migrations/` and `apps/api/migrations/` under a clearly-labelled
   `legacy/` path (or delete once prod parity is confirmed). Leave one tree.
6. **Add a CI guard** (`schema-smoke`): boot an ephemeral Postgres, run `db:migrate`, then
   assert every table the code `SELECT`s from exists. Permanently prevents re-fragmentation.
7. **Rewrite `docs/DATABASE.md`** to reflect the single inventory; delete the stale
   "Missing Migrations" section.

## Methodology

Table inventories were extracted with `grep "CREATE TABLE"` across all four sources and
cross-referenced against `FROM/INTO/UPDATE/JOIN <table>` references in `apps/api`. Dynamic
SQL (f-strings) means code-reference counts undercount real usage, so domain ownership was
confirmed by matching route modules to the `supabase/`-only tables. Live-DB validation is
still required before any runner change.
