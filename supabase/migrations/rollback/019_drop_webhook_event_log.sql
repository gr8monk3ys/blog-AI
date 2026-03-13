-- Rollback: 019_webhook_event_log.sql
-- Description: Drops the stripe_webhook_events table and removes the
--              payment_status column added to stripe_subscriptions.
--
-- WARNING: This will permanently delete webhook event audit data. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role can manage webhook events" ON stripe_webhook_events;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS cleanup_old_webhook_events(INTEGER) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS stripe_webhook_events CASCADE;

-- =========================================================================
-- Remove payment_status column from stripe_subscriptions
-- =========================================================================
ALTER TABLE stripe_subscriptions
    DROP COLUMN IF EXISTS payment_status;

COMMIT;
