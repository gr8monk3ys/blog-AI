-- Migration: Create webhook tables
-- Description: Creates tables for webhook subscriptions and delivery logs
-- Version: 001
-- Created: 2024-01-15
--
-- This migration creates the following tables:
-- - webhook_subscriptions: Stores webhook endpoint registrations
-- - webhook_deliveries: Logs all webhook delivery attempts
--
-- These tables support the Zapier-compatible webhook system with:
-- - Multi-tenant isolation (user_id foreign key)
-- - Event type filtering
-- - Delivery statistics tracking
-- - Retry logging

-- =============================================================================
-- Table: webhook_subscriptions
-- =============================================================================
-- Stores registered webhook endpoints that receive event notifications.
-- Each subscription belongs to a user and listens for specific event types.

CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Owner (foreign key to users table if it exists)
    user_id VARCHAR(255) NOT NULL,

    -- Subscription configuration
    target_url TEXT NOT NULL,
    event_types TEXT[] NOT NULL DEFAULT '{}',  -- Array of event type strings
    secret VARCHAR(256),  -- HMAC signing secret (optional)
    is_active BOOLEAN NOT NULL DEFAULT true,
    description VARCHAR(500),
    metadata JSONB DEFAULT '{}',

    -- Delivery statistics
    total_deliveries INTEGER NOT NULL DEFAULT 0,
    successful_deliveries INTEGER NOT NULL DEFAULT 0,
    failed_deliveries INTEGER NOT NULL DEFAULT 0,
    last_delivery_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    last_error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_target_url CHECK (
        target_url ~ '^https?://'
    ),
    CONSTRAINT valid_event_types CHECK (
        array_length(event_types, 1) > 0
    )
);

-- Indexes for webhook_subscriptions
CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_user_id
    ON webhook_subscriptions(user_id);

CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_event_types
    ON webhook_subscriptions USING GIN(event_types);

CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_is_active
    ON webhook_subscriptions(is_active)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_webhook_subscriptions_created_at
    ON webhook_subscriptions(created_at DESC);

-- Unique constraint: prevent duplicate subscriptions to same URL for same events
-- This is a partial index to allow different event types for same URL
CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_subscriptions_unique_url_user
    ON webhook_subscriptions(user_id, target_url, event_types)
    WHERE is_active = true;

-- =============================================================================
-- Table: webhook_deliveries
-- =============================================================================
-- Logs all webhook delivery attempts for auditing and debugging.
-- Includes request/response details and retry information.

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    subscription_id UUID NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255) NOT NULL,  -- Unique event ID for deduplication

    -- Delivery status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, delivered, failed, retrying
    target_url TEXT NOT NULL,

    -- Request details
    request_headers JSONB DEFAULT '{}',
    request_payload JSONB DEFAULT '{}',

    -- Response details
    response_status_code INTEGER,
    response_headers JSONB DEFAULT '{}',
    response_body TEXT,  -- Truncated to 10KB max

    -- Timing
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,

    -- Retry information
    attempt_number INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMPTZ,
    error_message TEXT,

    -- Constraints
    CONSTRAINT valid_status CHECK (
        status IN ('pending', 'delivered', 'failed', 'retrying')
    ),
    CONSTRAINT valid_attempt_number CHECK (
        attempt_number >= 1 AND attempt_number <= max_attempts
    )
);

-- Indexes for webhook_deliveries
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_subscription_id
    ON webhook_deliveries(subscription_id);

CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_event_id
    ON webhook_deliveries(event_id);

CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status
    ON webhook_deliveries(status);

CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_created_at
    ON webhook_deliveries(created_at DESC);

-- Index for finding deliveries that need retry
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_pending_retry
    ON webhook_deliveries(next_retry_at)
    WHERE status = 'retrying' AND next_retry_at IS NOT NULL;

-- Partial index for failed deliveries (for monitoring)
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_failed
    ON webhook_deliveries(created_at DESC)
    WHERE status = 'failed';

-- =============================================================================
-- Table: webhook_recent_events
-- =============================================================================
-- Stores recent events for Zapier polling triggers.
-- Events are automatically cleaned up after 7 days.

CREATE TABLE IF NOT EXISTS webhook_recent_events (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Owner
    user_id VARCHAR(255) NOT NULL,

    -- Event data
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- For deduplication in polling triggers
    event_id VARCHAR(255) NOT NULL
);

-- Indexes for webhook_recent_events
CREATE INDEX IF NOT EXISTS idx_webhook_recent_events_user_id
    ON webhook_recent_events(user_id);

CREATE INDEX IF NOT EXISTS idx_webhook_recent_events_created_at
    ON webhook_recent_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_webhook_recent_events_event_type
    ON webhook_recent_events(event_type);

-- Unique constraint for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_recent_events_unique
    ON webhook_recent_events(user_id, event_id);

-- =============================================================================
-- Functions and Triggers
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_webhook_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_webhook_subscription_updated_at ON webhook_subscriptions;
CREATE TRIGGER trigger_webhook_subscription_updated_at
    BEFORE UPDATE ON webhook_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_subscription_updated_at();

-- Function to update subscription stats after delivery
CREATE OR REPLACE FUNCTION update_webhook_subscription_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update on status change to delivered or failed
    IF NEW.status IN ('delivered', 'failed') AND
       (OLD.status IS NULL OR OLD.status != NEW.status) THEN

        UPDATE webhook_subscriptions
        SET
            total_deliveries = total_deliveries + 1,
            successful_deliveries = CASE WHEN NEW.status = 'delivered'
                THEN successful_deliveries + 1 ELSE successful_deliveries END,
            failed_deliveries = CASE WHEN NEW.status = 'failed'
                THEN failed_deliveries + 1 ELSE failed_deliveries END,
            last_delivery_at = NOW(),
            last_success_at = CASE WHEN NEW.status = 'delivered'
                THEN NOW() ELSE last_success_at END,
            last_failure_at = CASE WHEN NEW.status = 'failed'
                THEN NOW() ELSE last_failure_at END,
            last_error = CASE WHEN NEW.status = 'failed'
                THEN NEW.error_message ELSE last_error END
        WHERE id = NEW.subscription_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update subscription stats
DROP TRIGGER IF EXISTS trigger_update_subscription_stats ON webhook_deliveries;
CREATE TRIGGER trigger_update_subscription_stats
    AFTER INSERT OR UPDATE ON webhook_deliveries
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_subscription_stats();

-- =============================================================================
-- Cleanup Functions
-- =============================================================================

-- Function to clean up old delivery logs (retain 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_webhook_deliveries()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_deliveries
    WHERE created_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old recent events (retain 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_webhook_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_recent_events
    WHERE created_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Row Level Security (RLS) Policies
-- =============================================================================
-- Enable RLS for multi-tenant security if using Supabase

-- Enable RLS on tables
ALTER TABLE webhook_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_recent_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own subscriptions
CREATE POLICY webhook_subscriptions_user_policy ON webhook_subscriptions
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true))
    WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Policy: Users can only see deliveries for their subscriptions
CREATE POLICY webhook_deliveries_user_policy ON webhook_deliveries
    FOR ALL
    USING (
        subscription_id IN (
            SELECT id FROM webhook_subscriptions
            WHERE user_id = current_setting('app.current_user_id', true)
        )
    );

-- Policy: Users can only see their own recent events
CREATE POLICY webhook_recent_events_user_policy ON webhook_recent_events
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true))
    WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE webhook_subscriptions IS 'Stores webhook endpoint registrations for event notifications';
COMMENT ON TABLE webhook_deliveries IS 'Logs all webhook delivery attempts for auditing and debugging';
COMMENT ON TABLE webhook_recent_events IS 'Stores recent events for Zapier polling triggers';

COMMENT ON COLUMN webhook_subscriptions.event_types IS 'Array of event types: content.generated, content.published, batch.completed, quota.warning, etc.';
COMMENT ON COLUMN webhook_subscriptions.secret IS 'HMAC-SHA256 signing secret for payload verification';
COMMENT ON COLUMN webhook_deliveries.event_id IS 'Unique event ID used for deduplication by receivers';
COMMENT ON COLUMN webhook_deliveries.attempt_number IS 'Current retry attempt (1-indexed), max 5 by default';
