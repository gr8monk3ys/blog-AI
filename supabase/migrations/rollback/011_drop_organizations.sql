-- Rollback: 011_organizations.sql
-- Description: Drops organization tables (organizations, organization_members,
--              organization_invites, audit_logs, role_permissions,
--              organization_plan_limits), their functions, triggers, and
--              RLS policies. Also removes organization_id columns added to
--              brand_profiles, generated_content, and templates.
--
-- WARNING: This will permanently delete ALL organization and team data,
--          including audit logs and RBAC configuration. Back up first.

BEGIN;

-- =========================================================================
-- Remove organization_id columns from existing tables
-- =========================================================================
ALTER TABLE brand_profiles DROP COLUMN IF EXISTS organization_id;
ALTER TABLE generated_content DROP COLUMN IF EXISTS organization_id;
ALTER TABLE templates DROP COLUMN IF EXISTS organization_id;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- organizations
DROP POLICY IF EXISTS "Members can view their organizations" ON organizations;
DROP POLICY IF EXISTS "Service role full access to organizations" ON organizations;

-- organization_members
DROP POLICY IF EXISTS "Members can view org members" ON organization_members;
DROP POLICY IF EXISTS "Service role full access to organization_members" ON organization_members;

-- organization_invites
DROP POLICY IF EXISTS "Members can view org invites" ON organization_invites;
DROP POLICY IF EXISTS "Service role full access to organization_invites" ON organization_invites;

-- audit_logs
DROP POLICY IF EXISTS "Admins can view audit logs" ON audit_logs;
DROP POLICY IF EXISTS "Service role full access to audit_logs" ON audit_logs;

-- role_permissions
DROP POLICY IF EXISTS "Anyone can read role permissions" ON role_permissions;

-- organization_plan_limits
DROP POLICY IF EXISTS "Anyone can read plan limits" ON organization_plan_limits;
DROP POLICY IF EXISTS "Service role can manage plan limits" ON organization_plan_limits;

-- =========================================================================
-- Drop Triggers
-- =========================================================================
DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
DROP TRIGGER IF EXISTS update_organization_members_updated_at ON organization_members;
DROP TRIGGER IF EXISTS update_organization_invites_updated_at ON organization_invites;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS create_organization_with_owner(TEXT, TEXT, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS check_organization_permission(UUID, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_user_organizations(TEXT) CASCADE;
DROP FUNCTION IF EXISTS generate_invite_token() CASCADE;
DROP FUNCTION IF EXISTS accept_organization_invite(TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS check_organization_quota(UUID) CASCADE;
DROP FUNCTION IF EXISTS increment_organization_usage(UUID, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS log_audit_event(UUID, TEXT, TEXT, TEXT, TEXT, JSONB, JSONB, JSONB, INET, TEXT, TEXT, BOOLEAN, TEXT) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS organization_plan_limits CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS organization_invites CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

COMMIT;
