-- Rollback: 005_create_brand_profiles.sql
-- Description: Drops the brand_profiles table, its function, trigger,
--              and RLS policies.
--
-- WARNING: This will permanently delete all brand profile data. Back up first.
-- NOTE: If migration 006 (voice training) has been applied, roll that back first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role has full access to brand_profiles" ON brand_profiles;
DROP POLICY IF EXISTS "Anonymous can read own brand_profiles" ON brand_profiles;
DROP POLICY IF EXISTS "Anonymous can create brand_profiles" ON brand_profiles;
DROP POLICY IF EXISTS "Anonymous can update own brand_profiles" ON brand_profiles;
DROP POLICY IF EXISTS "Anonymous can delete own brand_profiles" ON brand_profiles;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_brand_profiles_updated_at ON brand_profiles;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS set_default_brand_profile(UUID, TEXT) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS brand_profiles CASCADE;

COMMIT;
