-- Migration: Create tool_usage table and analytics functions
-- Description: Tracks tool usage statistics for analytics dashboard

-- Create the tool_usage table
CREATE TABLE IF NOT EXISTS tool_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id TEXT NOT NULL UNIQUE,
    count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for tool lookups
CREATE INDEX idx_tool_usage_tool_id ON tool_usage(tool_id);
CREATE INDEX idx_tool_usage_count ON tool_usage(count DESC);

-- Enable Row Level Security
ALTER TABLE tool_usage ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read tool usage stats (public analytics)
CREATE POLICY "Anyone can read tool_usage"
    ON tool_usage
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- Policy: Service role can write
CREATE POLICY "Service role can write tool_usage"
    ON tool_usage
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Function: Increment tool usage count (atomic upsert)
CREATE OR REPLACE FUNCTION increment_tool_usage(p_tool_id TEXT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO tool_usage (tool_id, count, last_used_at)
    VALUES (p_tool_id, 1, NOW())
    ON CONFLICT (tool_id)
    DO UPDATE SET
        count = tool_usage.count + 1,
        last_used_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get tool usage stats (sorted by popularity)
CREATE OR REPLACE FUNCTION get_tool_stats()
RETURNS TABLE (
    tool_id TEXT,
    count INTEGER,
    last_used_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        tu.tool_id,
        tu.count,
        tu.last_used_at
    FROM tool_usage tu
    ORDER BY tu.count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION increment_tool_usage(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_tool_stats() TO anon, authenticated, service_role;

COMMENT ON TABLE tool_usage IS 'Tracks tool usage statistics for analytics';
COMMENT ON FUNCTION increment_tool_usage IS 'Atomically increments the usage count for a tool';
COMMENT ON FUNCTION get_tool_stats IS 'Returns tool usage statistics sorted by popularity';
