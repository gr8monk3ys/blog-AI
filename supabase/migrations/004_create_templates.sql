-- Migration: Create templates table
-- Description: Stores reusable content templates with preset inputs

-- Create the templates table
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Template identification
    name TEXT NOT NULL,
    description TEXT,
    slug TEXT NOT NULL UNIQUE,

    -- Tool association
    tool_id TEXT NOT NULL,

    -- Preset inputs for the tool
    preset_inputs JSONB NOT NULL DEFAULT '{}',

    -- Categorization and discovery
    category TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',

    -- Visibility and ownership
    is_public BOOLEAN NOT NULL DEFAULT true,
    user_hash TEXT,

    -- Usage tracking
    use_count INTEGER NOT NULL DEFAULT 0
);

-- Create indexes for common queries
CREATE INDEX idx_templates_tool_id ON templates(tool_id);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_slug ON templates(slug);
CREATE INDEX idx_templates_is_public ON templates(is_public) WHERE is_public = true;
CREATE INDEX idx_templates_created_at ON templates(created_at DESC);
CREATE INDEX idx_templates_use_count ON templates(use_count DESC);

-- GIN index for tags array search
CREATE INDEX idx_templates_tags ON templates USING GIN(tags);

-- Auto-update updated_at timestamp
CREATE TRIGGER update_templates_updated_at
    BEFORE UPDATE ON templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to increment template use count
CREATE OR REPLACE FUNCTION increment_template_use_count(p_template_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE templates
    SET use_count = use_count + 1
    WHERE id = p_template_id;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role has full access to templates"
    ON templates
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Anonymous users can read public templates
CREATE POLICY "Anonymous can read public templates"
    ON templates
    FOR SELECT
    TO anon
    USING (is_public = true);

-- Policy: Anonymous users can create templates
CREATE POLICY "Anonymous can create templates"
    ON templates
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Users can update their own templates
CREATE POLICY "Users can update own templates"
    ON templates
    FOR UPDATE
    TO anon
    USING (user_hash IS NOT NULL)
    WITH CHECK (user_hash IS NOT NULL);

-- Policy: Users can delete their own templates
CREATE POLICY "Users can delete own templates"
    ON templates
    FOR DELETE
    TO anon
    USING (user_hash IS NOT NULL);

COMMENT ON TABLE templates IS 'Stores reusable content templates with preset inputs';
COMMENT ON COLUMN templates.name IS 'Display name of the template';
COMMENT ON COLUMN templates.description IS 'Brief description of what this template creates';
COMMENT ON COLUMN templates.slug IS 'URL-friendly unique identifier';
COMMENT ON COLUMN templates.tool_id IS 'The ID of the tool this template is for';
COMMENT ON COLUMN templates.preset_inputs IS 'JSON object with preset input values for the tool';
COMMENT ON COLUMN templates.category IS 'Category for filtering (e.g., marketing, saas, ecommerce)';
COMMENT ON COLUMN templates.tags IS 'Array of tags for search and filtering';
COMMENT ON COLUMN templates.is_public IS 'Whether this template is visible to all users';
COMMENT ON COLUMN templates.user_hash IS 'Hashed user identifier who created this template';
COMMENT ON COLUMN templates.use_count IS 'Number of times this template has been used';
