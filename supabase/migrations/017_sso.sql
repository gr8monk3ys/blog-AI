-- Migration: SSO (Single Sign-On) Configuration Tables
-- Description: Implements enterprise SSO support for SAML 2.0 and OIDC protocols
--
-- Tables:
--   sso_configurations: Per-organization SSO settings
--   sso_sessions: SSO session tracking for SLO and session management
--   sso_attribute_mappings: Custom attribute/claim mappings
--   sso_used_assertions: Replay protection for SAML assertions and OIDC tokens
--
-- Security:
--   - Sensitive configuration data is encrypted at rest (application layer)
--   - Session tokens are hashed, not stored in plain text
--   - Replay protection via used assertion/token tracking
--   - Row Level Security for multi-tenant isolation

-- =============================================================================
-- SSO Configurations Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS sso_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization reference
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Provider type and status
    provider_type TEXT NOT NULL CHECK (provider_type IN ('saml', 'oidc')),
    enabled BOOLEAN NOT NULL DEFAULT false,
    enforce_sso BOOLEAN NOT NULL DEFAULT false,
    status TEXT NOT NULL DEFAULT 'pending_configuration' CHECK (
        status IN (
            'active',
            'inactive',
            'pending_configuration',
            'configuration_error',
            'certificate_expiring',
            'certificate_expired'
        )
    ),

    -- SAML Configuration (encrypted JSONB)
    -- Contains: idp_entity_id, idp_sso_url, idp_slo_url, idp_certificate,
    --           sp_entity_id, sp_acs_url, sp_slo_url, attribute_mapping
    saml_config JSONB,

    -- OIDC Configuration (encrypted JSONB)
    -- Contains: issuer, discovery_url, client_id, client_secret (encrypted),
    --           redirect_uri, scopes, claim_mapping
    oidc_config JSONB,

    -- Domain restrictions
    allowed_email_domains TEXT[] NOT NULL DEFAULT '{}',

    -- User provisioning settings
    auto_provision_users BOOLEAN NOT NULL DEFAULT true,
    default_role TEXT NOT NULL DEFAULT 'viewer' CHECK (default_role IN ('admin', 'editor', 'viewer')),

    -- Group to role mapping (IdP group name -> organization role)
    group_role_mapping JSONB NOT NULL DEFAULT '{}',

    -- Certificate tracking (for SAML)
    idp_certificate_fingerprint TEXT,
    idp_certificate_expiry TIMESTAMPTZ,
    sp_certificate_fingerprint TEXT,
    sp_certificate_expiry TIMESTAMPTZ,

    -- Status tracking
    last_successful_auth TIMESTAMPTZ,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    error_count INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT NOT NULL,
    updated_by TEXT,

    -- One SSO configuration per organization
    CONSTRAINT unique_org_sso_config UNIQUE (organization_id)
);

-- Indexes for sso_configurations
CREATE INDEX IF NOT EXISTS idx_sso_configs_org_id ON sso_configurations(organization_id);
CREATE INDEX IF NOT EXISTS idx_sso_configs_enabled ON sso_configurations(organization_id) WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_sso_configs_status ON sso_configurations(status);
CREATE INDEX IF NOT EXISTS idx_sso_configs_cert_expiry ON sso_configurations(idp_certificate_expiry)
    WHERE idp_certificate_expiry IS NOT NULL;

-- Comments
COMMENT ON TABLE sso_configurations IS 'SSO configuration per organization (SAML/OIDC)';
COMMENT ON COLUMN sso_configurations.enforce_sso IS 'When true, users must authenticate via SSO (no password login)';
COMMENT ON COLUMN sso_configurations.saml_config IS 'SAML configuration (sensitive data encrypted at application layer)';
COMMENT ON COLUMN sso_configurations.oidc_config IS 'OIDC configuration (client_secret encrypted at application layer)';
COMMENT ON COLUMN sso_configurations.group_role_mapping IS 'Maps IdP groups to organization roles';


-- =============================================================================
-- SSO Sessions Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS sso_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    sso_config_id UUID NOT NULL REFERENCES sso_configurations(id) ON DELETE CASCADE,

    -- Session identifiers (hashed)
    session_token_hash TEXT NOT NULL UNIQUE,

    -- Provider type
    provider_type TEXT NOT NULL CHECK (provider_type IN ('saml', 'oidc')),

    -- SSO user information (from assertion/token)
    provider_user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    display_name TEXT,
    groups TEXT[] DEFAULT '{}',

    -- SAML-specific fields (for SLO)
    saml_session_index TEXT,
    saml_name_id TEXT,
    saml_name_id_format TEXT,

    -- OIDC-specific fields (token hashes for revocation)
    oidc_access_token_hash TEXT,
    oidc_refresh_token_hash TEXT,
    oidc_id_token_hash TEXT,

    -- Session metadata
    ip_address INET,
    user_agent TEXT CHECK (char_length(user_agent) <= 500),

    -- Session lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Indexes for sso_sessions
CREATE INDEX IF NOT EXISTS idx_sso_sessions_org_id ON sso_sessions(organization_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sso_sessions_user_id ON sso_sessions(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sso_sessions_token_hash ON sso_sessions(session_token_hash) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sso_sessions_expires_at ON sso_sessions(expires_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sso_sessions_saml_index ON sso_sessions(saml_session_index)
    WHERE saml_session_index IS NOT NULL AND is_active = true;

-- Comments
COMMENT ON TABLE sso_sessions IS 'Active SSO sessions for session management and SLO';
COMMENT ON COLUMN sso_sessions.session_token_hash IS 'SHA-256 hash of session token (never store plaintext)';
COMMENT ON COLUMN sso_sessions.saml_session_index IS 'SAML SessionIndex for Single Logout';


-- =============================================================================
-- SSO Attribute Mappings Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS sso_attribute_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Configuration reference
    sso_config_id UUID NOT NULL REFERENCES sso_configurations(id) ON DELETE CASCADE,

    -- Mapping details
    source_attribute TEXT NOT NULL,  -- IdP attribute/claim name
    target_field TEXT NOT NULL,      -- Internal field name
    mapping_type TEXT NOT NULL DEFAULT 'direct' CHECK (
        mapping_type IN ('direct', 'transform', 'constant', 'concatenate')
    ),

    -- Transform configuration (for mapping_type = 'transform')
    transform_config JSONB,

    -- Priority (lower = higher priority for conflicts)
    priority INTEGER NOT NULL DEFAULT 100,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique source attribute per configuration
    CONSTRAINT unique_sso_attr_mapping UNIQUE (sso_config_id, source_attribute)
);

-- Indexes for sso_attribute_mappings
CREATE INDEX IF NOT EXISTS idx_sso_attr_mappings_config ON sso_attribute_mappings(sso_config_id) WHERE is_active = true;

-- Comments
COMMENT ON TABLE sso_attribute_mappings IS 'Custom attribute/claim mappings for SSO';
COMMENT ON COLUMN sso_attribute_mappings.mapping_type IS 'How to map: direct (1:1), transform (apply function), constant (fixed value), concatenate (combine multiple)';
COMMENT ON COLUMN sso_attribute_mappings.transform_config IS 'Configuration for non-direct mappings (e.g., regex, format string)';


-- =============================================================================
-- SSO Used Assertions Table (Replay Protection)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sso_used_assertions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization reference
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Assertion/token identifier
    assertion_id TEXT NOT NULL,
    assertion_type TEXT NOT NULL CHECK (assertion_type IN ('saml_assertion', 'oidc_jti', 'oidc_nonce')),

    -- When the assertion was used
    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- When the assertion expires (for cleanup)
    expires_at TIMESTAMPTZ NOT NULL,

    -- Unique assertion per organization
    CONSTRAINT unique_used_assertion UNIQUE (organization_id, assertion_id, assertion_type)
);

-- Indexes for sso_used_assertions
CREATE INDEX IF NOT EXISTS idx_sso_used_assertions_lookup ON sso_used_assertions(organization_id, assertion_id, assertion_type);
CREATE INDEX IF NOT EXISTS idx_sso_used_assertions_expires ON sso_used_assertions(expires_at);

-- Comments
COMMENT ON TABLE sso_used_assertions IS 'Tracks used assertions/tokens for replay attack prevention';
COMMENT ON COLUMN sso_used_assertions.assertion_id IS 'SAML AssertionID or OIDC jti/nonce';


-- =============================================================================
-- Functions
-- =============================================================================

-- Function: Check if assertion has been used (replay protection)
CREATE OR REPLACE FUNCTION check_sso_assertion_replay(
    p_organization_id UUID,
    p_assertion_id TEXT,
    p_assertion_type TEXT,
    p_expires_at TIMESTAMPTZ
)
RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    -- Check if assertion already exists
    SELECT EXISTS (
        SELECT 1 FROM sso_used_assertions
        WHERE organization_id = p_organization_id
          AND assertion_id = p_assertion_id
          AND assertion_type = p_assertion_type
    ) INTO v_exists;

    IF v_exists THEN
        -- Assertion already used - potential replay attack
        RETURN FALSE;
    END IF;

    -- Record the assertion
    INSERT INTO sso_used_assertions (
        organization_id, assertion_id, assertion_type, expires_at
    ) VALUES (
        p_organization_id, p_assertion_id, p_assertion_type, p_expires_at
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_sso_assertion_replay IS 'Check and record assertion for replay protection';


-- Function: Create SSO session
CREATE OR REPLACE FUNCTION create_sso_session(
    p_organization_id UUID,
    p_user_id TEXT,
    p_sso_config_id UUID,
    p_session_token_hash TEXT,
    p_provider_type TEXT,
    p_provider_user_id TEXT,
    p_email TEXT,
    p_display_name TEXT,
    p_groups TEXT[],
    p_expires_at TIMESTAMPTZ,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_saml_session_index TEXT DEFAULT NULL,
    p_saml_name_id TEXT DEFAULT NULL,
    p_saml_name_id_format TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    INSERT INTO sso_sessions (
        organization_id, user_id, sso_config_id, session_token_hash,
        provider_type, provider_user_id, email, display_name, groups,
        expires_at, ip_address, user_agent,
        saml_session_index, saml_name_id, saml_name_id_format
    ) VALUES (
        p_organization_id, p_user_id, p_sso_config_id, p_session_token_hash,
        p_provider_type, p_provider_user_id, p_email, p_display_name, p_groups,
        p_expires_at, p_ip_address, p_user_agent,
        p_saml_session_index, p_saml_name_id, p_saml_name_id_format
    )
    RETURNING id INTO v_session_id;

    -- Update SSO config last successful auth
    UPDATE sso_configurations
    SET last_successful_auth = NOW(),
        last_error = NULL,
        last_error_at = NULL,
        error_count = 0,
        updated_at = NOW()
    WHERE id = p_sso_config_id;

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_sso_session IS 'Create a new SSO session and update config status';


-- Function: Validate and refresh SSO session
CREATE OR REPLACE FUNCTION validate_sso_session(
    p_session_token_hash TEXT
)
RETURNS TABLE (
    is_valid BOOLEAN,
    session_id UUID,
    organization_id UUID,
    user_id TEXT,
    provider_type TEXT,
    email TEXT,
    expires_at TIMESTAMPTZ
) AS $$
DECLARE
    v_session RECORD;
BEGIN
    -- Find active session
    SELECT s.* INTO v_session
    FROM sso_sessions s
    WHERE s.session_token_hash = p_session_token_hash
      AND s.is_active = true
      AND s.expires_at > NOW()
      AND s.revoked_at IS NULL;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::UUID, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TIMESTAMPTZ;
        RETURN;
    END IF;

    -- Update last activity
    UPDATE sso_sessions
    SET last_activity_at = NOW()
    WHERE id = v_session.id;

    RETURN QUERY SELECT
        TRUE,
        v_session.id,
        v_session.organization_id,
        v_session.user_id,
        v_session.provider_type,
        v_session.email,
        v_session.expires_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION validate_sso_session IS 'Validate SSO session and update activity timestamp';


-- Function: Revoke SSO session
CREATE OR REPLACE FUNCTION revoke_sso_session(
    p_session_id UUID,
    p_reason TEXT DEFAULT 'manual_revocation'
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE sso_sessions
    SET is_active = false,
        revoked_at = NOW(),
        revoked_reason = p_reason
    WHERE id = p_session_id
      AND is_active = true;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION revoke_sso_session IS 'Revoke an SSO session';


-- Function: Revoke all SSO sessions for a user (used during SLO)
CREATE OR REPLACE FUNCTION revoke_user_sso_sessions(
    p_organization_id UUID,
    p_user_id TEXT,
    p_reason TEXT DEFAULT 'single_logout'
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE sso_sessions
    SET is_active = false,
        revoked_at = NOW(),
        revoked_reason = p_reason
    WHERE organization_id = p_organization_id
      AND user_id = p_user_id
      AND is_active = true;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION revoke_user_sso_sessions IS 'Revoke all SSO sessions for a user (e.g., during SLO)';


-- Function: Record SSO error
CREATE OR REPLACE FUNCTION record_sso_error(
    p_sso_config_id UUID,
    p_error_message TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE sso_configurations
    SET last_error = p_error_message,
        last_error_at = NOW(),
        error_count = error_count + 1,
        status = CASE
            WHEN error_count >= 5 THEN 'configuration_error'
            ELSE status
        END,
        updated_at = NOW()
    WHERE id = p_sso_config_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION record_sso_error IS 'Record an SSO error and update status if threshold reached';


-- Function: Clean up expired assertions
CREATE OR REPLACE FUNCTION cleanup_expired_sso_assertions()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    DELETE FROM sso_used_assertions
    WHERE expires_at < NOW();

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_expired_sso_assertions IS 'Remove expired assertions from replay protection table';


-- Function: Clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sso_sessions()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE sso_sessions
    SET is_active = false,
        revoked_at = NOW(),
        revoked_reason = 'expired'
    WHERE is_active = true
      AND expires_at < NOW();

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_expired_sso_sessions IS 'Deactivate expired SSO sessions';


-- Function: Get SSO configuration for organization
CREATE OR REPLACE FUNCTION get_sso_configuration(
    p_organization_id UUID
)
RETURNS TABLE (
    id UUID,
    provider_type TEXT,
    enabled BOOLEAN,
    enforce_sso BOOLEAN,
    status TEXT,
    saml_config JSONB,
    oidc_config JSONB,
    allowed_email_domains TEXT[],
    auto_provision_users BOOLEAN,
    default_role TEXT,
    group_role_mapping JSONB,
    last_successful_auth TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.provider_type,
        c.enabled,
        c.enforce_sso,
        c.status,
        c.saml_config,
        c.oidc_config,
        c.allowed_email_domains,
        c.auto_provision_users,
        c.default_role,
        c.group_role_mapping,
        c.last_successful_auth
    FROM sso_configurations c
    WHERE c.organization_id = p_organization_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_sso_configuration IS 'Get SSO configuration for an organization';


-- =============================================================================
-- Triggers
-- =============================================================================

-- Trigger: Auto-update updated_at for sso_configurations
CREATE TRIGGER update_sso_configurations_updated_at
    BEFORE UPDATE ON sso_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at for sso_attribute_mappings
CREATE TRIGGER update_sso_attribute_mappings_updated_at
    BEFORE UPDATE ON sso_attribute_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS on all SSO tables
ALTER TABLE sso_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sso_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sso_attribute_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE sso_used_assertions ENABLE ROW LEVEL SECURITY;

-- SSO Configurations: Only admins/owners can view
CREATE POLICY "Admins can view SSO configurations"
    ON sso_configurations
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = sso_configurations.organization_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
              AND om.role IN ('owner', 'admin')
        )
    );

-- SSO Configurations: Service role full access
CREATE POLICY "Service role full access to SSO configurations"
    ON sso_configurations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- SSO Sessions: Users can view their own sessions, admins can view all
CREATE POLICY "Users can view their SSO sessions"
    ON sso_sessions
    FOR SELECT
    TO authenticated
    USING (
        user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        OR EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = sso_sessions.organization_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
              AND om.role IN ('owner', 'admin')
        )
    );

-- SSO Sessions: Service role full access
CREATE POLICY "Service role full access to SSO sessions"
    ON sso_sessions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- SSO Attribute Mappings: Only admins/owners can view
CREATE POLICY "Admins can view SSO attribute mappings"
    ON sso_attribute_mappings
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM sso_configurations sc
            JOIN organization_members om ON om.organization_id = sc.organization_id
            WHERE sc.id = sso_attribute_mappings.sso_config_id
              AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
              AND om.is_active = true
              AND om.role IN ('owner', 'admin')
        )
    );

-- SSO Attribute Mappings: Service role full access
CREATE POLICY "Service role full access to SSO attribute mappings"
    ON sso_attribute_mappings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- SSO Used Assertions: Service role only (security-critical)
CREATE POLICY "Service role only for used assertions"
    ON sso_used_assertions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION check_sso_assertion_replay(UUID, TEXT, TEXT, TIMESTAMPTZ) TO service_role;
GRANT EXECUTE ON FUNCTION create_sso_session(UUID, TEXT, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT[], TIMESTAMPTZ, INET, TEXT, TEXT, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION validate_sso_session(TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION revoke_sso_session(UUID, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION revoke_user_sso_sessions(UUID, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION record_sso_error(UUID, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_sso_assertions() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_sso_sessions() TO service_role;
GRANT EXECUTE ON FUNCTION get_sso_configuration(UUID) TO authenticated, service_role;


-- =============================================================================
-- Update Organization Settings for SSO
-- =============================================================================

-- Add SSO feature flag to organization settings if not already present
UPDATE organizations
SET settings = settings || '{"sso_configured": false}'::jsonb
WHERE NOT (settings ? 'sso_configured');


-- =============================================================================
-- Scheduled Cleanup (optional - requires pg_cron extension)
-- =============================================================================

-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('cleanup-sso-assertions', '0 * * * *', 'SELECT cleanup_expired_sso_assertions()');
-- SELECT cron.schedule('cleanup-sso-sessions', '*/15 * * * *', 'SELECT cleanup_expired_sso_sessions()');
