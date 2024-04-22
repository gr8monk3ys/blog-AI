# Supabase Migration Rollback Scripts

## Overview

This directory contains rollback (DOWN) scripts for every Supabase migration.
Each script reverses the changes made by the corresponding UP migration by
dropping tables, functions, triggers, RLS policies, views, and columns.

## WARNING -- DATA LOSS

Running a rollback script **permanently deletes** the data stored in the
affected tables. Always create a full database backup before executing any
rollback:

```bash
pg_dump -Fc "$DATABASE_URL" -f backup_$(date +%Y%m%d_%H%M%S).dump
```

## Execution Order

Rollback scripts **must be run in reverse numerical order** (highest number
first). Dependencies between migrations mean that running them out of order
will fail.

To roll back to a specific migration, run every rollback script with a number
**greater than** the target migration. For example, to roll back to migration
010, run:

```bash
psql "$DATABASE_URL" -f rollback/019_drop_webhook_event_log.sql
psql "$DATABASE_URL" -f rollback/018_drop_content_feedback.sql
psql "$DATABASE_URL" -f rollback/017_drop_sso.sql
psql "$DATABASE_URL" -f rollback/016_drop_social_scheduling.sql
psql "$DATABASE_URL" -f rollback/015_drop_performance_analytics.sql
psql "$DATABASE_URL" -f rollback/014_drop_plagiarism_checks.sql
psql "$DATABASE_URL" -f rollback/013_drop_templates.sql
psql "$DATABASE_URL" -f rollback/012_drop_blog_posts.sql
psql "$DATABASE_URL" -f rollback/011_drop_organizations.sql
```

To roll back **all** Supabase migrations:

```bash
for n in 019 018 017 016 015 014 013 012 011 010 009 008 007 006 005 004 003 002 001; do
  psql "$DATABASE_URL" -f "rollback/${n}_*.sql"
done
```

## Script Inventory

| Rollback Script | Rolls Back | Objects Dropped |
|---|---|---|
| `019_drop_webhook_event_log.sql` | `019_webhook_event_log.sql` | `stripe_webhook_events` table, `payment_status` column on `stripe_subscriptions` |
| `018_drop_content_feedback.sql` | `018_content_feedback.sql` | `content_feedback` table, `get_content_feedback_stats` function |
| `017_drop_sso.sql` | `017_sso.sql` | `sso_configurations`, `sso_sessions`, `sso_attribute_mappings`, `sso_used_assertions` tables + 9 functions |
| `016_drop_social_scheduling.sql` | `016_social_scheduling.sql` | `social_accounts`, `scheduled_posts`, `social_campaigns`, `post_analytics`, `social_oauth_state` tables + 6 functions |
| `015_drop_performance_analytics.sql` | `015_performance_analytics.sql` | `content_performance`, `performance_events`, `performance_snapshots`, `seo_rankings`, `content_recommendations` tables + 2 views + 6 functions |
| `014_drop_plagiarism_checks.sql` | `014_plagiarism_checks.sql` | `plagiarism_checks`, `plagiarism_sources` tables + 5 functions |
| `013_drop_templates.sql` | `013_create_templates.sql` | `templates` table + `increment_template_use_count` function |
| `012_drop_blog_posts.sql` | `012_blog_posts.sql` | `blog_posts` table |
| `011_drop_organizations.sql` | `011_organizations.sql` | `organizations`, `organization_members`, `organization_invites`, `audit_logs`, `role_permissions`, `organization_plan_limits` tables + 8 functions + `organization_id` columns on other tables |
| `010_drop_knowledge_base.sql` | `010_knowledge_base.sql` | `kb_documents`, `kb_chunks` tables + `kb_usage_by_user` view + 5 functions |
| `009_drop_content_versions.sql` | `009_content_versions.sql` | `content_versions` table + `current_version`/`version_count` columns + 10 functions |
| `008_drop_stripe_integration.sql` | `008_stripe_integration.sql` | `stripe_customers`, `stripe_subscriptions`, `payments`, `payment_failures`, `users` tables + 2 functions |
| `007_drop_usage_quotas.sql` | `007_usage_quotas.sql` | `user_quotas`, `usage_records`, `tier_limits` tables + 6 functions |
| `006_drop_brand_voice_training.sql` | `006_enhance_brand_voice_training.sql` | `voice_samples`, `voice_fingerprints`, `voice_scores` tables + 4 columns on `brand_profiles` |
| `005_drop_brand_profiles.sql` | `005_create_brand_profiles.sql` | `brand_profiles` table + `set_default_brand_profile` function |
| `004_drop_favorites.sql` | `004_add_favorites.sql` | `is_favorite`, `tool_name`, `title` columns + `toggle_favorite`/`set_favorite` functions |
| `003_drop_conversations.sql` | `003_create_conversations.sql` | `conversations` table + `upsert_conversation`/`add_conversation_message` functions |
| `002_drop_tool_usage.sql` | `002_create_tool_usage.sql` | `tool_usage` table + `increment_tool_usage`/`get_tool_stats` functions |
| `001_drop_generated_content.sql` | `001_create_generated_content.sql` | `generated_content` table (shared `update_updated_at_column` function preserved) |

## Notes

- All scripts use `IF EXISTS` and `CASCADE` for safety.
- Each script is wrapped in a `BEGIN`/`COMMIT` transaction so it either
  succeeds completely or rolls back on error.
- The shared `update_updated_at_column()` function is intentionally **not**
  dropped by individual rollback scripts because many tables depend on it.
  Drop it manually only after rolling back all migrations.
- Extensions (`pgcrypto`) are not dropped because other schemas may depend on
  them.
