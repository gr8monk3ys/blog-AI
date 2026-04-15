# Schema Source-of-Truth Audit (P0.1)

> **Status:** Analysis complete. **Money-path gap closed** — the Stripe webhook
> idempotency log (`stripe_webhook_events`) and the `stripe_subscriptions.payment_status`
> column, previously only in the never-applied `supabase/migrations/019`, are now in the
> runner-applied set (`db/migrations/006_stripe_webhook_events.sql`). A CI **schema-smoke**
> gate (`scripts/schema_smoke.sql`, run by the `schema-smoke` job) now boots a fresh
> Postgres, applies `db/migrations/`, and fails if any code-referenced table/column is
> missing — so a fresh install is verified deterministically and the schema can't silently
> re-fragment.
>
> **Correction (supersedes the "UNION" target below):** the remaining `supabase/`-only
> domain tables are **not** Neon-runner gaps and must **not** be folded into `db/migrations/`.
> Code investigation (see "The supabase-only domains are a second datastore") showed the
> modules that use those tables — analytics, SEO, recommendations, dashboards, content
> versioning, knowledge base — talk to a **separate Supabase project** via the `supabase-py`
> client (`create_client(SUPABASE_URL, SUPABASE_KEY)`), with an **in-memory / disabled
> fallback** when Supabase is unconfigured. They never touch the Neon `DATABASE_URL`. All
> three are **off by default** (`ENABLE_PERFORMANCE_ANALYTICS`, `ENABLE_CONTENT_VERSIONING`,
> `ENABLE_KNOWLEDGE_BASE` = false) and `server.py` already labels them "Supabase-dependent
> modules … disabled by default for a Neon-only SaaS until they're migrated." So the Neon
> runner is already **complete** for everything the asyncpg code needs (the `schema-smoke`
> gate proves it); the real resolution for those features is **porting the modules from
> `supabase-py` to asyncpg/Neon** — a tracked product decision, not a migration cutover.
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

### Consequence (for the Neon/asyncpg code path)

`bun run db:migrate` applies **only** the `db/` set. The tables the **Neon/asyncpg** code
path needs are now all in that set (core content, brand voice, payments/quotas, blog_posts,
organizations/workflows/research/SSO runtime tables, and — since
`006_stripe_webhook_events.sql` — the Stripe webhook log + `payment_status`). The
`schema-smoke` CI gate asserts this on every run, so a fresh Neon install is complete and
deterministic for the always-on product.

The `supabase/`-only domain tables (social, analytics, SEO, plagiarism, knowledge base,
conversations, content versions, …) are a **different story** — see below.

## The supabase-only domains are a second datastore (not a Neon-runner gap)

The original "Target = UNION" plan (folding the `supabase/`-only tables into `db/migrations/`)
was based on a wrong assumption: that those tables belong in Neon. They do not. The modules
that use them query a **separate Supabase project** through the `supabase-py` client, never
the Neon pool:

| Module (route, default flag) | DB access | Tables (defined in) |
|------------------------------|-----------|---------------------|
| `src/analytics/*` (performance, SEO, dashboard, recommendations) — `ENABLE_PERFORMANCE_ANALYTICS=false` | `create_client(SUPABASE_URL, SUPABASE_KEY)`; returns `None`/no-op when unset | `content_performance`, `performance_events`, `performance_snapshots`, `seo_rankings`, `content_recommendations` (`supabase/015`) |
| `src/content/version_service.py` — `ENABLE_CONTENT_VERSIONING=false` | Supabase client + `client.rpc(...)`; **in-memory** fallback when unset | `content_versions` (`supabase/009`) |
| `src/knowledge/*` — `ENABLE_KNOWLEDGE_BASE=false` | Supabase client + a pluggable `VectorStore` | `kb_documents` (`supabase/010`) |

Evidence: those service files have **0** `get_pool`/`asyncpg` references and 19–39
`client.table`/`client.rpc` references each; `server.py` labels the block "Supabase-dependent
modules … disabled by default for a Neon-only SaaS until they're migrated."

Everything else in the old `supabase/`-only list (`conversations`, `tool_usage`, `users`,
`content_feedback`, `voice_scores`, `tier_limits`, `plagiarism_*`, `post_analytics`,
`social_*`, `scheduled_posts`, `organization_plan_limits`, `role_permissions`, `kb_chunks`,
`kb_embeddings`) is **not queried by any code** — dead schema.

### Resolution (a product decision, not a migration cutover)

For each Supabase-dependent feature, pick one — there is nothing to "cut over" in the runner:

1. **Keep on Supabase** (status quo): the feature requires a Supabase project with
   `supabase/migrations` applied via the Supabase CLI and `SUPABASE_URL`/`SUPABASE_KEY` set;
   otherwise it runs in-memory or stays disabled. Document the requirement.
2. **Port to Neon/asyncpg**: rewrite the module to use the asyncpg pool (and convert its
   `client.rpc(...)` Postgres functions to SQL), then add the tables to `db/migrations/` and
   `scripts/schema_smoke.sql`. This is the path to a true single datastore, but it's a
   module rewrite per feature, not a schema edit.
3. **Remove**: if a feature isn't on the roadmap, delete the module + its `supabase/` tables.

Until one of the above is chosen per feature, **do not** add these tables to `db/migrations/` —
doing so creates dead Neon tables while the code still reads Supabase.

### Still valid regardless of the above
- **Dropped:** the legacy `sso_*` tables from `supabase/` (superseded by `app_sso_*`).
- **Runtime DDL** (`app_sso_*`, `app_workflows`, `research_*`, `organizations*`, `audit_logs`)
  is created both by `db/migrations/` and lazily by Python at startup; folding the startup
  DDL fully into migrations (and replacing it with a startup assertion) is still worthwhile
  hygiene, independent of the Supabase question.

## Methodology

Table inventories were extracted with `grep "CREATE TABLE"` across all four sources and
cross-referenced against `FROM/INTO/UPDATE/JOIN <table>` references in `apps/api`. Dynamic
SQL (f-strings) means code-reference counts undercount real usage, so domain ownership was
confirmed by matching route modules to the `supabase/`-only tables. Live-DB validation is
still required before any runner change.
