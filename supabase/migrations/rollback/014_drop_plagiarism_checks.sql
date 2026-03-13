-- Rollback: 014_plagiarism_checks.sql
-- Description: Drops plagiarism_checks and plagiarism_sources tables along with
--              their functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all plagiarism check history. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Users can view own plagiarism checks" ON plagiarism_checks;
DROP POLICY IF EXISTS "Service role can manage plagiarism checks" ON plagiarism_checks;
DROP POLICY IF EXISTS "Users can view own plagiarism sources" ON plagiarism_sources;
DROP POLICY IF EXISTS "Service role can manage plagiarism sources" ON plagiarism_sources;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_plagiarism_checks_updated_at ON plagiarism_checks;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS get_cached_plagiarism_check(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS store_plagiarism_check(TEXT, TEXT, TEXT, TEXT, DECIMAL, DECIMAL, TEXT, INTEGER, INTEGER, INTEGER, DECIMAL, INTEGER, TEXT, JSONB, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS add_plagiarism_source(UUID, TEXT, TEXT, DECIMAL, INTEGER, TEXT, BOOLEAN, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_user_plagiarism_stats(TEXT, TIMESTAMPTZ, TIMESTAMPTZ) CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_plagiarism_cache() CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS plagiarism_sources CASCADE;
DROP TABLE IF EXISTS plagiarism_checks CASCADE;

COMMIT;
