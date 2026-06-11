-- Migration 006: Stripe webhook event log + subscription payment status
--
-- Closes a fresh-install gap: the Stripe subscription sync service
-- (src/payments/subscription_sync.py) requires both of these to exist, but they
-- were previously only defined in supabase/migrations/019 — which the migration
-- runner (scripts/migrate_db.mjs, db/migrations only) never applies. On a fresh
-- database the webhook handler crashed on the idempotency check and the
-- subscription upsert (missing payment_status column).
--
-- This is the portable, Neon-friendly form: no RLS policies, no Supabase
-- `service_role`/`authenticated` grants (the app authorizes in Python and
-- connects with a single role), and idempotent so it is safe to run against an
-- already-populated database.

-- Idempotency + audit log of processed Stripe webhook events.
CREATE TABLE IF NOT EXISTS stripe_webhook_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id text NOT NULL UNIQUE,
  event_type text NOT NULL,
  user_id text,
  customer_id text,
  subscription_id text,
  processed_at timestamptz NOT NULL DEFAULT NOW(),
  sync_result jsonb,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

-- Fast duplicate lookups by Stripe event id (primary use case).
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_event_id
  ON stripe_webhook_events(event_id);

-- Auditing by user.
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_user_id
  ON stripe_webhook_events(user_id)
  WHERE user_id IS NOT NULL;

-- Event-type filtering / recent-first scans.
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_type_time
  ON stripe_webhook_events(event_type, processed_at DESC);

-- Grace-period / payment-health tracking written by the subscription sync upsert.
ALTER TABLE stripe_subscriptions
  ADD COLUMN IF NOT EXISTS payment_status text DEFAULT 'current'
    CHECK (payment_status IN ('current', 'grace_period', 'payment_failed'));

-- Retention helper for the webhook event log (keeps `retention_days`, default 90).
CREATE OR REPLACE FUNCTION cleanup_old_webhook_events(retention_days integer DEFAULT 90)
RETURNS integer AS $$
DECLARE
  v_deleted integer;
BEGIN
  DELETE FROM stripe_webhook_events
  WHERE processed_at < NOW() - (retention_days || ' days')::interval;

  GET DIAGNOSTICS v_deleted = ROW_COUNT;
  RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;
