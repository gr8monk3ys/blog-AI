-- Rollback: 007_usage_quotas.sql
-- Description: Drops user_quotas, usage_records, and tier_limits tables along
--              with their functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all usage tracking and quota data.
--          Quota enforcement will stop working. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- user_quotas
DROP POLICY IF EXISTS "Users can view own quota" ON user_quotas;
DROP POLICY IF EXISTS "Service role can manage quotas" ON user_quotas;

-- usage_records
DROP POLICY IF EXISTS "Users can view own usage" ON usage_records;
DROP POLICY IF EXISTS "Service role can manage usage records" ON usage_records;

-- tier_limits
DROP POLICY IF EXISTS "Anyone can read tier limits" ON tier_limits;
DROP POLICY IF EXISTS "Service role can manage tier limits" ON tier_limits;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS update_user_quotas_updated_at ON user_quotas;
DROP TRIGGER IF EXISTS update_tier_limits_updated_at ON tier_limits;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS get_current_month_usage(TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_daily_usage(TEXT) CASCADE;
DROP FUNCTION IF EXISTS check_quota_available(TEXT) CASCADE;
DROP FUNCTION IF EXISTS increment_user_usage(TEXT, TEXT, INTEGER, JSONB) CASCADE;
DROP FUNCTION IF EXISTS reset_expired_quotas() CASCADE;
DROP FUNCTION IF EXISTS get_usage_breakdown(TEXT, TIMESTAMPTZ, TIMESTAMPTZ) CASCADE;

-- =========================================================================
-- Drop Tables
-- =========================================================================
DROP TABLE IF EXISTS usage_records CASCADE;
DROP TABLE IF EXISTS tier_limits CASCADE;
DROP TABLE IF EXISTS user_quotas CASCADE;

COMMIT;
