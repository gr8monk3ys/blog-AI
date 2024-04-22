-- Rollback: 016_social_scheduling.sql
-- Description: Drops social_accounts, scheduled_posts, social_campaigns,
--              post_analytics, and social_oauth_state tables along with
--              their functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all social media scheduling data,
--          OAuth tokens, and analytics. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- social_accounts
DROP POLICY IF EXISTS "Users can view own social accounts" ON social_accounts;
DROP POLICY IF EXISTS "Users can insert own social accounts" ON social_accounts;
DROP POLICY IF EXISTS "Users can update own social accounts" ON social_accounts;
DROP POLICY IF EXISTS "Users can delete own social accounts" ON social_accounts;
DROP POLICY IF EXISTS "Service role can manage all social accounts" ON social_accounts;

-- scheduled_posts
DROP POLICY IF EXISTS "Users can view own scheduled posts" ON scheduled_posts;
DROP POLICY IF EXISTS "Users can insert own scheduled posts" ON scheduled_posts;
DROP POLICY IF EXISTS "Users can update own scheduled posts" ON scheduled_posts;
DROP POLICY IF EXISTS "Users can delete own scheduled posts" ON scheduled_posts;
DROP POLICY IF EXISTS "Service role can manage all scheduled posts" ON scheduled_posts;

-- social_campaigns
DROP POLICY IF EXISTS "Users can view own campaigns" ON social_campaigns;
DROP POLICY IF EXISTS "Users can insert own campaigns" ON social_campaigns;
DROP POLICY IF EXISTS "Users can update own campaigns" ON social_campaigns;
DROP POLICY IF EXISTS "Users can delete own campaigns" ON social_campaigns;
DROP POLICY IF EXISTS "Service role can manage all campaigns" ON social_campaigns;

-- post_analytics
DROP POLICY IF EXISTS "Users can view analytics for own posts" ON post_analytics;
DROP POLICY IF EXISTS "Service role can manage all analytics" ON post_analytics;

-- social_oauth_state
DROP POLICY IF EXISTS "Users can view own oauth state" ON social_oauth_state;
DROP POLICY IF EXISTS "Users can insert own oauth state" ON social_oauth_state;
DROP POLICY IF EXISTS "Service role can manage all oauth state" ON social_oauth_state;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS update_social_accounts_updated_at ON social_accounts;
DROP TRIGGER IF EXISTS update_scheduled_posts_updated_at ON scheduled_posts;
DROP TRIGGER IF EXISTS update_social_campaigns_updated_at ON social_campaigns;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS get_due_posts(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS mark_post_publishing(UUID) CASCADE;
DROP FUNCTION IF EXISTS complete_post_publishing(UUID, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS fail_post_publishing(UUID, TEXT, BOOLEAN) CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_oauth_state() CASCADE;
DROP FUNCTION IF EXISTS get_campaign_analytics(UUID) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS social_oauth_state CASCADE;
DROP TABLE IF EXISTS post_analytics CASCADE;
DROP TABLE IF EXISTS scheduled_posts CASCADE;
DROP TABLE IF EXISTS social_campaigns CASCADE;
DROP TABLE IF EXISTS social_accounts CASCADE;

COMMIT;
