-- Migration: Create social media scheduling tables
-- Description: Stores social accounts, scheduled posts, campaigns, and analytics
--
-- Tables:
--   social_accounts: Connected social media accounts
--   scheduled_posts: Post queue for scheduled publishing
--   social_campaigns: Multi-platform campaigns
--   post_analytics: Per-post performance metrics

-- =============================================================================
-- Social Accounts Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'linkedin', 'facebook', 'instagram')),
    platform_user_id TEXT NOT NULL,
    platform_username TEXT NOT NULL,
    display_name TEXT,
    profile_image_url TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique platform account per user
    CONSTRAINT unique_platform_account UNIQUE (user_id, platform, platform_user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);
CREATE INDEX IF NOT EXISTS idx_social_accounts_active ON social_accounts(user_id, is_active) WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE social_accounts IS 'Connected social media accounts for users';
COMMENT ON COLUMN social_accounts.platform IS 'Social platform: twitter, linkedin, facebook, instagram';
COMMENT ON COLUMN social_accounts.platform_user_id IS 'User ID on the social platform';
COMMENT ON COLUMN social_accounts.access_token IS 'OAuth access token (encrypted at rest)';
COMMENT ON COLUMN social_accounts.refresh_token IS 'OAuth refresh token for token renewal';


-- =============================================================================
-- Scheduled Posts Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES social_accounts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'linkedin', 'facebook', 'instagram')),

    -- Content
    content_text TEXT NOT NULL,
    content_media JSONB DEFAULT '[]',
    content_link_url TEXT,
    content_link_title TEXT,
    content_link_description TEXT,
    content_hashtags TEXT[] DEFAULT '{}',
    content_mentions TEXT[] DEFAULT '{}',

    -- Scheduling
    scheduled_at TIMESTAMPTZ NOT NULL,
    published_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('draft', 'scheduled', 'publishing', 'published', 'failed', 'cancelled')),

    -- Retry handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Platform response
    platform_post_id TEXT,
    platform_post_url TEXT,

    -- Relations
    campaign_id UUID,
    source_content_id TEXT,

    -- Recurrence
    recurrence TEXT DEFAULT 'none' CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly')),
    recurrence_end_date TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user_id ON scheduled_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_account_id ON scheduled_posts(account_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_campaign_id ON scheduled_posts(campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_scheduled_at ON scheduled_posts(scheduled_at);

-- Index for finding due posts (critical for the worker)
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_due ON scheduled_posts(scheduled_at, status)
    WHERE status = 'scheduled';

-- Composite index for user's scheduled posts
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user_status ON scheduled_posts(user_id, status, scheduled_at DESC);

-- Comments
COMMENT ON TABLE scheduled_posts IS 'Queue of posts scheduled for future publishing';
COMMENT ON COLUMN scheduled_posts.content_text IS 'Post text content';
COMMENT ON COLUMN scheduled_posts.content_media IS 'JSON array of media attachments';
COMMENT ON COLUMN scheduled_posts.status IS 'Post status: draft, scheduled, publishing, published, failed, cancelled';
COMMENT ON COLUMN scheduled_posts.recurrence IS 'Recurrence pattern: none, daily, weekly, monthly';


-- =============================================================================
-- Social Campaigns Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS social_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,

    -- Base content
    content_text TEXT NOT NULL,
    content_media JSONB DEFAULT '[]',
    content_link_url TEXT,
    content_hashtags TEXT[] DEFAULT '{}',

    -- Platform configurations
    platforms JSONB NOT NULL DEFAULT '[]',

    -- Scheduling
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),

    -- Recurrence
    recurrence TEXT DEFAULT 'none' CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly')),
    recurrence_end_date TIMESTAMPTZ,

    -- Relations
    post_ids UUID[] DEFAULT '{}',
    source_content_id TEXT,

    -- Organization
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_social_campaigns_user_id ON social_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_social_campaigns_status ON social_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_social_campaigns_scheduled_at ON social_campaigns(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_social_campaigns_tags ON social_campaigns USING GIN(tags);

-- Comments
COMMENT ON TABLE social_campaigns IS 'Multi-platform social media campaigns';
COMMENT ON COLUMN social_campaigns.platforms IS 'JSON array of platform configurations with account_id and offset';
COMMENT ON COLUMN social_campaigns.post_ids IS 'Array of scheduled_posts IDs created for this campaign';
COMMENT ON COLUMN social_campaigns.status IS 'Campaign status: draft, active, paused, completed, cancelled';


-- =============================================================================
-- Post Analytics Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS post_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES scheduled_posts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    platform_post_id TEXT NOT NULL,

    -- Engagement metrics
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    engagements INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    link_clicks INTEGER DEFAULT 0,
    profile_visits INTEGER DEFAULT 0,

    -- Video metrics
    video_views INTEGER DEFAULT 0,
    video_watch_time_seconds INTEGER DEFAULT 0,

    -- Calculated metrics
    engagement_rate DECIMAL(5,2) DEFAULT 0,

    -- Raw data from platform
    raw_data JSONB DEFAULT '{}',

    -- Timestamps
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One analytics record per post
    CONSTRAINT unique_post_analytics UNIQUE (post_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_post_analytics_post_id ON post_analytics(post_id);
CREATE INDEX IF NOT EXISTS idx_post_analytics_platform ON post_analytics(platform);
CREATE INDEX IF NOT EXISTS idx_post_analytics_fetched_at ON post_analytics(fetched_at);

-- Comments
COMMENT ON TABLE post_analytics IS 'Performance metrics for published posts';
COMMENT ON COLUMN post_analytics.engagement_rate IS 'Calculated engagement rate percentage';
COMMENT ON COLUMN post_analytics.raw_data IS 'Raw analytics response from platform API';


-- =============================================================================
-- OAuth State Table (for OAuth flow tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS social_oauth_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    state_token TEXT NOT NULL UNIQUE,
    redirect_uri TEXT NOT NULL,
    pkce_verifier TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for state token lookup
CREATE INDEX IF NOT EXISTS idx_social_oauth_state_token ON social_oauth_state(state_token);

-- Auto-cleanup expired states
CREATE INDEX IF NOT EXISTS idx_social_oauth_state_expires ON social_oauth_state(expires_at);

-- Comments
COMMENT ON TABLE social_oauth_state IS 'Temporary storage for OAuth flow state';
COMMENT ON COLUMN social_oauth_state.state_token IS 'CSRF protection state parameter';
COMMENT ON COLUMN social_oauth_state.pkce_verifier IS 'PKCE code verifier for OAuth 2.0 PKCE flow';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_oauth_state ENABLE ROW LEVEL SECURITY;

-- Social Accounts: Users can manage their own accounts
CREATE POLICY "Users can view own social accounts"
    ON social_accounts
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can insert own social accounts"
    ON social_accounts
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can update own social accounts"
    ON social_accounts
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can delete own social accounts"
    ON social_accounts
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage all social accounts"
    ON social_accounts
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Scheduled Posts: Users can manage their own posts
CREATE POLICY "Users can view own scheduled posts"
    ON scheduled_posts
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can insert own scheduled posts"
    ON scheduled_posts
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can update own scheduled posts"
    ON scheduled_posts
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can delete own scheduled posts"
    ON scheduled_posts
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage all scheduled posts"
    ON scheduled_posts
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Social Campaigns: Users can manage their own campaigns
CREATE POLICY "Users can view own campaigns"
    ON social_campaigns
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can insert own campaigns"
    ON social_campaigns
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can update own campaigns"
    ON social_campaigns
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can delete own campaigns"
    ON social_campaigns
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage all campaigns"
    ON social_campaigns
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Post Analytics: Viewable by post owner
CREATE POLICY "Users can view analytics for own posts"
    ON post_analytics
    FOR SELECT
    TO authenticated
    USING (
        post_id IN (
            SELECT id FROM scheduled_posts
            WHERE user_id = auth.uid()::TEXT
            OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
    );

CREATE POLICY "Service role can manage all analytics"
    ON post_analytics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- OAuth State: Users can manage their own state
CREATE POLICY "Users can view own oauth state"
    ON social_oauth_state
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Users can insert own oauth state"
    ON social_oauth_state
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid()::TEXT OR user_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Service role can manage all oauth state"
    ON social_oauth_state
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Triggers for updated_at
-- =============================================================================

CREATE TRIGGER update_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_posts_updated_at
    BEFORE UPDATE ON scheduled_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_campaigns_updated_at
    BEFORE UPDATE ON social_campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Function: Get Due Posts for Publishing
-- =============================================================================

CREATE OR REPLACE FUNCTION get_due_posts(p_limit INTEGER DEFAULT 100)
RETURNS TABLE (
    post_id UUID,
    user_id TEXT,
    account_id UUID,
    platform TEXT,
    content_text TEXT,
    content_media JSONB,
    scheduled_at TIMESTAMPTZ,
    retry_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sp.id as post_id,
        sp.user_id,
        sp.account_id,
        sp.platform,
        sp.content_text,
        sp.content_media,
        sp.scheduled_at,
        sp.retry_count
    FROM scheduled_posts sp
    WHERE sp.status = 'scheduled'
      AND sp.scheduled_at <= NOW()
    ORDER BY sp.scheduled_at ASC
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED;  -- Prevents race conditions in worker
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_due_posts IS 'Get posts that are due for publishing (for background worker)';


-- =============================================================================
-- Function: Mark Post as Publishing
-- =============================================================================

CREATE OR REPLACE FUNCTION mark_post_publishing(p_post_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated INTEGER;
BEGIN
    UPDATE scheduled_posts
    SET status = 'publishing',
        updated_at = NOW()
    WHERE id = p_post_id
      AND status = 'scheduled';

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION mark_post_publishing IS 'Atomically mark a post as publishing to prevent duplicate processing';


-- =============================================================================
-- Function: Complete Post Publishing
-- =============================================================================

CREATE OR REPLACE FUNCTION complete_post_publishing(
    p_post_id UUID,
    p_platform_post_id TEXT,
    p_platform_post_url TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE scheduled_posts
    SET status = 'published',
        published_at = NOW(),
        platform_post_id = p_platform_post_id,
        platform_post_url = p_platform_post_url,
        updated_at = NOW()
    WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION complete_post_publishing IS 'Mark a post as successfully published';


-- =============================================================================
-- Function: Fail Post Publishing
-- =============================================================================

CREATE OR REPLACE FUNCTION fail_post_publishing(
    p_post_id UUID,
    p_error_message TEXT,
    p_should_retry BOOLEAN DEFAULT TRUE
)
RETURNS VOID AS $$
DECLARE
    v_retry_count INTEGER;
    v_max_retries INTEGER;
BEGIN
    SELECT retry_count, max_retries INTO v_retry_count, v_max_retries
    FROM scheduled_posts WHERE id = p_post_id;

    IF p_should_retry AND v_retry_count < v_max_retries THEN
        -- Mark for retry
        UPDATE scheduled_posts
        SET status = 'scheduled',
            retry_count = v_retry_count + 1,
            error_message = p_error_message,
            updated_at = NOW()
        WHERE id = p_post_id;
    ELSE
        -- Mark as failed
        UPDATE scheduled_posts
        SET status = 'failed',
            error_message = p_error_message,
            updated_at = NOW()
        WHERE id = p_post_id;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION fail_post_publishing IS 'Handle failed post publishing with retry logic';


-- =============================================================================
-- Function: Cleanup Expired OAuth State
-- =============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_oauth_state()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM social_oauth_state
    WHERE expires_at < NOW();

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_expired_oauth_state IS 'Remove expired OAuth state records';


-- =============================================================================
-- Function: Get Campaign Analytics Summary
-- =============================================================================

CREATE OR REPLACE FUNCTION get_campaign_analytics(p_campaign_id UUID)
RETURNS TABLE (
    total_posts INTEGER,
    published_posts INTEGER,
    failed_posts INTEGER,
    total_impressions BIGINT,
    total_engagements BIGINT,
    total_clicks BIGINT,
    avg_engagement_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(sp.id)::INTEGER as total_posts,
        COUNT(sp.id) FILTER (WHERE sp.status = 'published')::INTEGER as published_posts,
        COUNT(sp.id) FILTER (WHERE sp.status = 'failed')::INTEGER as failed_posts,
        COALESCE(SUM(pa.impressions), 0)::BIGINT as total_impressions,
        COALESCE(SUM(pa.engagements), 0)::BIGINT as total_engagements,
        COALESCE(SUM(pa.clicks), 0)::BIGINT as total_clicks,
        COALESCE(AVG(pa.engagement_rate), 0)::DECIMAL as avg_engagement_rate
    FROM scheduled_posts sp
    LEFT JOIN post_analytics pa ON pa.post_id = sp.id
    WHERE sp.campaign_id = p_campaign_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_campaign_analytics IS 'Get aggregated analytics for a campaign';


-- =============================================================================
-- Grant Permissions
-- =============================================================================

GRANT EXECUTE ON FUNCTION get_due_posts(INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION mark_post_publishing(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION complete_post_publishing(UUID, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION fail_post_publishing(UUID, TEXT, BOOLEAN) TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_expired_oauth_state() TO service_role;
GRANT EXECUTE ON FUNCTION get_campaign_analytics(UUID) TO authenticated, service_role;
