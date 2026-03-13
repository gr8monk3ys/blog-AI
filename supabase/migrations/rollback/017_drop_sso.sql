-- Rollback: 017_sso.sql
-- Description: Drops all SSO tables (sso_configurations, sso_sessions,
--              sso_attribute_mappings, sso_used_assertions), their functions,
--              triggers, and RLS policies.
--
-- WARNING: This will permanently delete all SSO configuration and session data.
--          Users relying on SSO will lose access until reconfigured. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Admins can view SSO configurations" ON sso_configurations;
DROP POLICY IF EXISTS "Service role full access to SSO configurations" ON sso_configurations;
DROP POLICY IF EXISTS "Users can view their SSO sessions" ON sso_sessions;
DROP POLICY IF EXISTS "Service role full access to SSO sessions" ON sso_sessions;
DROP POLICY IF EXISTS "Admins can view SSO attribute mappings" ON sso_attribute_mappings;
DROP POLICY IF EXISTS "Service role full access to SSO attribute mappings" ON sso_attribute_mappings;
DROP POLICY IF EXISTS "Service role only for used assertions" ON sso_used_assertions;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS update_sso_configurations_updated_at ON sso_configurations;
DROP TRIGGER IF EXISTS update_sso_attribute_mappings_updated_at ON sso_attribute_mappings;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS check_sso_assertion_replay(UUID, TEXT, TEXT, TIMESTAMPTZ) CASCADE;
DROP FUNCTION IF EXISTS create_sso_session(UUID, TEXT, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT[], TIMESTAMPTZ, INET, TEXT, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS validate_sso_session(TEXT) CASCADE;
DROP FUNCTION IF EXISTS revoke_sso_session(UUID, TEXT) CASCADE;
DROP FUNCTION IF EXISTS revoke_user_sso_sessions(UUID, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS record_sso_error(UUID, TEXT) CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_sso_assertions() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_sso_sessions() CASCADE;
DROP FUNCTION IF EXISTS get_sso_configuration(UUID) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS sso_used_assertions CASCADE;
DROP TABLE IF EXISTS sso_attribute_mappings CASCADE;
DROP TABLE IF EXISTS sso_sessions CASCADE;
DROP TABLE IF EXISTS sso_configurations CASCADE;

-- =========================================================================
-- Remove sso_configured flag from organization settings
-- =========================================================================
UPDATE organizations
SET settings = settings - 'sso_configured'
WHERE settings ? 'sso_configured';

COMMIT;
