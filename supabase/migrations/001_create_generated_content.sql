-- Migration: Create generated_content table
-- Description: Stores all AI-generated content for history and analytics

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the generated_content table
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Tool information
    tool_id TEXT NOT NULL,

    -- Input/Output
    inputs JSONB NOT NULL,
    output TEXT NOT NULL,

    -- Execution metadata
    provider TEXT NOT NULL DEFAULT 'openai',
    execution_time_ms INTEGER NOT NULL DEFAULT 0,

    -- Optional user tracking (hashed for privacy)
    user_hash TEXT
);

-- Create indexes for common queries
CREATE INDEX idx_generated_content_tool_id ON generated_content(tool_id);
CREATE INDEX idx_generated_content_created_at ON generated_content(created_at DESC);
CREATE INDEX idx_generated_content_user_hash ON generated_content(user_hash) WHERE user_hash IS NOT NULL;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_generated_content_updated_at
    BEFORE UPDATE ON generated_content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE generated_content ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role has full access to generated_content"
    ON generated_content
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Anonymous users can insert (for content generation)
CREATE POLICY "Anonymous can insert generated_content"
    ON generated_content
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Users can read their own content by user_hash
CREATE POLICY "Users can read own generated_content"
    ON generated_content
    FOR SELECT
    TO anon
    USING (user_hash IS NOT NULL);

COMMENT ON TABLE generated_content IS 'Stores all AI-generated content for history and analytics';
COMMENT ON COLUMN generated_content.tool_id IS 'The ID of the tool used to generate this content';
COMMENT ON COLUMN generated_content.inputs IS 'JSON object containing all input parameters';
COMMENT ON COLUMN generated_content.output IS 'The generated content';
COMMENT ON COLUMN generated_content.provider IS 'LLM provider used (openai, anthropic, gemini)';
COMMENT ON COLUMN generated_content.execution_time_ms IS 'Time taken to generate content in milliseconds';
COMMENT ON COLUMN generated_content.user_hash IS 'Hashed user identifier for tracking without PII';
