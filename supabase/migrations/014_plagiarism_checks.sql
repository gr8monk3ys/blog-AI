-- Migration: Create plagiarism check tables and functions
-- Description: Implements storage for plagiarism detection results with caching
--
-- Tables:
--   plagiarism_checks: Stores plagiarism check results and metadata
--   plagiarism_sources: Stores matching sources for each check
--
-- Features:
--   - Content hash-based caching to avoid duplicate API costs
--   - User-level usage tracking for plagiarism checks
--   - Matching source details with similarity scores
--   - Provider tracking for cost analysis
--
-- This migration supports multiple plagiarism providers:
--   - copyscape: Copyscape Premium API
--   - originality: Originality.ai API
--   - embedding: Local embedding-based similarity

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Plagiarism Checks Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS plagiarism_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and content identification
    user_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,  -- SHA-256 hash of content for deduplication

    -- Check results
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cached')),
    provider TEXT NOT NULL
        CHECK (provider IN ('copyscape', 'originality', 'embedding')),

    -- Scores and analysis
    overall_score DECIMAL(5, 2) NOT NULL DEFAULT 0
        CHECK (overall_score >= 0 AND overall_score <= 100),
    original_percentage DECIMAL(5, 2) NOT NULL DEFAULT 100
        CHECK (original_percentage >= 0 AND original_percentage <= 100),
    risk_level TEXT NOT NULL DEFAULT 'none'
        CHECK (risk_level IN ('none', 'low', 'moderate', 'high', 'critical')),

    -- Content metadata
    total_words_checked INTEGER NOT NULL DEFAULT 0,
    total_matched_words INTEGER NOT NULL DEFAULT 0,
    sources_count INTEGER NOT NULL DEFAULT 0,

    -- Cost tracking
    api_credits_used DECIMAL(10, 4) NOT NULL DEFAULT 0,

    -- Processing info
    processing_time_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,

    -- Provider-specific metadata
    provider_metadata JSONB DEFAULT '{}',

    -- Caching
    is_cached BOOLEAN NOT NULL DEFAULT FALSE,
    cache_expires_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for user queries
CREATE INDEX IF NOT EXISTS idx_plagiarism_checks_user_id
    ON plagiarism_checks(user_id, created_at DESC);

-- Index for cache lookups (most important for cost optimization)
CREATE INDEX IF NOT EXISTS idx_plagiarism_checks_content_hash
    ON plagiarism_checks(content_hash, created_at DESC);

-- Index for finding valid cached results
CREATE INDEX IF NOT EXISTS idx_plagiarism_checks_cache
    ON plagiarism_checks(content_hash, status)
    WHERE status = 'completed';

-- Index for provider analytics
CREATE INDEX IF NOT EXISTS idx_plagiarism_checks_provider
    ON plagiarism_checks(provider, created_at DESC);

-- Index for risk level filtering
CREATE INDEX IF NOT EXISTS idx_plagiarism_checks_risk
    ON plagiarism_checks(user_id, risk_level)
    WHERE status = 'completed';

-- Comments
COMMENT ON TABLE plagiarism_checks IS 'Stores plagiarism detection check results and metadata';
COMMENT ON COLUMN plagiarism_checks.content_hash IS 'SHA-256 hash of content for cache deduplication';
COMMENT ON COLUMN plagiarism_checks.overall_score IS 'Plagiarism score (0 = original, 100 = fully plagiarized)';
COMMENT ON COLUMN plagiarism_checks.original_percentage IS 'Percentage of content that is original (100 - overall_score)';
COMMENT ON COLUMN plagiarism_checks.api_credits_used IS 'Credits consumed from plagiarism API provider';


-- =============================================================================
-- Plagiarism Sources Table (matching sources for each check)
-- =============================================================================

CREATE TABLE IF NOT EXISTS plagiarism_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to parent check
    check_id UUID NOT NULL REFERENCES plagiarism_checks(id) ON DELETE CASCADE,

    -- Source details
    url TEXT NOT NULL,
    title TEXT,
    similarity_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0
        CHECK (similarity_percentage >= 0 AND similarity_percentage <= 100),
    matched_words INTEGER NOT NULL DEFAULT 0,
    matched_text TEXT,  -- Sample of matched text (truncated)
    is_exact_match BOOLEAN NOT NULL DEFAULT FALSE,

    -- Ordering
    rank INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for check lookups
CREATE INDEX IF NOT EXISTS idx_plagiarism_sources_check_id
    ON plagiarism_sources(check_id, similarity_percentage DESC);

-- Comments
COMMENT ON TABLE plagiarism_sources IS 'Matching sources found during plagiarism checks';
COMMENT ON COLUMN plagiarism_sources.matched_text IS 'Sample of matched text, truncated to 1000 chars';


-- =============================================================================
-- Function: Get Cached Plagiarism Check
-- =============================================================================

CREATE OR REPLACE FUNCTION get_cached_plagiarism_check(
    p_content_hash TEXT,
    p_max_age_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    check_id UUID,
    status TEXT,
    provider TEXT,
    overall_score DECIMAL(5, 2),
    original_percentage DECIMAL(5, 2),
    risk_level TEXT,
    sources_count INTEGER,
    created_at TIMESTAMPTZ,
    is_valid BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pc.id as check_id,
        pc.status,
        pc.provider,
        pc.overall_score,
        pc.original_percentage,
        pc.risk_level,
        pc.sources_count,
        pc.created_at,
        (pc.status = 'completed'
            AND pc.created_at > NOW() - (p_max_age_hours || ' hours')::INTERVAL
        ) as is_valid
    FROM plagiarism_checks pc
    WHERE pc.content_hash = p_content_hash
      AND pc.status = 'completed'
    ORDER BY pc.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_cached_plagiarism_check IS 'Retrieves cached plagiarism check result if available and valid';


-- =============================================================================
-- Function: Store Plagiarism Check Result
-- =============================================================================

CREATE OR REPLACE FUNCTION store_plagiarism_check(
    p_user_id TEXT,
    p_content_hash TEXT,
    p_status TEXT,
    p_provider TEXT,
    p_overall_score DECIMAL(5, 2),
    p_original_percentage DECIMAL(5, 2),
    p_risk_level TEXT,
    p_total_words INTEGER,
    p_matched_words INTEGER,
    p_sources_count INTEGER,
    p_credits_used DECIMAL(10, 4),
    p_processing_time_ms INTEGER,
    p_error_message TEXT DEFAULT NULL,
    p_provider_metadata JSONB DEFAULT '{}',
    p_cache_hours INTEGER DEFAULT 24
)
RETURNS UUID AS $$
DECLARE
    v_check_id UUID;
    v_cache_expires TIMESTAMPTZ;
BEGIN
    -- Calculate cache expiration
    v_cache_expires := NOW() + (p_cache_hours || ' hours')::INTERVAL;

    -- Insert the check record
    INSERT INTO plagiarism_checks (
        user_id,
        content_hash,
        status,
        provider,
        overall_score,
        original_percentage,
        risk_level,
        total_words_checked,
        total_matched_words,
        sources_count,
        api_credits_used,
        processing_time_ms,
        error_message,
        provider_metadata,
        is_cached,
        cache_expires_at
    ) VALUES (
        p_user_id,
        p_content_hash,
        p_status,
        p_provider,
        p_overall_score,
        p_original_percentage,
        p_risk_level,
        p_total_words,
        p_matched_words,
        p_sources_count,
        p_credits_used,
        p_processing_time_ms,
        p_error_message,
        p_provider_metadata,
        FALSE,
        v_cache_expires
    )
    RETURNING id INTO v_check_id;

    RETURN v_check_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION store_plagiarism_check IS 'Stores a plagiarism check result with automatic cache expiration';


-- =============================================================================
-- Function: Add Plagiarism Source
-- =============================================================================

CREATE OR REPLACE FUNCTION add_plagiarism_source(
    p_check_id UUID,
    p_url TEXT,
    p_title TEXT,
    p_similarity DECIMAL(5, 2),
    p_matched_words INTEGER,
    p_matched_text TEXT DEFAULT NULL,
    p_is_exact_match BOOLEAN DEFAULT FALSE,
    p_rank INTEGER DEFAULT 0
)
RETURNS UUID AS $$
DECLARE
    v_source_id UUID;
BEGIN
    INSERT INTO plagiarism_sources (
        check_id,
        url,
        title,
        similarity_percentage,
        matched_words,
        matched_text,
        is_exact_match,
        rank
    ) VALUES (
        p_check_id,
        p_url,
        p_title,
        p_similarity,
        p_matched_words,
        LEFT(p_matched_text, 1000),  -- Truncate to 1000 chars
        p_is_exact_match,
        p_rank
    )
    RETURNING id INTO v_source_id;

    RETURN v_source_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION add_plagiarism_source IS 'Adds a matching source to a plagiarism check';


-- =============================================================================
-- Function: Get User Plagiarism Statistics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_user_plagiarism_stats(
    p_user_id TEXT,
    p_period_start TIMESTAMPTZ DEFAULT NULL,
    p_period_end TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    total_checks BIGINT,
    avg_originality DECIMAL(5, 2),
    high_risk_count BIGINT,
    total_credits_used DECIMAL(10, 2),
    provider_breakdown JSONB,
    risk_breakdown JSONB
) AS $$
BEGIN
    -- Default to last 30 days if no period specified
    IF p_period_start IS NULL THEN
        p_period_start := NOW() - INTERVAL '30 days';
    END IF;
    IF p_period_end IS NULL THEN
        p_period_end := NOW();
    END IF;

    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_checks,
        COALESCE(AVG(pc.original_percentage), 100)::DECIMAL(5, 2) as avg_originality,
        COUNT(*) FILTER (
            WHERE pc.risk_level IN ('high', 'critical')
        )::BIGINT as high_risk_count,
        COALESCE(SUM(pc.api_credits_used), 0)::DECIMAL(10, 2) as total_credits_used,
        jsonb_object_agg(
            COALESCE(provider_counts.provider, 'unknown'),
            provider_counts.count
        ) as provider_breakdown,
        jsonb_object_agg(
            COALESCE(risk_counts.risk_level, 'unknown'),
            risk_counts.count
        ) as risk_breakdown
    FROM plagiarism_checks pc
    LEFT JOIN LATERAL (
        SELECT provider, COUNT(*)::INTEGER as count
        FROM plagiarism_checks
        WHERE user_id = p_user_id
          AND status = 'completed'
          AND created_at BETWEEN p_period_start AND p_period_end
        GROUP BY provider
    ) provider_counts ON TRUE
    LEFT JOIN LATERAL (
        SELECT risk_level, COUNT(*)::INTEGER as count
        FROM plagiarism_checks
        WHERE user_id = p_user_id
          AND status = 'completed'
          AND created_at BETWEEN p_period_start AND p_period_end
        GROUP BY risk_level
    ) risk_counts ON TRUE
    WHERE pc.user_id = p_user_id
      AND pc.status = 'completed'
      AND pc.created_at BETWEEN p_period_start AND p_period_end;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_plagiarism_stats IS 'Returns aggregated plagiarism check statistics for a user';


-- =============================================================================
-- Function: Cleanup Expired Cache
-- =============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_plagiarism_cache()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Delete checks older than 30 days with no user reference
    -- or expired cache entries older than 7 days
    WITH deleted AS (
        DELETE FROM plagiarism_checks
        WHERE (cache_expires_at < NOW() - INTERVAL '7 days')
           OR (created_at < NOW() - INTERVAL '90 days')
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_expired_plagiarism_cache IS 'Removes old plagiarism check records (run periodically via cron)';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS on tables
ALTER TABLE plagiarism_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE plagiarism_sources ENABLE ROW LEVEL SECURITY;

-- Plagiarism Checks: Users can only see their own checks
CREATE POLICY "Users can view own plagiarism checks"
    ON plagiarism_checks
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Plagiarism Checks: Only service role can insert/modify
CREATE POLICY "Service role can manage plagiarism checks"
    ON plagiarism_checks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Plagiarism Sources: Users can view sources for their checks
CREATE POLICY "Users can view own plagiarism sources"
    ON plagiarism_sources
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM plagiarism_checks pc
            WHERE pc.id = plagiarism_sources.check_id
            AND (
                pc.user_id = auth.uid()::TEXT
                OR pc.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
            )
        )
    );

-- Plagiarism Sources: Only service role can insert/modify
CREATE POLICY "Service role can manage plagiarism sources"
    ON plagiarism_sources
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions to relevant roles
GRANT EXECUTE ON FUNCTION get_cached_plagiarism_check(TEXT, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION store_plagiarism_check(TEXT, TEXT, TEXT, TEXT, DECIMAL, DECIMAL, TEXT, INTEGER, INTEGER, INTEGER, DECIMAL, INTEGER, TEXT, JSONB, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION add_plagiarism_source(UUID, TEXT, TEXT, DECIMAL, INTEGER, TEXT, BOOLEAN, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION get_user_plagiarism_stats(TEXT, TIMESTAMPTZ, TIMESTAMPTZ) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_plagiarism_cache() TO service_role;


-- =============================================================================
-- Trigger: Auto-update updated_at
-- =============================================================================

CREATE TRIGGER update_plagiarism_checks_updated_at
    BEFORE UPDATE ON plagiarism_checks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
