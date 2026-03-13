-- Rollback: 005_organizations.sql
-- Description: Drops organization, member, invite, and audit log tables
--              created by the db/migrations/005_organizations migration.
--
-- WARNING: This will permanently delete all organization data. Back up first.

BEGIN;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS organization_invites CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

COMMIT;
