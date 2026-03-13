-- Rollback: 018_content_feedback.sql
-- Description: Drops the content_feedback table, its function, trigger,
--              and RLS policies.
--
-- WARNING: This will permanently delete all content feedback data. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Anyone can insert feedback" ON content_feedback;
DROP POLICY IF EXISTS "Users can view own feedback" ON content_feedback;
DROP POLICY IF EXISTS "Service role can manage all feedback" ON content_feedback;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_content_feedback_updated_at ON content_feedback;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS get_content_feedback_stats(TEXT) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS content_feedback CASCADE;

COMMIT;
