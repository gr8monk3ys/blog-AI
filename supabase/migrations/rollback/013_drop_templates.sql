-- Rollback: 013_create_templates.sql
-- Description: Drops the templates table, its function, trigger, and RLS policies.
--
-- WARNING: This will permanently delete all template data. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role has full access to templates" ON templates;
DROP POLICY IF EXISTS "Anonymous can read public templates" ON templates;
DROP POLICY IF EXISTS "Anonymous can create templates" ON templates;
DROP POLICY IF EXISTS "Users can update own templates" ON templates;
DROP POLICY IF EXISTS "Users can delete own templates" ON templates;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_templates_updated_at ON templates;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS increment_template_use_count(UUID) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS templates CASCADE;

COMMIT;
