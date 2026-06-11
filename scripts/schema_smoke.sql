-- Schema smoke guard (pure SQL, no driver dependency).
--
-- Asserts that the migration runner (scripts/migrate_db.mjs, which applies only
-- db/migrations/) produces every table the backend code actually queries. This
-- makes "fresh install is missing tables" a CI-enforced failure and keeps the
-- schema from silently re-fragmenting. See docs/SCHEMA_AUDIT.md.
--
-- Usage (after applying db/migrations against the target database):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/schema_smoke.sql
--
-- Intentionally NOT required here:
--   * kb_documents / kb_embeddings / kb_usage_stats — gated behind
--     ENABLE_KNOWLEDGE_BASE and need the pgvector extension, so they live in
--     apps/api/migrations/002_knowledge_base.sql, outside the default runner.
--   * webhook_* (outbound webhooks) — the webhook store is Redis/memory backed;
--     no code references those tables.

DO $$
DECLARE
  required_tables text[] := ARRAY[
    'app_sso_auth_sessions',
    'app_sso_configurations',
    'app_sso_user_sessions',
    'app_workflow_executions',
    'app_workflows',
    'audit_logs',
    'blog_posts',
    'brand_profiles',
    'generated_content',
    'organization_invites',
    'organization_members',
    'organizations',
    'payment_failures',
    'payments',
    'research_queries',
    'research_sources',
    'stripe_customers',
    'stripe_subscriptions',
    'stripe_webhook_events',
    'templates',
    'usage_records',
    'user_quotas',
    'voice_fingerprints',
    'voice_samples'
  ];
  t text;
  missing text[] := ARRAY[]::text[];
BEGIN
  -- Required tables.
  FOREACH t IN ARRAY required_tables LOOP
    IF to_regclass('public.' || t) IS NULL THEN
      missing := array_append(missing, 'table ' || t);
    END IF;
  END LOOP;

  -- Columns added by later migrations whose absence has broken the money path.
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'stripe_subscriptions'
      AND column_name = 'payment_status'
  ) THEN
    missing := array_append(missing, 'column stripe_subscriptions.payment_status');
  END IF;

  IF array_length(missing, 1) > 0 THEN
    RAISE EXCEPTION E'Schema smoke FAILED — fresh-install migration is incomplete.\nMissing: %\nAdd the missing definitions to db/migrations/ (the only directory the runner applies). See docs/SCHEMA_AUDIT.md.',
      array_to_string(missing, ', ');
  END IF;

  RAISE NOTICE 'Schema smoke OK — all % required tables present.', array_length(required_tables, 1);
END $$;
