# DB Migration Rollback Scripts (Neon/Postgres)

## Overview

This directory contains rollback (DOWN) scripts for the `db/migrations/`
migration files that target the Neon/Postgres database used by the Next.js
and Python backends.

## WARNING -- DATA LOSS

Running a rollback script **permanently deletes** the data stored in the
affected tables. Always create a full database backup before executing any
rollback:

```bash
pg_dump -Fc "$DATABASE_URL" -f backup_$(date +%Y%m%d_%H%M%S).dump
```

## Execution Order

Rollback scripts **must be run in reverse numerical order** (highest number
first):

```bash
psql "$DATABASE_URL" -f rollback/005_drop_organizations.sql
psql "$DATABASE_URL" -f rollback/004_drop_deep_research.sql
psql "$DATABASE_URL" -f rollback/003_drop_workflows_sso_runtime.sql
psql "$DATABASE_URL" -f rollback/002_drop_brand_voice.sql
psql "$DATABASE_URL" -f rollback/001_drop_init.sql
```

## Script Inventory

| Rollback Script | Rolls Back | Objects Dropped |
|---|---|---|
| `005_drop_organizations.sql` | `005_organizations.sql` | `organizations`, `organization_members`, `organization_invites`, `audit_logs` tables |
| `004_drop_deep_research.sql` | `004_deep_research.sql` | `research_queries`, `research_sources` tables |
| `003_drop_workflows_sso_runtime.sql` | `003_workflows_sso_runtime.sql` | `app_workflows`, `app_workflow_executions`, `app_sso_configurations`, `app_sso_auth_sessions`, `app_sso_user_sessions` tables |
| `002_drop_brand_voice.sql` | `002_brand_voice.sql` | `voice_samples`, `voice_fingerprints` tables + composite index on `brand_profiles` |
| `001_drop_init.sql` | `001_init.sql` | `blog_posts`, `templates`, `brand_profiles`, `generated_content`, `user_quotas`, `usage_records`, `stripe_customers`, `stripe_subscriptions`, `payments`, `payment_failures` tables |

## Notes

- All scripts use `IF EXISTS` and `CASCADE` for safety.
- Each script is wrapped in a `BEGIN`/`COMMIT` transaction.
- The `pgcrypto` extension is not dropped because other schemas may depend on it.
