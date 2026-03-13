-- Rollback: 001_create_webhook_tables.sql
-- Description: Drops webhook subscription, delivery, and recent event tables
--              along with their triggers, functions, RLS policies, and indexes.
--
-- WARNING: This will permanently delete all webhook data. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS webhook_subscriptions_user_policy ON webhook_subscriptions;
DROP POLICY IF EXISTS webhook_deliveries_user_policy ON webhook_deliveries;
DROP POLICY IF EXISTS webhook_recent_events_user_policy ON webhook_recent_events;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS trigger_webhook_subscription_updated_at ON webhook_subscriptions;
DROP TRIGGER IF EXISTS trigger_update_subscription_stats ON webhook_deliveries;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS update_webhook_subscription_updated_at() CASCADE;
DROP FUNCTION IF EXISTS update_webhook_subscription_stats() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_webhook_deliveries() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_webhook_events() CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS webhook_recent_events CASCADE;
DROP TABLE IF EXISTS webhook_deliveries CASCADE;
DROP TABLE IF EXISTS webhook_subscriptions CASCADE;

COMMIT;
