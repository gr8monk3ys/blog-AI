-- Rollback: 009_content_versions.sql
-- Description: Drops the content_versions table, removes current_version and
--              version_count columns from generated_content, and drops all
--              versioning functions and RLS policies.
--
-- WARNING: This will permanently delete all content version history. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role has full access to content_versions" ON content_versions;
DROP POLICY IF EXISTS "Users can read own content versions" ON content_versions;
DROP POLICY IF EXISTS "Users can create versions of own content" ON content_versions;
DROP POLICY IF EXISTS "Anonymous can read content versions" ON content_versions;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS get_latest_version_number(UUID) CASCADE;
DROP FUNCTION IF EXISTS calculate_content_hash(TEXT) CASCADE;
DROP FUNCTION IF EXISTS create_content_version(UUID, TEXT, TEXT, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_content_versions(UUID, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_content_version(UUID, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS restore_content_version(UUID, INTEGER, TEXT) CASCADE;
DROP FUNCTION IF EXISTS compare_content_versions(UUID, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS has_significant_changes(UUID, TEXT, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS create_initial_version_if_missing(UUID) CASCADE;
DROP FUNCTION IF EXISTS get_version_statistics(UUID) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS content_versions CASCADE;

-- =========================================================================
-- Remove versioning columns from generated_content
-- =========================================================================
ALTER TABLE generated_content DROP COLUMN IF EXISTS current_version;
ALTER TABLE generated_content DROP COLUMN IF EXISTS version_count;

COMMIT;
