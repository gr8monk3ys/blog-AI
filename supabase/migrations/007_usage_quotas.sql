-- Migration: Create usage quota tables and functions
-- Description: Implements subscription-based usage tracking and quota enforcement
--
-- Tables:
--   user_quotas: Tracks user subscription tier and billing period
--   usage_records: Records individual usage events
--
-- Functions:
--   get_current_month_usage: Calculate usage for current billing period
--   check_quota_available: Check if user has remaining quota
--   increment_user_usage: Record a usage event atomically
--
-- This migration supports the following subscription tiers:
--   - free: 5 generations/month
--   - starter: 50 generations/month
--   - pro: 200 generations/month
--   - business: 1000 generations/month

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- User Quotas Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'pro', 'business')),
    period_start TIMESTAMPTZ NOT NULL DEFAULT date_trunc('month', NOW()),
    period_end TIMESTAMPTZ NOT NULL DEFAULT date_trunc('month', NOW()) + INTERVAL '1 month',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_user_quotas_user_id ON user_quotas(user_id);

-- Index for finding expired periods (for batch reset jobs)
CREATE INDEX IF NOT EXISTS idx_user_quotas_period_end ON user_quotas(period_end);

-- Comments
COMMENT ON TABLE user_quotas IS 'Stores user subscription tier and billing period information';
COMMENT ON COLUMN user_quotas.tier IS 'Subscription tier: free, starter, pro, or business';
COMMENT ON COLUMN user_quotas.period_start IS 'Start of current billing period';
COMMENT ON COLUMN user_quotas.period_end IS 'End of current billing period (when quota resets)';


-- =============================================================================
-- Usage Records Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('blog', 'book', 'batch', 'remix', 'tool', 'other')),
    tokens_used INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for user + time range queries (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_usage_records_user_time ON usage_records(user_id, timestamp DESC);

-- Index for operation type analytics
CREATE INDEX IF NOT EXISTS idx_usage_records_operation ON usage_records(operation_type, timestamp DESC);

-- Partial index for recent records (optimizes current period queries)
CREATE INDEX IF NOT EXISTS idx_usage_records_recent ON usage_records(user_id, timestamp)
    WHERE timestamp > NOW() - INTERVAL '2 months';

-- Comments
COMMENT ON TABLE usage_records IS 'Records individual content generation usage events';
COMMENT ON COLUMN usage_records.operation_type IS 'Type of generation: blog, book, batch, remix, tool, or other';
COMMENT ON COLUMN usage_records.tokens_used IS 'Number of LLM tokens consumed';
COMMENT ON COLUMN usage_records.metadata IS 'Additional operation metadata (provider, model, etc.)';


-- =============================================================================
-- Tier Limits Configuration Table (for dynamic updates without code changes)
-- =============================================================================

CREATE TABLE IF NOT EXISTS tier_limits (
    tier TEXT PRIMARY KEY CHECK (tier IN ('free', 'starter', 'pro', 'business')),
    monthly_limit INTEGER NOT NULL,
    daily_limit INTEGER NOT NULL DEFAULT -1,  -- -1 means unlimited
    features TEXT[] NOT NULL DEFAULT '{}',
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    price_yearly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default tier configurations
INSERT INTO tier_limits (tier, monthly_limit, daily_limit, features, price_monthly, price_yearly, description)
VALUES
    ('free', 5, 2, ARRAY['blog_generation', 'basic_tools'], 0, 0, 'Perfect for trying out Blog AI'),
    ('starter', 50, 10, ARRAY['blog_generation', 'book_generation', 'basic_tools', 'export_formats'], 19, 190, 'For individuals getting started'),
    ('pro', 200, 50, ARRAY['blog_generation', 'book_generation', 'bulk_generation', 'all_tools', 'research_mode', 'brand_voice', 'remix', 'priority_support'], 49, 490, 'For content creators and marketers'),
    ('business', 1000, -1, ARRAY['blog_generation', 'book_generation', 'bulk_generation', 'batch_processing', 'all_tools', 'research_mode', 'brand_voice', 'remix', 'api_access', 'custom_integrations', 'dedicated_support', 'team_collaboration'], 149, 1490, 'For teams and businesses')
ON CONFLICT (tier) DO UPDATE SET
    monthly_limit = EXCLUDED.monthly_limit,
    daily_limit = EXCLUDED.daily_limit,
    features = EXCLUDED.features,
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    description = EXCLUDED.description,
    updated_at = NOW();

COMMENT ON TABLE tier_limits IS 'Configurable tier limits and pricing (source of truth for quota enforcement)';


-- =============================================================================
-- Function: Get Current Month Usage
-- =============================================================================

CREATE OR REPLACE FUNCTION get_current_month_usage(p_user_id TEXT)
RETURNS TABLE (
    usage_count BIGINT,
    tokens_used BIGINT,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ
) AS $$
DECLARE
    v_period_start TIMESTAMPTZ;
    v_period_end TIMESTAMPTZ;
BEGIN
    -- Get user's period bounds or use default monthly period
    SELECT uq.period_start, uq.period_end
    INTO v_period_start, v_period_end
    FROM user_quotas uq
    WHERE uq.user_id = p_user_id;

    -- Default to current month if no quota record exists
    IF v_period_start IS NULL THEN
        v_period_start := date_trunc('month', NOW());
        v_period_end := date_trunc('month', NOW()) + INTERVAL '1 month';
    END IF;

    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as usage_count,
        COALESCE(SUM(ur.tokens_used), 0)::BIGINT as tokens_used,
        v_period_start as period_start,
        v_period_end as period_end
    FROM usage_records ur
    WHERE ur.user_id = p_user_id
      AND ur.timestamp >= v_period_start
      AND ur.timestamp < v_period_end;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_current_month_usage IS 'Returns usage count and tokens for user in current billing period';


-- =============================================================================
-- Function: Get Daily Usage
-- =============================================================================

CREATE OR REPLACE FUNCTION get_daily_usage(p_user_id TEXT)
RETURNS BIGINT AS $$
DECLARE
    v_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM usage_records
    WHERE user_id = p_user_id
      AND timestamp >= date_trunc('day', NOW())
      AND timestamp < date_trunc('day', NOW()) + INTERVAL '1 day';

    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_daily_usage IS 'Returns usage count for user today (UTC)';


-- =============================================================================
-- Function: Check Quota Available
-- =============================================================================

CREATE OR REPLACE FUNCTION check_quota_available(p_user_id TEXT)
RETURNS TABLE (
    has_quota BOOLEAN,
    tier TEXT,
    current_usage BIGINT,
    monthly_limit INTEGER,
    daily_usage BIGINT,
    daily_limit INTEGER,
    remaining INTEGER,
    reset_date TIMESTAMPTZ
) AS $$
DECLARE
    v_tier TEXT;
    v_monthly_limit INTEGER;
    v_daily_limit INTEGER;
    v_current_usage BIGINT;
    v_daily_usage BIGINT;
    v_period_end TIMESTAMPTZ;
BEGIN
    -- Get user tier (default to 'free')
    SELECT COALESCE(uq.tier, 'free'), uq.period_end
    INTO v_tier, v_period_end
    FROM user_quotas uq
    WHERE uq.user_id = p_user_id;

    IF v_tier IS NULL THEN
        v_tier := 'free';
        v_period_end := date_trunc('month', NOW()) + INTERVAL '1 month';
    END IF;

    -- Get tier limits
    SELECT tl.monthly_limit, tl.daily_limit
    INTO v_monthly_limit, v_daily_limit
    FROM tier_limits tl
    WHERE tl.tier = v_tier;

    -- Default limits if tier not found
    IF v_monthly_limit IS NULL THEN
        v_monthly_limit := 5;
        v_daily_limit := 2;
    END IF;

    -- Get current usage
    SELECT usage.usage_count
    INTO v_current_usage
    FROM get_current_month_usage(p_user_id) usage;

    -- Get daily usage
    v_daily_usage := get_daily_usage(p_user_id);

    RETURN QUERY
    SELECT
        -- Has quota if under both limits (-1 means unlimited)
        (v_monthly_limit = -1 OR v_current_usage < v_monthly_limit)
        AND (v_daily_limit = -1 OR v_daily_usage < v_daily_limit) as has_quota,
        v_tier as tier,
        v_current_usage as current_usage,
        v_monthly_limit as monthly_limit,
        v_daily_usage as daily_usage,
        v_daily_limit as daily_limit,
        CASE
            WHEN v_monthly_limit = -1 THEN -1
            ELSE GREATEST(0, v_monthly_limit - v_current_usage::INTEGER)
        END as remaining,
        v_period_end as reset_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_quota_available IS 'Checks if user has remaining quota (both monthly and daily)';


-- =============================================================================
-- Function: Increment User Usage (Atomic)
-- =============================================================================

CREATE OR REPLACE FUNCTION increment_user_usage(
    p_user_id TEXT,
    p_operation_type TEXT,
    p_tokens_used INTEGER DEFAULT 0,
    p_metadata JSONB DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN,
    usage_id UUID,
    new_count BIGINT,
    remaining INTEGER
) AS $$
DECLARE
    v_usage_id UUID;
    v_new_count BIGINT;
    v_monthly_limit INTEGER;
    v_tier TEXT;
BEGIN
    -- Ensure user has a quota record
    INSERT INTO user_quotas (user_id, tier, period_start, period_end)
    VALUES (
        p_user_id,
        'free',
        date_trunc('month', NOW()),
        date_trunc('month', NOW()) + INTERVAL '1 month'
    )
    ON CONFLICT (user_id) DO NOTHING;

    -- Get tier and limit
    SELECT uq.tier
    INTO v_tier
    FROM user_quotas uq
    WHERE uq.user_id = p_user_id;

    SELECT tl.monthly_limit
    INTO v_monthly_limit
    FROM tier_limits tl
    WHERE tl.tier = v_tier;

    IF v_monthly_limit IS NULL THEN
        v_monthly_limit := 5;
    END IF;

    -- Insert usage record
    INSERT INTO usage_records (user_id, operation_type, tokens_used, timestamp, metadata)
    VALUES (p_user_id, p_operation_type, p_tokens_used, NOW(), p_metadata)
    RETURNING id INTO v_usage_id;

    -- Get new count
    SELECT usage_count
    INTO v_new_count
    FROM get_current_month_usage(p_user_id);

    RETURN QUERY
    SELECT
        TRUE as success,
        v_usage_id as usage_id,
        v_new_count as new_count,
        CASE
            WHEN v_monthly_limit = -1 THEN -1
            ELSE GREATEST(0, v_monthly_limit - v_new_count::INTEGER)
        END as remaining;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION increment_user_usage IS 'Atomically records a usage event and returns updated counts';


-- =============================================================================
-- Function: Reset Expired Quotas (for scheduled job)
-- =============================================================================

CREATE OR REPLACE FUNCTION reset_expired_quotas()
RETURNS INTEGER AS $$
DECLARE
    v_reset_count INTEGER;
BEGIN
    WITH expired AS (
        UPDATE user_quotas
        SET
            period_start = date_trunc('month', NOW()),
            period_end = date_trunc('month', NOW()) + INTERVAL '1 month',
            updated_at = NOW()
        WHERE period_end <= NOW()
        RETURNING id
    )
    SELECT COUNT(*) INTO v_reset_count FROM expired;

    RETURN v_reset_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION reset_expired_quotas IS 'Resets billing periods for all expired quotas (call from cron job)';


-- =============================================================================
-- Function: Get Usage Breakdown by Operation Type
-- =============================================================================

CREATE OR REPLACE FUNCTION get_usage_breakdown(
    p_user_id TEXT,
    p_period_start TIMESTAMPTZ DEFAULT NULL,
    p_period_end TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    operation_type TEXT,
    count BIGINT,
    tokens_used BIGINT
) AS $$
BEGIN
    -- Default to current period if not specified
    IF p_period_start IS NULL THEN
        SELECT uq.period_start, uq.period_end
        INTO p_period_start, p_period_end
        FROM user_quotas uq
        WHERE uq.user_id = p_user_id;

        IF p_period_start IS NULL THEN
            p_period_start := date_trunc('month', NOW());
            p_period_end := date_trunc('month', NOW()) + INTERVAL '1 month';
        END IF;
    END IF;

    RETURN QUERY
    SELECT
        ur.operation_type,
        COUNT(*)::BIGINT as count,
        COALESCE(SUM(ur.tokens_used), 0)::BIGINT as tokens_used
    FROM usage_records ur
    WHERE ur.user_id = p_user_id
      AND ur.timestamp >= p_period_start
      AND ur.timestamp < p_period_end
    GROUP BY ur.operation_type
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_usage_breakdown IS 'Returns usage breakdown by operation type for a user';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS on tables
ALTER TABLE user_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tier_limits ENABLE ROW LEVEL SECURITY;

-- User Quotas: Users can only see their own quota
CREATE POLICY "Users can view own quota"
    ON user_quotas
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- User Quotas: Only service role can modify
CREATE POLICY "Service role can manage quotas"
    ON user_quotas
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Usage Records: Users can only see their own records
CREATE POLICY "Users can view own usage"
    ON usage_records
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Usage Records: Only service role can insert/modify
CREATE POLICY "Service role can manage usage records"
    ON usage_records
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Tier Limits: Anyone can read (public pricing info)
CREATE POLICY "Anyone can read tier limits"
    ON tier_limits
    FOR SELECT
    TO anon, authenticated, service_role
    USING (true);

-- Tier Limits: Only service role can modify
CREATE POLICY "Service role can manage tier limits"
    ON tier_limits
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions to relevant roles
GRANT EXECUTE ON FUNCTION get_current_month_usage(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_daily_usage(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION check_quota_available(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION increment_user_usage(TEXT, TEXT, INTEGER, JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION reset_expired_quotas() TO service_role;
GRANT EXECUTE ON FUNCTION get_usage_breakdown(TEXT, TIMESTAMPTZ, TIMESTAMPTZ) TO anon, authenticated, service_role;


-- =============================================================================
-- Trigger: Auto-update updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_quotas_updated_at
    BEFORE UPDATE ON user_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tier_limits_updated_at
    BEFORE UPDATE ON tier_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
