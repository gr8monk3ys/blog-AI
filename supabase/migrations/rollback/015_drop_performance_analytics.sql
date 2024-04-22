-- Rollback: 015_performance_analytics.sql
-- Description: Drops content_performance, performance_events, performance_snapshots,
--              seo_rankings, and content_recommendations tables along with their
--              views, functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all performance analytics data. Back up first.

BEGIN;

-- =========================================================================
-- Drop Views
-- =========================================================================
DROP VIEW IF EXISTS v_seo_opportunities CASCADE;
DROP VIEW IF EXISTS v_active_content_performance CASCADE;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Org members can view content performance" ON content_performance;
DROP POLICY IF EXISTS "Service role full access to content_performance" ON content_performance;
DROP POLICY IF EXISTS "Org members can view performance events" ON performance_events;
DROP POLICY IF EXISTS "Service role full access to performance_events" ON performance_events;
DROP POLICY IF EXISTS "Org members can view snapshots" ON performance_snapshots;
DROP POLICY IF EXISTS "Service role full access to snapshots" ON performance_snapshots;
DROP POLICY IF EXISTS "Org members can view SEO rankings" ON seo_rankings;
DROP POLICY IF EXISTS "Service role full access to SEO rankings" ON seo_rankings;
DROP POLICY IF EXISTS "Org members can view recommendations" ON content_recommendations;
DROP POLICY IF EXISTS "Service role full access to recommendations" ON content_recommendations;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_content_performance_updated_at ON content_performance;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS increment_content_metric(TEXT, TEXT, NUMERIC) CASCADE;
DROP FUNCTION IF EXISTS create_daily_snapshot(TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_performance_trend(TEXT, TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_top_content(UUID, TEXT, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_performance_summary(UUID, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_performance_events(INTEGER) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS content_recommendations CASCADE;
DROP TABLE IF EXISTS seo_rankings CASCADE;
DROP TABLE IF EXISTS performance_snapshots CASCADE;
DROP TABLE IF EXISTS performance_events CASCADE;
DROP TABLE IF EXISTS content_performance CASCADE;

COMMIT;
