-- Rollback: 002_create_tool_usage.sql
-- Description: Drops the tool_usage table, its functions, and RLS policies.
--
-- WARNING: This will permanently delete all tool usage analytics. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Anyone can read tool_usage" ON tool_usage;
DROP POLICY IF EXISTS "Service role can write tool_usage" ON tool_usage;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS increment_tool_usage(TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_tool_stats() CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS tool_usage CASCADE;

COMMIT;
