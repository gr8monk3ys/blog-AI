-- Rollback: 008_stripe_integration.sql
-- Description: Drops Stripe integration tables (stripe_customers,
--              stripe_subscriptions, payments, payment_failures, users),
--              their functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all payment and subscription data.
--          Billing will stop working. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- stripe_customers
DROP POLICY IF EXISTS "Users can view own customer mapping" ON stripe_customers;
DROP POLICY IF EXISTS "Service role can manage customer mappings" ON stripe_customers;

-- stripe_subscriptions
DROP POLICY IF EXISTS "Users can view own subscriptions" ON stripe_subscriptions;
DROP POLICY IF EXISTS "Service role can manage subscriptions" ON stripe_subscriptions;

-- payments
DROP POLICY IF EXISTS "Users can view own payments" ON payments;
DROP POLICY IF EXISTS "Service role can manage payments" ON payments;

-- payment_failures
DROP POLICY IF EXISTS "Users can view own payment failures" ON payment_failures;
DROP POLICY IF EXISTS "Service role can manage payment failures" ON payment_failures;

-- users
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Service role can manage users" ON users;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS sync_tier_on_subscription_change ON stripe_subscriptions;
DROP TRIGGER IF EXISTS update_stripe_customers_updated_at ON stripe_customers;
DROP TRIGGER IF EXISTS update_stripe_subscriptions_updated_at ON stripe_subscriptions;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS sync_user_tier_from_subscription() CASCADE;
DROP FUNCTION IF EXISTS get_subscription_status(TEXT) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS payment_failures CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS stripe_subscriptions CASCADE;
DROP TABLE IF EXISTS stripe_customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

COMMIT;
