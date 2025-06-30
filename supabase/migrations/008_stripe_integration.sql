-- Migration: Create Stripe integration tables
-- Description: Stores Stripe customer and subscription mappings for webhook sync
--
-- Tables:
--   stripe_customers: Maps user_id to Stripe customer_id
--   stripe_subscriptions: Tracks subscription details
--   payments: Records successful payments
--   payment_failures: Tracks failed payment attempts

-- =============================================================================
-- Stripe Customers Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL UNIQUE,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stripe_customers_user_id ON stripe_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_stripe_customers_customer_id ON stripe_customers(customer_id);

-- Comments
COMMENT ON TABLE stripe_customers IS 'Maps internal user IDs to Stripe customer IDs';
COMMENT ON COLUMN stripe_customers.user_id IS 'Internal user identifier';
COMMENT ON COLUMN stripe_customers.customer_id IS 'Stripe customer ID (cus_xxx)';


-- =============================================================================
-- Stripe Subscriptions Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS stripe_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    customer_id TEXT,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'starter', 'pro', 'business')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'trialing', 'past_due', 'cancelled', 'incomplete')),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_user_id ON stripe_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer_id ON stripe_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_status ON stripe_subscriptions(status);

-- Comments
COMMENT ON TABLE stripe_subscriptions IS 'Tracks Stripe subscription details';
COMMENT ON COLUMN stripe_subscriptions.subscription_id IS 'Stripe subscription ID (sub_xxx)';
COMMENT ON COLUMN stripe_subscriptions.tier IS 'Subscription tier: free, starter, pro, business';
COMMENT ON COLUMN stripe_subscriptions.status IS 'Subscription status: active, trialing, past_due, cancelled, incomplete';


-- =============================================================================
-- Payments Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    subscription_id TEXT,
    invoice_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid', 'refunded', 'partially_refunded')),
    paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_paid_at ON payments(paid_at DESC);

-- Comments
COMMENT ON TABLE payments IS 'Records successful payment events from Stripe';
COMMENT ON COLUMN payments.amount_cents IS 'Payment amount in cents (e.g., 1900 = $19.00)';


-- =============================================================================
-- Payment Failures Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS payment_failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    subscription_id TEXT,
    invoice_id TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    failure_reason TEXT,
    failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payment_failures_user_id ON payment_failures(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_failures_subscription_id ON payment_failures(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payment_failures_unresolved ON payment_failures(user_id)
    WHERE resolved_at IS NULL;

-- Comments
COMMENT ON TABLE payment_failures IS 'Tracks failed payment attempts for monitoring and user notification';


-- =============================================================================
-- Users Table (for proper user management)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    email TEXT,
    name TEXT,
    stripe_customer_id TEXT,
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'pro', 'business')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

-- Comments
COMMENT ON TABLE users IS 'Core user accounts with subscription status';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS
ALTER TABLE stripe_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE stripe_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_failures ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Stripe Customers: Users can view own mapping
CREATE POLICY "Users can view own customer mapping"
    ON stripe_customers
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage customer mappings"
    ON stripe_customers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Stripe Subscriptions: Users can view own subscriptions
CREATE POLICY "Users can view own subscriptions"
    ON stripe_subscriptions
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage subscriptions"
    ON stripe_subscriptions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Payments: Users can view own payments
CREATE POLICY "Users can view own payments"
    ON payments
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage payments"
    ON payments
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Payment Failures: Users can view own failures
CREATE POLICY "Users can view own payment failures"
    ON payment_failures
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage payment failures"
    ON payment_failures
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Users: Users can view/update own profile
CREATE POLICY "Users can view own profile"
    ON users
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can update own profile"
    ON users
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage users"
    ON users
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Triggers for updated_at
-- =============================================================================

CREATE TRIGGER update_stripe_customers_updated_at
    BEFORE UPDATE ON stripe_customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stripe_subscriptions_updated_at
    BEFORE UPDATE ON stripe_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Function: Sync User Tier from Subscription
-- =============================================================================

CREATE OR REPLACE FUNCTION sync_user_tier_from_subscription()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user_quotas tier when subscription changes
    UPDATE user_quotas
    SET tier = NEW.tier,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;

    -- Also update users table if it exists
    UPDATE users
    SET tier = NEW.tier,
        stripe_customer_id = NEW.customer_id,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER sync_tier_on_subscription_change
    AFTER INSERT OR UPDATE ON stripe_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION sync_user_tier_from_subscription();

COMMENT ON FUNCTION sync_user_tier_from_subscription IS 'Automatically syncs user tier in user_quotas when subscription changes';


-- =============================================================================
-- Function: Get Full Subscription Status
-- =============================================================================

CREATE OR REPLACE FUNCTION get_subscription_status(p_user_id TEXT)
RETURNS TABLE (
    has_subscription BOOLEAN,
    tier TEXT,
    status TEXT,
    customer_id TEXT,
    subscription_id TEXT,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN,
    monthly_limit INTEGER,
    current_usage BIGINT,
    remaining INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(ss.status IN ('active', 'trialing'), FALSE) as has_subscription,
        COALESCE(ss.tier, uq.tier, 'free') as tier,
        ss.status,
        ss.customer_id,
        ss.subscription_id,
        ss.current_period_end,
        COALESCE(ss.cancel_at_period_end, FALSE) as cancel_at_period_end,
        tl.monthly_limit,
        COALESCE(usage.usage_count, 0) as current_usage,
        CASE
            WHEN tl.monthly_limit = -1 THEN -1
            ELSE GREATEST(0, tl.monthly_limit - COALESCE(usage.usage_count, 0)::INTEGER)
        END as remaining
    FROM user_quotas uq
    LEFT JOIN stripe_subscriptions ss ON ss.user_id = uq.user_id AND ss.status IN ('active', 'trialing')
    LEFT JOIN tier_limits tl ON tl.tier = COALESCE(ss.tier, uq.tier, 'free')
    LEFT JOIN LATERAL get_current_month_usage(p_user_id) usage ON TRUE
    WHERE uq.user_id = p_user_id;

    -- Return default free tier if user not found
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT
            FALSE as has_subscription,
            'free'::TEXT as tier,
            NULL::TEXT as status,
            NULL::TEXT as customer_id,
            NULL::TEXT as subscription_id,
            NULL::TIMESTAMPTZ as current_period_end,
            FALSE as cancel_at_period_end,
            5 as monthly_limit,
            0::BIGINT as current_usage,
            5 as remaining;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_subscription_status IS 'Returns complete subscription status including usage for a user';

GRANT EXECUTE ON FUNCTION get_subscription_status(TEXT) TO anon, authenticated, service_role;
