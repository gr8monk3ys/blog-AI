-- Rollback: 003_workflows_sso_runtime.sql
-- Description: Drops workflow tables and SSO runtime tables from the db schema.
--
-- WARNING: This will permanently delete all workflow and SSO session data. Back up first.

BEGIN;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS app_sso_user_sessions CASCADE;
DROP TABLE IF EXISTS app_sso_auth_sessions CASCADE;
DROP TABLE IF EXISTS app_sso_configurations CASCADE;
DROP TABLE IF EXISTS app_workflow_executions CASCADE;
DROP TABLE IF EXISTS app_workflows CASCADE;

COMMIT;
