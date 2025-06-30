-- Migration: Create content feedback table
-- Description: Implements a user feedback and rating system for generated content
--
-- Tables:
--   content_feedback: Stores user ratings, quick-feedback tags, and optional text
--
-- Features:
--   - 1-5 star rating per submission
--   - Multiple quick-feedback tags stored as text[]
--   - Optional free-text feedback (max 1000 chars)
--   - Indexed on content_id for fast aggregation
--   - Allows anonymous feedback (user_id may be NULL)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Content Feedback Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS content_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User (nullable -- anonymous feedback is allowed)
    user_id TEXT,

    -- Reference to the generated content being rated
    content_id TEXT NOT NULL,

    -- Star rating
    rating INTEGER NOT NULL
        CHECK (rating >= 1 AND rating <= 5),

    -- Quick feedback tags
    tags TEXT[] NOT NULL DEFAULT '{}',

    -- Optional free-text feedback
    feedback_text TEXT
        CHECK (feedback_text IS NULL OR char_length(feedback_text) <= 1000),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Primary lookup: aggregate stats for a given piece of content
CREATE INDEX IF NOT EXISTS idx_content_feedback_content_id
    ON content_feedback(content_id, created_at DESC);

-- User-specific history
CREATE INDEX IF NOT EXISTS idx_content_feedback_user_id
    ON content_feedback(user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

-- Rating distribution queries
CREATE INDEX IF NOT EXISTS idx_content_feedback_rating
    ON content_feedback(content_id, rating);

-- Comments
COMMENT ON TABLE content_feedback IS 'User feedback and star ratings for generated content';
COMMENT ON COLUMN content_feedback.content_id IS 'Identifier of the generated content (conversation_id or history item id)';
COMMENT ON COLUMN content_feedback.tags IS 'Array of quick-feedback labels selected by the user';
COMMENT ON COLUMN content_feedback.feedback_text IS 'Optional free-text feedback, up to 1000 characters';


-- =============================================================================
-- Function: Get Feedback Stats For Content
-- =============================================================================

CREATE OR REPLACE FUNCTION get_content_feedback_stats(
    p_content_id TEXT
)
RETURNS TABLE (
    total_ratings BIGINT,
    average_rating NUMERIC(3, 1),
    rating_1 BIGINT,
    rating_2 BIGINT,
    rating_3 BIGINT,
    rating_4 BIGINT,
    rating_5 BIGINT,
    common_tags JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_ratings,
        COALESCE(ROUND(AVG(cf.rating)::NUMERIC, 1), 0) AS average_rating,
        COUNT(*) FILTER (WHERE cf.rating = 1)::BIGINT AS rating_1,
        COUNT(*) FILTER (WHERE cf.rating = 2)::BIGINT AS rating_2,
        COUNT(*) FILTER (WHERE cf.rating = 3)::BIGINT AS rating_3,
        COUNT(*) FILTER (WHERE cf.rating = 4)::BIGINT AS rating_4,
        COUNT(*) FILTER (WHERE cf.rating = 5)::BIGINT AS rating_5,
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object('tag', tag_data.tag, 'count', tag_data.cnt)
                    ORDER BY tag_data.cnt DESC
                )
                FROM (
                    SELECT tag, COUNT(*)::INT AS cnt
                    FROM content_feedback cf2, UNNEST(cf2.tags) AS tag
                    WHERE cf2.content_id = p_content_id
                    GROUP BY tag
                    ORDER BY cnt DESC
                ) tag_data
            ),
            '[]'::JSONB
        ) AS common_tags
    FROM content_feedback cf
    WHERE cf.content_id = p_content_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_content_feedback_stats IS 'Returns aggregated feedback statistics for a piece of content';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

ALTER TABLE content_feedback ENABLE ROW LEVEL SECURITY;

-- Anyone can insert feedback (anonymous allowed)
CREATE POLICY "Anyone can insert feedback"
    ON content_feedback
    FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

-- Authenticated users can view their own feedback
CREATE POLICY "Users can view own feedback"
    ON content_feedback
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Service role has full access
CREATE POLICY "Service role can manage all feedback"
    ON content_feedback
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

GRANT EXECUTE ON FUNCTION get_content_feedback_stats(TEXT) TO anon, authenticated, service_role;


-- =============================================================================
-- Trigger: Auto-update updated_at
-- =============================================================================

CREATE TRIGGER update_content_feedback_updated_at
    BEFORE UPDATE ON content_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
