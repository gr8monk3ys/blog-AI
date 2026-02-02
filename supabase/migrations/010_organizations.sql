-- Migration: Create organization and team management tables
-- Description: Implements multi-tenant organization support with RBAC
--
-- Tables:
--   organizations: Core organization/workspace table
--   organization_members: Organization membership with roles
--   organization_invites: Pending invitations
--   audit_logs: Comprehensive audit trail for compliance
--
-- Roles:
--   - owner: Full control including delete organization
--   - admin: Manage members and settings (cannot delete org)
--   - editor: Create and edit content
--   - viewer: Read-only access
--
-- Security:
--   - Row Level Security for multi-tenant isolation
--   - Audit logging for compliance
--   - Secure invite token handling

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Organizations Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic information
    name TEXT NOT NULL CHECK (char_length(name) >= 1 AND char_length(name) <= 100),
    slug TEXT NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' AND char_length(slug) >= 3 AND char_length(slug) <= 50),
    description TEXT CHECK (char_length(description) <= 500),

    -- Subscription and billing
    plan_tier TEXT NOT NULL DEFAULT 'free' CHECK (plan_tier IN ('free', 'starter', 'pro', 'business', 'enterprise')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,

    -- Settings (JSONB for flexibility)
    settings JSONB NOT NULL DEFAULT '{
        "default_brand_profile_id": null,
        "content_approval_required": false,
        "sso_enabled": false,
        "allowed_domains": [],
        "max_members": 5,
        "features": {}
    }'::jsonb,

    -- Quotas (organization-level)
    monthly_generation_limit INTEGER NOT NULL DEFAULT 100,
    current_month_usage INTEGER NOT NULL DEFAULT 0,
    quota_reset_date TIMESTAMPTZ NOT NULL DEFAULT date_trunc('month', NOW()) + INTERVAL '1 month',

    -- Metadata
    logo_url TEXT CHECK (logo_url IS NULL OR logo_url ~ '^https?://'),
    website_url TEXT CHECK (website_url IS NULL OR website_url ~ '^https?://'),

    -- Soft delete support
    is_active BOOLEAN NOT NULL DEFAULT true,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL
);

-- Indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_organizations_created_by ON organizations(created_by);
CREATE INDEX IF NOT EXISTS idx_organizations_plan_tier ON organizations(plan_tier) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_customer ON organizations(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_organizations_quota_reset ON organizations(quota_reset_date);

-- Comments
COMMENT ON TABLE organizations IS 'Organizations/workspaces for team collaboration';
COMMENT ON COLUMN organizations.slug IS 'URL-friendly unique identifier (3-50 chars, lowercase alphanumeric with hyphens)';
COMMENT ON COLUMN organizations.settings IS 'Organization settings including SSO, approval workflows, feature flags';
COMMENT ON COLUMN organizations.monthly_generation_limit IS 'Monthly content generation limit based on plan';


-- =============================================================================
-- Organization Members Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign keys
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,  -- Matches user_id from API key auth

    -- Role with strict enum
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),

    -- Invitation tracking
    invited_by UUID REFERENCES organization_members(id),
    invite_accepted_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    deactivated_at TIMESTAMPTZ,
    deactivated_by UUID,
    deactivation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one membership per user per org
    CONSTRAINT unique_org_member UNIQUE (organization_id, user_id)
);

-- Indexes for organization_members
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(organization_id, role) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_org_members_invited_by ON organization_members(invited_by);

-- Comments
COMMENT ON TABLE organization_members IS 'Organization membership with role assignments';
COMMENT ON COLUMN organization_members.role IS 'Member role: owner, admin, editor, or viewer';
COMMENT ON COLUMN organization_members.invite_accepted_at IS 'When the user accepted the invitation (null if direct add)';


-- =============================================================================
-- Organization Invites Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_invites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign keys
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES organization_members(id),

    -- Invitation details
    email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer')),  -- Cannot invite as owner

    -- Secure token (hashed in DB, plaintext sent via email)
    token_hash TEXT NOT NULL,

    -- Expiration and status
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '7 days',
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES organization_members(id),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID,

    -- Metadata
    message TEXT CHECK (char_length(message) <= 500),  -- Optional personal message
    resend_count INTEGER NOT NULL DEFAULT 0,
    last_resent_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one pending invite per email per org
    CONSTRAINT unique_pending_invite UNIQUE (organization_id, email)
        DEFERRABLE INITIALLY DEFERRED
);

-- Indexes for organization_invites
CREATE INDEX IF NOT EXISTS idx_org_invites_org_id ON organization_invites(organization_id) WHERE accepted_at IS NULL AND revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_org_invites_email ON organization_invites(email) WHERE accepted_at IS NULL AND revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_org_invites_token_hash ON organization_invites(token_hash) WHERE accepted_at IS NULL AND revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_org_invites_expires_at ON organization_invites(expires_at) WHERE accepted_at IS NULL AND revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_org_invites_invited_by ON organization_invites(invited_by);

-- Comments
COMMENT ON TABLE organization_invites IS 'Pending organization invitations';
COMMENT ON COLUMN organization_invites.token_hash IS 'SHA-256 hash of the invitation token (plaintext token sent via email)';
COMMENT ON COLUMN organization_invites.role IS 'Role to assign when invite is accepted (owner role cannot be invited)';


-- =============================================================================
-- Audit Logs Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Context
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    user_id TEXT,  -- Can be null for system actions

    -- Action details
    action TEXT NOT NULL CHECK (char_length(action) >= 1 AND char_length(action) <= 100),
    resource_type TEXT NOT NULL CHECK (char_length(resource_type) >= 1 AND char_length(resource_type) <= 50),
    resource_id TEXT,

    -- Change details
    metadata JSONB DEFAULT '{}',
    old_values JSONB,  -- Previous state for updates
    new_values JSONB,  -- New state for creates/updates

    -- Request context
    ip_address INET,
    user_agent TEXT CHECK (char_length(user_agent) <= 500),
    request_id TEXT,  -- Correlation ID from request headers

    -- Result
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,

    -- Timestamp (immutable)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for audit_logs (optimized for common query patterns)
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id_time ON audit_logs(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id_time ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Partial index for failed actions (useful for security monitoring)
CREATE INDEX IF NOT EXISTS idx_audit_logs_failures ON audit_logs(organization_id, created_at DESC) WHERE success = false;

-- Comments
COMMENT ON TABLE audit_logs IS 'Immutable audit trail for compliance and security monitoring';
COMMENT ON COLUMN audit_logs.action IS 'Action performed (e.g., create_content, invite_member, update_settings)';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource affected (e.g., organization, member, content)';
COMMENT ON COLUMN audit_logs.old_values IS 'Previous values before update (for change tracking)';
COMMENT ON COLUMN audit_logs.new_values IS 'New values after create/update';


-- =============================================================================
-- Role Permissions Reference Table (for documentation and potential dynamic updates)
-- =============================================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),
    permission TEXT NOT NULL,
    description TEXT,

    PRIMARY KEY (role, permission)
);

-- Insert permission definitions
INSERT INTO role_permissions (role, permission, description) VALUES
    -- Owner permissions (all permissions)
    ('owner', 'organization.delete', 'Delete the organization'),
    ('owner', 'organization.transfer', 'Transfer ownership to another member'),
    ('owner', 'organization.update', 'Update organization settings'),
    ('owner', 'organization.view', 'View organization details'),
    ('owner', 'members.manage', 'Add, remove, and update member roles'),
    ('owner', 'members.invite', 'Invite new members'),
    ('owner', 'members.view', 'View member list'),
    ('owner', 'content.create', 'Create new content'),
    ('owner', 'content.edit', 'Edit any content'),
    ('owner', 'content.delete', 'Delete any content'),
    ('owner', 'content.view', 'View all content'),
    ('owner', 'content.publish', 'Publish content'),
    ('owner', 'brand.manage', 'Manage brand profiles'),
    ('owner', 'brand.view', 'View brand profiles'),
    ('owner', 'templates.manage', 'Manage templates'),
    ('owner', 'templates.view', 'View templates'),
    ('owner', 'billing.manage', 'Manage billing and subscriptions'),
    ('owner', 'billing.view', 'View billing information'),
    ('owner', 'audit.view', 'View audit logs'),

    -- Admin permissions (everything except delete org and transfer ownership)
    ('admin', 'organization.update', 'Update organization settings'),
    ('admin', 'organization.view', 'View organization details'),
    ('admin', 'members.manage', 'Add, remove, and update member roles'),
    ('admin', 'members.invite', 'Invite new members'),
    ('admin', 'members.view', 'View member list'),
    ('admin', 'content.create', 'Create new content'),
    ('admin', 'content.edit', 'Edit any content'),
    ('admin', 'content.delete', 'Delete any content'),
    ('admin', 'content.view', 'View all content'),
    ('admin', 'content.publish', 'Publish content'),
    ('admin', 'brand.manage', 'Manage brand profiles'),
    ('admin', 'brand.view', 'View brand profiles'),
    ('admin', 'templates.manage', 'Manage templates'),
    ('admin', 'templates.view', 'View templates'),
    ('admin', 'billing.view', 'View billing information'),
    ('admin', 'audit.view', 'View audit logs'),

    -- Editor permissions
    ('editor', 'organization.view', 'View organization details'),
    ('editor', 'members.view', 'View member list'),
    ('editor', 'content.create', 'Create new content'),
    ('editor', 'content.edit', 'Edit own content'),
    ('editor', 'content.delete', 'Delete own content'),
    ('editor', 'content.view', 'View all content'),
    ('editor', 'brand.view', 'View brand profiles'),
    ('editor', 'templates.view', 'View templates'),

    -- Viewer permissions
    ('viewer', 'organization.view', 'View organization details'),
    ('viewer', 'members.view', 'View member list'),
    ('viewer', 'content.view', 'View all content'),
    ('viewer', 'brand.view', 'View brand profiles'),
    ('viewer', 'templates.view', 'View templates')
ON CONFLICT (role, permission) DO NOTHING;

COMMENT ON TABLE role_permissions IS 'Reference table for role-based access control permissions';


-- =============================================================================
-- Organization Plan Limits Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_plan_limits (
    plan_tier TEXT PRIMARY KEY CHECK (plan_tier IN ('free', 'starter', 'pro', 'business', 'enterprise')),

    -- Member limits
    max_members INTEGER NOT NULL,

    -- Generation limits
    monthly_generation_limit INTEGER NOT NULL,

    -- Feature flags
    features JSONB NOT NULL DEFAULT '{}',

    -- Pricing
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0,
    price_yearly DECIMAL(10, 2) NOT NULL DEFAULT 0,

    -- Metadata
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default plan configurations
INSERT INTO organization_plan_limits (plan_tier, max_members, monthly_generation_limit, features, price_monthly, price_yearly, description) VALUES
    ('free', 3, 25, '{"sso": false, "api_access": false, "custom_branding": false, "priority_support": false}', 0, 0, 'Free tier for small teams'),
    ('starter', 5, 100, '{"sso": false, "api_access": true, "custom_branding": false, "priority_support": false}', 29, 290, 'Starter tier for growing teams'),
    ('pro', 15, 500, '{"sso": false, "api_access": true, "custom_branding": true, "priority_support": true}', 79, 790, 'Pro tier for professional teams'),
    ('business', 50, 2000, '{"sso": true, "api_access": true, "custom_branding": true, "priority_support": true, "dedicated_support": true}', 199, 1990, 'Business tier for large teams'),
    ('enterprise', -1, -1, '{"sso": true, "api_access": true, "custom_branding": true, "priority_support": true, "dedicated_support": true, "custom_integrations": true}', 0, 0, 'Enterprise tier with custom pricing')
ON CONFLICT (plan_tier) DO UPDATE SET
    max_members = EXCLUDED.max_members,
    monthly_generation_limit = EXCLUDED.monthly_generation_limit,
    features = EXCLUDED.features,
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    description = EXCLUDED.description,
    updated_at = NOW();

COMMENT ON TABLE organization_plan_limits IS 'Plan-based limits for organizations';
COMMENT ON COLUMN organization_plan_limits.max_members IS 'Maximum members allowed (-1 for unlimited)';
COMMENT ON COLUMN organization_plan_limits.monthly_generation_limit IS 'Monthly generation limit (-1 for unlimited)';


-- =============================================================================
-- Functions
-- =============================================================================

-- Function: Create organization with owner
CREATE OR REPLACE FUNCTION create_organization_with_owner(
    p_name TEXT,
    p_slug TEXT,
    p_user_id TEXT,
    p_description TEXT DEFAULT NULL,
    p_plan_tier TEXT DEFAULT 'free'
)
RETURNS TABLE (
    organization_id UUID,
    member_id UUID
) AS $$
DECLARE
    v_org_id UUID;
    v_member_id UUID;
    v_plan_limits RECORD;
BEGIN
    -- Get plan limits
    SELECT * INTO v_plan_limits FROM organization_plan_limits WHERE plan_tier = p_plan_tier;
    IF NOT FOUND THEN
        v_plan_limits := (SELECT * FROM organization_plan_limits WHERE plan_tier = 'free');
    END IF;

    -- Create organization
    INSERT INTO organizations (
        name, slug, description, plan_tier,
        monthly_generation_limit, created_by,
        settings
    )
    VALUES (
        p_name, p_slug, p_description, p_plan_tier,
        v_plan_limits.monthly_generation_limit,
        uuid_generate_v4(),  -- Placeholder, will update below
        jsonb_build_object(
            'default_brand_profile_id', NULL,
            'content_approval_required', false,
            'sso_enabled', (v_plan_limits.features->>'sso')::boolean,
            'allowed_domains', '[]'::jsonb,
            'max_members', v_plan_limits.max_members,
            'features', v_plan_limits.features
        )
    )
    RETURNING id INTO v_org_id;

    -- Create owner membership
    INSERT INTO organization_members (
        organization_id, user_id, role, invite_accepted_at
    )
    VALUES (
        v_org_id, p_user_id, 'owner', NOW()
    )
    RETURNING id INTO v_member_id;

    -- Update organization with actual created_by
    UPDATE organizations SET created_by = v_member_id WHERE id = v_org_id;

    RETURN QUERY SELECT v_org_id, v_member_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_organization_with_owner IS 'Creates an organization and assigns the creator as owner';


-- Function: Check if user has permission in organization
CREATE OR REPLACE FUNCTION check_organization_permission(
    p_organization_id UUID,
    p_user_id TEXT,
    p_permission TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_role TEXT;
BEGIN
    -- Get user's role in the organization
    SELECT role INTO v_role
    FROM organization_members
    WHERE organization_id = p_organization_id
      AND user_id = p_user_id
      AND is_active = true;

    IF v_role IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if role has the permission
    RETURN EXISTS (
        SELECT 1 FROM role_permissions
        WHERE role = v_role AND permission = p_permission
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_organization_permission IS 'Checks if a user has a specific permission in an organization';


-- Function: Get user's organizations
CREATE OR REPLACE FUNCTION get_user_organizations(p_user_id TEXT)
RETURNS TABLE (
    organization_id UUID,
    organization_name TEXT,
    organization_slug TEXT,
    role TEXT,
    plan_tier TEXT,
    member_count BIGINT,
    joined_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        om.role,
        o.plan_tier,
        (SELECT COUNT(*) FROM organization_members WHERE organization_id = o.id AND is_active = true),
        om.created_at
    FROM organizations o
    JOIN organization_members om ON o.id = om.organization_id
    WHERE om.user_id = p_user_id
      AND om.is_active = true
      AND o.is_active = true
    ORDER BY om.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_organizations IS 'Returns all organizations a user is a member of';


-- Function: Generate and hash invite token
CREATE OR REPLACE FUNCTION generate_invite_token()
RETURNS TABLE (
    token TEXT,
    token_hash TEXT
) AS $$
DECLARE
    v_token TEXT;
    v_hash TEXT;
BEGIN
    -- Generate a secure random token
    v_token := encode(gen_random_bytes(32), 'base64');
    -- Replace URL-unsafe characters
    v_token := replace(replace(v_token, '+', '-'), '/', '_');
    -- Remove padding
    v_token := rtrim(v_token, '=');

    -- Hash the token for storage
    v_hash := encode(digest(v_token, 'sha256'), 'hex');

    RETURN QUERY SELECT v_token, v_hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION generate_invite_token IS 'Generates a secure invite token and its hash';


-- Function: Accept organization invite
CREATE OR REPLACE FUNCTION accept_organization_invite(
    p_token TEXT,
    p_user_id TEXT
)
RETURNS TABLE (
    success BOOLEAN,
    organization_id UUID,
    member_id UUID,
    error_message TEXT
) AS $$
DECLARE
    v_token_hash TEXT;
    v_invite RECORD;
    v_member_id UUID;
    v_existing_member UUID;
BEGIN
    -- Hash the provided token
    v_token_hash := encode(digest(p_token, 'sha256'), 'hex');

    -- Find the invite
    SELECT * INTO v_invite
    FROM organization_invites
    WHERE token_hash = v_token_hash
      AND accepted_at IS NULL
      AND revoked_at IS NULL
      AND expires_at > NOW();

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::UUID, 'Invalid or expired invitation token';
        RETURN;
    END IF;

    -- Check if user is already a member
    SELECT id INTO v_existing_member
    FROM organization_members
    WHERE organization_id = v_invite.organization_id
      AND user_id = p_user_id
      AND is_active = true;

    IF FOUND THEN
        RETURN QUERY SELECT FALSE, v_invite.organization_id, v_existing_member, 'User is already a member of this organization';
        RETURN;
    END IF;

    -- Create membership
    INSERT INTO organization_members (
        organization_id, user_id, role, invited_by, invite_accepted_at
    )
    VALUES (
        v_invite.organization_id, p_user_id, v_invite.role, v_invite.invited_by, NOW()
    )
    RETURNING id INTO v_member_id;

    -- Mark invite as accepted
    UPDATE organization_invites
    SET accepted_at = NOW(), accepted_by = v_member_id, updated_at = NOW()
    WHERE id = v_invite.id;

    RETURN QUERY SELECT TRUE, v_invite.organization_id, v_member_id, NULL::TEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION accept_organization_invite IS 'Accepts an organization invitation and creates membership';


-- Function: Check organization quota
CREATE OR REPLACE FUNCTION check_organization_quota(p_organization_id UUID)
RETURNS TABLE (
    has_quota BOOLEAN,
    current_usage INTEGER,
    monthly_limit INTEGER,
    remaining INTEGER,
    reset_date TIMESTAMPTZ
) AS $$
DECLARE
    v_org RECORD;
BEGIN
    SELECT * INTO v_org
    FROM organizations
    WHERE id = p_organization_id AND is_active = true;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0, 0, 0, NOW();
        RETURN;
    END IF;

    -- Reset quota if needed
    IF v_org.quota_reset_date <= NOW() THEN
        UPDATE organizations
        SET current_month_usage = 0,
            quota_reset_date = date_trunc('month', NOW()) + INTERVAL '1 month',
            updated_at = NOW()
        WHERE id = p_organization_id;

        v_org.current_month_usage := 0;
        v_org.quota_reset_date := date_trunc('month', NOW()) + INTERVAL '1 month';
    END IF;

    RETURN QUERY SELECT
        (v_org.monthly_generation_limit = -1 OR v_org.current_month_usage < v_org.monthly_generation_limit),
        v_org.current_month_usage,
        v_org.monthly_generation_limit,
        CASE
            WHEN v_org.monthly_generation_limit = -1 THEN -1
            ELSE GREATEST(0, v_org.monthly_generation_limit - v_org.current_month_usage)
        END,
        v_org.quota_reset_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_organization_quota IS 'Checks if organization has remaining quota';


-- Function: Increment organization usage
CREATE OR REPLACE FUNCTION increment_organization_usage(
    p_organization_id UUID,
    p_amount INTEGER DEFAULT 1
)
RETURNS TABLE (
    success BOOLEAN,
    new_usage INTEGER,
    remaining INTEGER
) AS $$
DECLARE
    v_org RECORD;
    v_new_usage INTEGER;
BEGIN
    -- Lock the row for update
    SELECT * INTO v_org
    FROM organizations
    WHERE id = p_organization_id AND is_active = true
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0, 0;
        RETURN;
    END IF;

    -- Reset if needed
    IF v_org.quota_reset_date <= NOW() THEN
        v_org.current_month_usage := 0;
    END IF;

    v_new_usage := v_org.current_month_usage + p_amount;

    UPDATE organizations
    SET current_month_usage = v_new_usage,
        quota_reset_date = CASE
            WHEN quota_reset_date <= NOW() THEN date_trunc('month', NOW()) + INTERVAL '1 month'
            ELSE quota_reset_date
        END,
        updated_at = NOW()
    WHERE id = p_organization_id;

    RETURN QUERY SELECT
        TRUE,
        v_new_usage,
        CASE
            WHEN v_org.monthly_generation_limit = -1 THEN -1
            ELSE GREATEST(0, v_org.monthly_generation_limit - v_new_usage)
        END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION increment_organization_usage IS 'Atomically increments organization usage counter';


-- Function: Log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_organization_id UUID,
    p_user_id TEXT,
    p_action TEXT,
    p_resource_type TEXT,
    p_resource_id TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}',
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_request_id TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO audit_logs (
        organization_id, user_id, action, resource_type, resource_id,
        metadata, old_values, new_values,
        ip_address, user_agent, request_id,
        success, error_message
    )
    VALUES (
        p_organization_id, p_user_id, p_action, p_resource_type, p_resource_id,
        p_metadata, p_old_values, p_new_values,
        p_ip_address, p_user_agent, p_request_id,
        p_success, p_error_message
    )
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION log_audit_event IS 'Records an audit log entry';


-- =============================================================================
-- Triggers
-- =============================================================================

-- Trigger: Auto-update updated_at for organizations
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at for organization_members
CREATE TRIGGER update_organization_members_updated_at
    BEFORE UPDATE ON organization_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at for organization_invites
CREATE TRIGGER update_organization_invites_updated_at
    BEFORE UPDATE ON organization_invites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_plan_limits ENABLE ROW LEVEL SECURITY;

-- Organizations: Members can view their organizations
CREATE POLICY "Members can view their organizations"
    ON organizations
    FOR SELECT
    TO authenticated
    USING (
        is_active = true AND
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = organizations.id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
        )
    );

-- Organizations: Service role full access
CREATE POLICY "Service role full access to organizations"
    ON organizations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Organization Members: Members can view other members in their orgs
CREATE POLICY "Members can view org members"
    ON organization_members
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = organization_members.organization_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
        )
    );

-- Organization Members: Service role full access
CREATE POLICY "Service role full access to organization_members"
    ON organization_members
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Organization Invites: Members with invite permission can view invites
CREATE POLICY "Members can view org invites"
    ON organization_invites
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = organization_invites.organization_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
              AND om.role IN ('owner', 'admin')
        )
    );

-- Organization Invites: Service role full access
CREATE POLICY "Service role full access to organization_invites"
    ON organization_invites
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Audit Logs: Admins and owners can view audit logs
CREATE POLICY "Admins can view audit logs"
    ON audit_logs
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = audit_logs.organization_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
              AND om.role IN ('owner', 'admin')
        )
    );

-- Audit Logs: Service role full access
CREATE POLICY "Service role full access to audit_logs"
    ON audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Role Permissions: Anyone can read
CREATE POLICY "Anyone can read role permissions"
    ON role_permissions
    FOR SELECT
    TO anon, authenticated, service_role
    USING (true);

-- Organization Plan Limits: Anyone can read
CREATE POLICY "Anyone can read plan limits"
    ON organization_plan_limits
    FOR SELECT
    TO anon, authenticated, service_role
    USING (true);

-- Service role can manage plan limits
CREATE POLICY "Service role can manage plan limits"
    ON organization_plan_limits
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION create_organization_with_owner(TEXT, TEXT, TEXT, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION check_organization_permission(UUID, TEXT, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_user_organizations(TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION generate_invite_token() TO service_role;
GRANT EXECUTE ON FUNCTION accept_organization_invite(TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION check_organization_quota(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION increment_organization_usage(UUID, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION log_audit_event(UUID, TEXT, TEXT, TEXT, TEXT, JSONB, JSONB, JSONB, INET, TEXT, TEXT, BOOLEAN, TEXT) TO service_role;


-- =============================================================================
-- Add organization reference to existing tables (if they exist)
-- =============================================================================

-- Add org_id to brand_profiles if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'brand_profiles') THEN
        ALTER TABLE brand_profiles ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
        CREATE INDEX IF NOT EXISTS idx_brand_profiles_org_id ON brand_profiles(organization_id) WHERE organization_id IS NOT NULL;
    END IF;
END $$;

-- Add org_id to generated_content if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'generated_content') THEN
        ALTER TABLE generated_content ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
        CREATE INDEX IF NOT EXISTS idx_generated_content_org_id ON generated_content(organization_id) WHERE organization_id IS NOT NULL;
    END IF;
END $$;

-- Add org_id to templates if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'templates') THEN
        ALTER TABLE templates ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
        CREATE INDEX IF NOT EXISTS idx_templates_org_id ON templates(organization_id) WHERE organization_id IS NOT NULL;
    END IF;
END $$;
