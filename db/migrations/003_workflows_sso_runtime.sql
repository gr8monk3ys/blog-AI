-- Workflow + SSO runtime persistence (Neon/Postgres)
--
-- Adds durable storage for:
-- - Custom workflows and executions (backend workflow routes)
-- - SSO org configs and session state (backend SSO routes)

-- =============================================================================
-- Workflows
-- =============================================================================

CREATE TABLE IF NOT EXISTS app_workflows (
  id text PRIMARY KEY,
  user_id text NOT NULL,
  name text NOT NULL,
  description text NOT NULL DEFAULT '',
  steps jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_workflows_user_id
  ON app_workflows(user_id);

CREATE TABLE IF NOT EXISTS app_workflow_executions (
  execution_id text PRIMARY KEY,
  workflow_id text NOT NULL,
  workflow_name text NOT NULL,
  user_id text NOT NULL,
  status text NOT NULL,
  current_step text,
  started_at timestamptz NOT NULL DEFAULT NOW(),
  completed_at timestamptz,
  error text,
  results jsonb NOT NULL DEFAULT '{}'::jsonb,
  provider text,
  variables jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_app_workflow_exec_workflow_started
  ON app_workflow_executions(workflow_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_workflow_exec_user_started
  ON app_workflow_executions(user_id, started_at DESC);

-- =============================================================================
-- SSO
-- =============================================================================

CREATE TABLE IF NOT EXISTS app_sso_configurations (
  organization_id text PRIMARY KEY,
  config_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_sso_auth_sessions (
  session_id text PRIMARY KEY,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  expires_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_sso_auth_sessions_expires
  ON app_sso_auth_sessions(expires_at);

CREATE TABLE IF NOT EXISTS app_sso_user_sessions (
  session_id text PRIMARY KEY,
  organization_id text NOT NULL,
  user_id text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  expires_at timestamptz NOT NULL,
  last_activity_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_sso_user_sessions_org
  ON app_sso_user_sessions(organization_id, expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_sso_user_sessions_expires
  ON app_sso_user_sessions(expires_at);
