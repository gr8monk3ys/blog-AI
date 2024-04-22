-- Migration 009: Content performance analytics (Neon/asyncpg port)
--
-- Third module in the Supabase -> Neon migration (see docs/SCHEMA_AUDIT.md).
-- Backs src/analytics/* (performance_service, seo_tracker, recommendation_engine,
-- dashboard_service), which previously read/wrote these tables in a separate
-- Supabase project. Tables + indexes only (the services use no Postgres RPC):
-- the dead RLS policies, grants, and helper functions/views from
-- supabase/migrations/015 are intentionally omitted. organization_id reconciled
-- UUID -> TEXT to match the canonical organizations.id. Portable/idempotent;
-- feature gated behind ENABLE_PERFORMANCE_ANALYTICS (default off).

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
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,
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
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance_events
CREATE INDEX IF NOT EXISTS idx_perf_events_content_id ON performance_events(content_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_perf_events_type ON performance_events(event_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_perf_events_org_id ON performance_events(organization_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_perf_events_timestamp ON performance_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_perf_events_session ON performance_events(session_id) WHERE session_id IS NOT NULL;

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
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one snapshot per content per day
    CONSTRAINT unique_content_snapshot UNIQUE (content_id, snapshot_date)
);

-- Indexes for performance_snapshots
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_content ON performance_snapshots(content_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_perf_snapshots_date ON performance_snapshots(snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_perf_snapshots_org ON performance_snapshots(organization_id, snapshot_date DESC);

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
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,

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
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,
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
