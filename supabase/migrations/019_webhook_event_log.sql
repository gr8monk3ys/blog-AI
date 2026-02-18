-- Migration: Create webhook event log for Stripe idempotency
-- Description: Tracks processed Stripe webhook events to prevent duplicate processing
--   and provides an audit trail for payment-related events.
--
-- Tables:
--   stripe_webhook_events: Log of all processed Stripe webhook events
--
-- Also adds a payment_status column to stripe_subscriptions for grace period tracking.

-- =============================================================================
-- Stripe Webhook Events Table (idempotency + audit log)
-- =============================================================================

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    user_id TEXT,
    customer_id TEXT,
    subscription_id TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sync_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast duplicate lookups (primary use case)
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_event_id
    ON stripe_webhook_events(event_id);

-- Index for auditing by user
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_user_id
    ON stripe_webhook_events(user_id)
    WHERE user_id IS NOT NULL;

-- Index for event type filtering
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_type_time
    ON stripe_webhook_events(event_type, processed_at DESC);

-- Comments
COMMENT ON TABLE stripe_webhook_events IS 'Audit log of processed Stripe webhook events for idempotency and debugging';
COMMENT ON COLUMN stripe_webhook_events.event_id IS 'Stripe event ID (evt_xxx) - unique constraint prevents duplicate processing';
COMMENT ON COLUMN stripe_webhook_events.sync_result IS 'JSON result from the subscription sync service';


-- =============================================================================
-- Add payment_status to stripe_subscriptions for grace period tracking
-- =============================================================================

ALTER TABLE stripe_subscriptions
    ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'current'
        CHECK (payment_status IN ('current', 'grace_period', 'payment_failed'));

COMMENT ON COLUMN stripe_subscriptions.payment_status IS 'Payment health: current, grace_period, or payment_failed';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

ALTER TABLE stripe_webhook_events ENABLE ROW LEVEL SECURITY;

-- Only service role can read/write webhook events (no user access needed)
CREATE POLICY "Service role can manage webhook events"
    ON stripe_webhook_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Cleanup function for old webhook events (keep 90 days)
-- =============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_webhook_events(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM stripe_webhook_events
    WHERE processed_at < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_old_webhook_events IS 'Removes webhook event records older than retention_days (default 90)';
GRANT EXECUTE ON FUNCTION cleanup_old_webhook_events(INTEGER) TO service_role;
