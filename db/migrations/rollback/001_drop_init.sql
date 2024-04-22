-- Rollback: 001_init.sql
-- Description: Drops ALL tables and objects created by the initial Neon/Postgres
--              schema: blog_posts, templates, brand_profiles, generated_content,
--              user_quotas, usage_records, stripe_customers, stripe_subscriptions,
--              payments, payment_failures.
--
-- WARNING: This will permanently delete ALL application data. Back up first.
-- NOTE: This does NOT drop the pgcrypto extension as other schemas may depend on it.

BEGIN;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS payment_failures CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS stripe_subscriptions CASCADE;
DROP TABLE IF EXISTS stripe_customers CASCADE;
DROP TABLE IF EXISTS usage_records CASCADE;
DROP TABLE IF EXISTS user_quotas CASCADE;
DROP TABLE IF EXISTS generated_content CASCADE;
DROP TABLE IF EXISTS brand_profiles CASCADE;
DROP TABLE IF EXISTS templates CASCADE;
DROP TABLE IF EXISTS blog_posts CASCADE;

COMMIT;
