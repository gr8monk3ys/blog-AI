-- Rollback: 001_create_generated_content.sql
-- Description: Drops the generated_content table, its trigger, function,
--              and RLS policies.
--
-- WARNING: This will permanently delete ALL generated content history. Back up first.
-- NOTE: The update_updated_at_column() function is shared by many migrations.
--       It is intentionally NOT dropped here. Drop it manually only when
--       rolling back ALL migrations.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role has full access to generated_content" ON generated_content;
DROP POLICY IF EXISTS "Anonymous can insert generated_content" ON generated_content;
DROP POLICY IF EXISTS "Users can read own generated_content" ON generated_content;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_generated_content_updated_at ON generated_content;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS generated_content CASCADE;

-- =========================================================================
-- NOTE: update_updated_at_column() is shared across many tables.
-- Only uncomment the line below if you are rolling back ALL migrations:
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
-- =========================================================================

COMMIT;
