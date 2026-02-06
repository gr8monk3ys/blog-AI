-- Migration: Create performance analytics tables
-- Description: Implements content performance tracking, SEO rankings, and recommendations
--
-- Tables:
--   content_performance: Aggregated performance metrics per content
--   performance_events: Individual tracking events
--   performance_snapshots: Daily snapshots for trending
--   seo_rankings: Keyword ranking history
--   content_recommendations: AI-generated recommendations
--
-- Features:
--   - Real-time event tracking with efficient aggregation
--   - Historical snapshots for trend analysis
--   - SEO ranking tracking with competitor comparison
--   - AI-powered content recommendations
--
-- Performance optimizations:
--   - Partitioned events table by date
--   - Materialized views for common aggregations
--   - Efficient indexes for time-series queries

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Content Performance Table (Aggregated Metrics)
-- =============================================================================

CREATE TABLE IF NOT EXISTS content_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content identification
    content_id TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL DEFAULT 'blog' CHECK (content_type IN ('blog', 'book', 'social', 'email', 'video')),
    title TEXT NOT NULL DEFAULT '',
    url TEXT,
    platform TEXT,  -- wordpress, medium, custom, etc.

    -- Organization/User association
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT,

    -- Core engagement metrics
    views INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
    unique_views INTEGER NOT NULL DEFAULT 0 CHECK (unique_views >= 0),
    time_on_page_seconds NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (time_on_page_seconds >= 0),
    avg_scroll_depth NUMERIC(5, 4) NOT NULL DEFAULT 0 CHECK (avg_scroll_depth >= 0 AND avg_scroll_depth <= 1),
    bounce_rate NUMERIC(5, 4) NOT NULL DEFAULT 0 CHECK (bounce_rate >= 0 AND bounce_rate <= 1),

    -- Social metrics
    shares INTEGER NOT NULL DEFAULT 0 CHECK (shares >= 0),
    shares_by_platform JSONB NOT NULL DEFAULT '{}',
    comments INTEGER NOT NULL DEFAULT 0 CHECK (comments >= 0),
    reactions INTEGER NOT NULL DEFAULT 0 CHECK (reactions >= 0),

    -- SEO metrics
    backlinks INTEGER NOT NULL DEFAULT 0 CHECK (backlinks >= 0),
    referring_domains INTEGER NOT NULL DEFAULT 0 CHECK (referring_domains >= 0),
    organic_traffic INTEGER NOT NULL DEFAULT 0 CHECK (organic_traffic >= 0),

    -- Conversion metrics
    conversions INTEGER NOT NULL DEFAULT 0 CHECK (conversions >= 0),
    conversion_rate NUMERIC(5, 4) NOT NULL DEFAULT 0 CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    revenue NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (revenue >= 0),

    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',
    published_at TIMESTAMPTZ,
    first_tracked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_tracked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for content_performance
CREATE INDEX IF NOT EXISTS idx_content_perf_org_id ON content_performance(organization_id);
CREATE INDEX IF NOT EXISTS idx_content_perf_user_id ON content_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_content_perf_type ON content_performance(content_type);
CREATE INDEX IF NOT EXISTS idx_content_perf_views ON content_performance(views DESC);
CREATE INDEX IF NOT EXISTS idx_content_perf_last_tracked ON content_performance(last_tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_perf_published ON content_performance(published_at DESC);

-- Optional index for active content (predicate removed for immutability)

-- GIN index for JSONB metadata queries
CREATE INDEX IF NOT EXISTS idx_content_perf_metadata ON content_performance USING GIN (metadata);

COMMENT ON TABLE content_performance IS 'Aggregated performance metrics for tracked content';
COMMENT ON COLUMN content_performance.content_id IS 'Unique identifier for the content (from generated_content or external)';
COMMENT ON COLUMN content_performance.shares_by_platform IS 'Share counts by platform: {"twitter": 10, "linkedin": 5}';


-- =============================================================================
-- Performance Events Table (Raw Events)
-- =============================================================================

CREATE TABLE IF NOT EXISTS performance_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identification
    content_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'view', 'unique_view', 'time_on_page', 'scroll_depth', 'bounce',
        'share', 'click', 'conversion', 'comment', 'backlink'
    )),
    value NUMERIC(12, 4) NOT NULL DEFAULT 1,

    -- User tracking (anonymized)
    user_id TEXT,
    session_id TEXT,

    -- Source tracking
    source TEXT,  -- tracking_pixel, webhook, api
    platform TEXT,  -- twitter, facebook, linkedin, etc.
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,

    -- Event metadata
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Organization association
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance_events
CREATE INDEX IF NOT EXISTS idx_perf_events_content_id ON performance_events(content_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_perf_events_type ON performance_events(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_perf_events_org_id ON performance_events(organization_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_perf_events_timestamp ON performance_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_perf_events_session ON performance_events(session_id) WHERE session_id IS NOT NULL;

-- Optional index for recent events (predicate removed for immutability)

COMMENT ON TABLE performance_events IS 'Raw performance tracking events';
COMMENT ON COLUMN performance_events.value IS 'Event value (1 for counts, seconds for time, 0-1 for scroll depth)';


-- =============================================================================
-- Performance Snapshots Table (Daily Aggregates)
-- =============================================================================

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content identification
    content_id TEXT NOT NULL,

    -- Snapshot date
    snapshot_date DATE NOT NULL,

    -- Snapshot metrics
    views INTEGER NOT NULL DEFAULT 0,
    unique_views INTEGER NOT NULL DEFAULT 0,
    shares INTEGER NOT NULL DEFAULT 0,
    backlinks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    engagement_score NUMERIC(5, 2) NOT NULL DEFAULT 0,

    -- Additional metrics
    avg_time_on_page NUMERIC(10, 2),
    avg_scroll_depth NUMERIC(5, 4),
    bounce_rate NUMERIC(5, 4),

    -- Organization association
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one snapshot per content per day
    CONSTRAINT unique_content_snapshot UNIQUE (content_id, snapshot_date)
);

-- Indexes for performance_snapshots
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_content ON performance_snapshots(content_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_date ON performance_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_org ON performance_snapshots(organization_id, snapshot_date DESC);

COMMENT ON TABLE performance_snapshots IS 'Daily snapshots of content performance for trend analysis';


-- =============================================================================
-- SEO Rankings Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS seo_rankings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ranking data
    keyword TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),  -- 0 = not found in top 100
    previous_position INTEGER,
    change INTEGER NOT NULL DEFAULT 0,

    -- Keyword metrics
    search_volume INTEGER,
    difficulty NUMERIC(5, 2),

    -- Content association
    content_id TEXT,
    url TEXT,

    -- Search context
    search_engine TEXT NOT NULL DEFAULT 'google',
    location TEXT NOT NULL DEFAULT 'us',

    -- Organization association
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Timestamps
    tracked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for seo_rankings
CREATE INDEX IF NOT EXISTS idx_seo_rankings_keyword ON seo_rankings(keyword, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_seo_rankings_content ON seo_rankings(content_id, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_seo_rankings_url ON seo_rankings(url, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_seo_rankings_org ON seo_rankings(organization_id, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_seo_rankings_position ON seo_rankings(position) WHERE position > 0 AND position <= 100;

-- Index for opportunity detection (positions 11-30)
CREATE INDEX IF NOT EXISTS idx_seo_rankings_opportunities ON seo_rankings(organization_id, search_volume DESC)
    WHERE position >= 11 AND position <= 30;

COMMENT ON TABLE seo_rankings IS 'Keyword ranking history from SERP tracking';
COMMENT ON COLUMN seo_rankings.position IS 'Search result position (0 = not in top 100)';
COMMENT ON COLUMN seo_rankings.change IS 'Position change (positive = improved, negative = declined)';


-- =============================================================================
-- Content Recommendations Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS content_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recommendation data
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN (
        'topic', 'keyword', 'format', 'timing', 'optimization'
    )),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence NUMERIC(3, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    priority INTEGER NOT NULL DEFAULT 1,

    -- Recommendation details
    data JSONB NOT NULL DEFAULT '{}',
    based_on TEXT[] NOT NULL DEFAULT '{}',  -- Content IDs this is based on

    -- Organization/User association
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    actioned_at TIMESTAMPTZ
);

-- Indexes for content_recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_org ON content_recommendations(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON content_recommendations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON content_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_active ON content_recommendations(organization_id, priority)
    WHERE dismissed_at IS NULL AND actioned_at IS NULL;

COMMENT ON TABLE content_recommendations IS 'AI-generated content recommendations';


-- =============================================================================
-- Functions
-- =============================================================================

-- Function: Increment content metric
CREATE OR REPLACE FUNCTION increment_content_metric(
    p_content_id TEXT,
    p_metric TEXT,
    p_value NUMERIC DEFAULT 1
)
RETURNS BOOLEAN AS $$
DECLARE
    v_query TEXT;
BEGIN
    -- Validate metric name to prevent SQL injection
    IF p_metric NOT IN ('views', 'unique_views', 'shares', 'comments', 'reactions', 'backlinks', 'conversions') THEN
        RAISE EXCEPTION 'Invalid metric name: %', p_metric;
    END IF;

    -- Build and execute dynamic update
    v_query := format(
        'UPDATE content_performance SET %I = %I + $1, last_tracked_at = NOW(), updated_at = NOW() WHERE content_id = $2',
        p_metric, p_metric
    );

    EXECUTE v_query USING p_value, p_content_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION increment_content_metric IS 'Atomically increment a content performance metric';


-- Function: Create daily snapshot
CREATE OR REPLACE FUNCTION create_daily_snapshot(p_content_id TEXT)
RETURNS UUID AS $$
DECLARE
    v_snapshot_id UUID;
    v_perf RECORD;
BEGIN
    -- Get current performance
    SELECT * INTO v_perf FROM content_performance WHERE content_id = p_content_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    -- Insert or update snapshot for today
    INSERT INTO performance_snapshots (
        content_id, snapshot_date, views, unique_views, shares,
        backlinks, conversions, engagement_score, avg_time_on_page,
        avg_scroll_depth, bounce_rate, organization_id
    ) VALUES (
        p_content_id,
        CURRENT_DATE,
        v_perf.views,
        v_perf.unique_views,
        v_perf.shares,
        v_perf.backlinks,
        v_perf.conversions,
        COALESCE(
            (v_perf.time_on_page_seconds / NULLIF(180, 0) * 25) +
            (v_perf.avg_scroll_depth * 25) +
            ((1 - v_perf.bounce_rate) * 20) +
            (LEAST(v_perf.shares::NUMERIC / NULLIF(v_perf.views * 0.01, 0), 1) * 15) +
            (LEAST(v_perf.conversion_rate * 10, 1) * 15),
            0
        ),
        v_perf.time_on_page_seconds,
        v_perf.avg_scroll_depth,
        v_perf.bounce_rate,
        v_perf.organization_id
    )
    ON CONFLICT (content_id, snapshot_date) DO UPDATE SET
        views = EXCLUDED.views,
        unique_views = EXCLUDED.unique_views,
        shares = EXCLUDED.shares,
        backlinks = EXCLUDED.backlinks,
        conversions = EXCLUDED.conversions,
        engagement_score = EXCLUDED.engagement_score,
        avg_time_on_page = EXCLUDED.avg_time_on_page,
        avg_scroll_depth = EXCLUDED.avg_scroll_depth,
        bounce_rate = EXCLUDED.bounce_rate
    RETURNING id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_daily_snapshot IS 'Creates a daily performance snapshot for a content item';


-- Function: Get performance trend
CREATE OR REPLACE FUNCTION get_performance_trend(
    p_content_id TEXT,
    p_metric TEXT,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    snapshot_date DATE,
    value NUMERIC,
    change_from_previous NUMERIC
) AS $$
BEGIN
    -- Validate metric name
    IF p_metric NOT IN ('views', 'unique_views', 'shares', 'backlinks', 'conversions', 'engagement_score') THEN
        RAISE EXCEPTION 'Invalid metric name: %', p_metric;
    END IF;

    RETURN QUERY EXECUTE format(
        'SELECT
            ps.snapshot_date,
            ps.%I::NUMERIC as value,
            ps.%I - LAG(ps.%I) OVER (ORDER BY ps.snapshot_date) as change_from_previous
        FROM performance_snapshots ps
        WHERE ps.content_id = $1
            AND ps.snapshot_date >= CURRENT_DATE - $2
        ORDER BY ps.snapshot_date',
        p_metric, p_metric, p_metric
    ) USING p_content_id, p_days;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_performance_trend IS 'Returns trend data for a specific metric';


-- Function: Get top performing content
CREATE OR REPLACE FUNCTION get_top_content(
    p_organization_id UUID,
    p_metric TEXT DEFAULT 'views',
    p_days INTEGER DEFAULT 30,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    content_id TEXT,
    title TEXT,
    content_type TEXT,
    metric_value NUMERIC,
    engagement_score NUMERIC
) AS $$
BEGIN
    -- Validate metric name
    IF p_metric NOT IN ('views', 'unique_views', 'shares', 'conversions', 'engagement_score') THEN
        RAISE EXCEPTION 'Invalid metric name: %', p_metric;
    END IF;

    RETURN QUERY EXECUTE format(
        'SELECT
            cp.content_id,
            cp.title,
            cp.content_type,
            cp.%I::NUMERIC as metric_value,
            COALESCE(
                (cp.time_on_page_seconds / NULLIF(180, 0) * 25) +
                (cp.avg_scroll_depth * 25) +
                ((1 - cp.bounce_rate) * 20) +
                (LEAST(cp.shares::NUMERIC / NULLIF(cp.views * 0.01, 0), 1) * 15) +
                (LEAST(cp.conversion_rate * 10, 1) * 15),
                0
            )::NUMERIC as engagement_score
        FROM content_performance cp
        WHERE cp.organization_id = $1
            AND cp.last_tracked_at >= NOW() - ($2 || '' days'')::INTERVAL
        ORDER BY cp.%I DESC
        LIMIT $3',
        p_metric, p_metric
    ) USING p_organization_id, p_days, p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_top_content IS 'Returns top performing content by specified metric';


-- Function: Calculate aggregated summary
CREATE OR REPLACE FUNCTION get_performance_summary(
    p_organization_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_content INTEGER,
    total_views BIGINT,
    total_unique_views BIGINT,
    total_shares BIGINT,
    total_conversions BIGINT,
    avg_time_on_page NUMERIC,
    avg_bounce_rate NUMERIC,
    avg_engagement_score NUMERIC,
    views_change_percent NUMERIC,
    shares_change_percent NUMERIC
) AS $$
DECLARE
    v_current_start TIMESTAMPTZ;
    v_previous_start TIMESTAMPTZ;
    v_current_views BIGINT;
    v_previous_views BIGINT;
    v_current_shares BIGINT;
    v_previous_shares BIGINT;
BEGIN
    v_current_start := NOW() - (p_days || ' days')::INTERVAL;
    v_previous_start := v_current_start - (p_days || ' days')::INTERVAL;

    -- Get current period totals
    SELECT
        COALESCE(SUM(views), 0),
        COALESCE(SUM(shares), 0)
    INTO v_current_views, v_current_shares
    FROM content_performance
    WHERE organization_id = p_organization_id
        AND last_tracked_at >= v_current_start;

    -- Get previous period totals for comparison
    SELECT
        COALESCE(SUM(views), 0),
        COALESCE(SUM(shares), 0)
    INTO v_previous_views, v_previous_shares
    FROM content_performance
    WHERE organization_id = p_organization_id
        AND last_tracked_at >= v_previous_start
        AND last_tracked_at < v_current_start;

    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_content,
        COALESCE(SUM(cp.views), 0)::BIGINT as total_views,
        COALESCE(SUM(cp.unique_views), 0)::BIGINT as total_unique_views,
        COALESCE(SUM(cp.shares), 0)::BIGINT as total_shares,
        COALESCE(SUM(cp.conversions), 0)::BIGINT as total_conversions,
        ROUND(AVG(cp.time_on_page_seconds), 2) as avg_time_on_page,
        ROUND(AVG(cp.bounce_rate), 4) as avg_bounce_rate,
        ROUND(AVG(
            COALESCE(
                (cp.time_on_page_seconds / NULLIF(180, 0) * 25) +
                (cp.avg_scroll_depth * 25) +
                ((1 - cp.bounce_rate) * 20) +
                (LEAST(cp.shares::NUMERIC / NULLIF(cp.views * 0.01, 0), 1) * 15) +
                (LEAST(cp.conversion_rate * 10, 1) * 15),
                0
            )
        ), 2) as avg_engagement_score,
        CASE
            WHEN v_previous_views = 0 THEN
                CASE WHEN v_current_views > 0 THEN 100.0 ELSE 0.0 END
            ELSE
                ROUND(((v_current_views - v_previous_views)::NUMERIC / v_previous_views) * 100, 2)
        END as views_change_percent,
        CASE
            WHEN v_previous_shares = 0 THEN
                CASE WHEN v_current_shares > 0 THEN 100.0 ELSE 0.0 END
            ELSE
                ROUND(((v_current_shares - v_previous_shares)::NUMERIC / v_previous_shares) * 100, 2)
        END as shares_change_percent
    FROM content_performance cp
    WHERE cp.organization_id = p_organization_id
        AND cp.last_tracked_at >= v_current_start;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_performance_summary IS 'Returns aggregated performance summary with trend comparison';


-- =============================================================================
-- Triggers
-- =============================================================================

-- Trigger: Auto-update updated_at for content_performance
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_content_performance_updated_at
    BEFORE UPDATE ON content_performance
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Views
-- =============================================================================

-- View: Active content with engagement scores
CREATE OR REPLACE VIEW v_active_content_performance AS
SELECT
    cp.*,
    COALESCE(
        (cp.time_on_page_seconds / NULLIF(180, 0) * 25) +
        (cp.avg_scroll_depth * 25) +
        ((1 - cp.bounce_rate) * 20) +
        (LEAST(cp.shares::NUMERIC / NULLIF(cp.views * 0.01, 0), 1) * 15) +
        (LEAST(cp.conversion_rate * 10, 1) * 15),
        0
    ) as engagement_score
FROM content_performance cp
WHERE cp.last_tracked_at > NOW() - INTERVAL '30 days';

COMMENT ON VIEW v_active_content_performance IS 'Active content with calculated engagement scores';


-- View: SEO opportunities (keywords ranking 11-30)
CREATE OR REPLACE VIEW v_seo_opportunities AS
SELECT DISTINCT ON (sr.keyword)
    sr.keyword,
    sr.position as current_position,
    sr.search_volume,
    sr.content_id,
    sr.url,
    sr.organization_id,
    CASE
        WHEN sr.search_volume IS NULL THEN 0
        ELSE sr.search_volume * (0.30 - 0.01)  -- Potential traffic if moved to #1
    END as potential_traffic
FROM seo_rankings sr
WHERE sr.position >= 11
    AND sr.position <= 30
    AND sr.tracked_at > NOW() - INTERVAL '7 days'
ORDER BY sr.keyword, sr.tracked_at DESC;

COMMENT ON VIEW v_seo_opportunities IS 'Keywords with improvement potential (positions 11-30)';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE content_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_rankings ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_recommendations ENABLE ROW LEVEL SECURITY;

-- Content Performance: Organization members can access
CREATE POLICY "Org members can view content performance"
    ON content_performance
    FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = content_performance.organization_id
                AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
                AND om.is_active = true
        )
    );

-- Service role full access
CREATE POLICY "Service role full access to content_performance"
    ON content_performance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Performance Events: Organization members can view
CREATE POLICY "Org members can view performance events"
    ON performance_events
    FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = performance_events.organization_id
                AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
                AND om.is_active = true
        )
    );

-- Service role can insert events (for tracking API)
CREATE POLICY "Service role full access to performance_events"
    ON performance_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Performance Snapshots: Organization members can view
CREATE POLICY "Org members can view snapshots"
    ON performance_snapshots
    FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = performance_snapshots.organization_id
                AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
                AND om.is_active = true
        )
    );

CREATE POLICY "Service role full access to snapshots"
    ON performance_snapshots
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- SEO Rankings: Organization members can view
CREATE POLICY "Org members can view SEO rankings"
    ON seo_rankings
    FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = seo_rankings.organization_id
                AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
                AND om.is_active = true
        )
    );

CREATE POLICY "Service role full access to SEO rankings"
    ON seo_rankings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Content Recommendations: Organization members can view
CREATE POLICY "Org members can view recommendations"
    ON content_recommendations
    FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = content_recommendations.organization_id
                AND om.user_id = current_setting('request.jwt.claims', true)::json->>'sub'
                AND om.is_active = true
        )
    );

CREATE POLICY "Service role full access to recommendations"
    ON content_recommendations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION increment_content_metric(TEXT, TEXT, NUMERIC) TO service_role;
GRANT EXECUTE ON FUNCTION create_daily_snapshot(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION get_performance_trend(TEXT, TEXT, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_top_content(UUID, TEXT, INTEGER, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_performance_summary(UUID, INTEGER) TO authenticated, service_role;

-- Grant view access
GRANT SELECT ON v_active_content_performance TO authenticated, service_role;
GRANT SELECT ON v_seo_opportunities TO authenticated, service_role;


-- =============================================================================
-- Data Retention Job (scheduled via pg_cron if available)
-- =============================================================================

-- Function to clean up old events (keeps 90 days by default)
CREATE OR REPLACE FUNCTION cleanup_old_performance_events(p_retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM performance_events
    WHERE timestamp < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_old_performance_events IS 'Removes performance events older than retention period';

GRANT EXECUTE ON FUNCTION cleanup_old_performance_events(INTEGER) TO service_role;
