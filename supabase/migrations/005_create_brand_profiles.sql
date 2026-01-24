-- Migration: Create brand_profiles table
-- Description: Stores brand voice profiles for consistent content generation

-- Create the brand_profiles table
CREATE TABLE IF NOT EXISTS brand_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Profile identification
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,

    -- Brand voice characteristics
    tone_keywords TEXT[] NOT NULL DEFAULT '{}',
    writing_style TEXT NOT NULL DEFAULT 'balanced',

    -- Example content for AI context
    example_content TEXT,

    -- Industry and audience targeting
    industry TEXT,
    target_audience TEXT,

    -- Words/phrases to use or avoid
    preferred_words TEXT[] DEFAULT '{}',
    avoid_words TEXT[] DEFAULT '{}',

    -- Additional brand guidelines
    brand_values TEXT[] DEFAULT '{}',
    content_themes TEXT[] DEFAULT '{}',

    -- Ownership
    user_hash TEXT,

    -- Active status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_default BOOLEAN NOT NULL DEFAULT false
);

-- Create indexes for common queries
CREATE INDEX idx_brand_profiles_slug ON brand_profiles(slug);
CREATE INDEX idx_brand_profiles_user_hash ON brand_profiles(user_hash) WHERE user_hash IS NOT NULL;
CREATE INDEX idx_brand_profiles_is_active ON brand_profiles(is_active) WHERE is_active = true;
CREATE INDEX idx_brand_profiles_is_default ON brand_profiles(is_default) WHERE is_default = true;
CREATE INDEX idx_brand_profiles_industry ON brand_profiles(industry);
CREATE INDEX idx_brand_profiles_created_at ON brand_profiles(created_at DESC);

-- GIN indexes for array searches
CREATE INDEX idx_brand_profiles_tone_keywords ON brand_profiles USING GIN(tone_keywords);
CREATE INDEX idx_brand_profiles_brand_values ON brand_profiles USING GIN(brand_values);

-- Auto-update updated_at timestamp
CREATE TRIGGER update_brand_profiles_updated_at
    BEFORE UPDATE ON brand_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to set a profile as default (and unset others for same user)
CREATE OR REPLACE FUNCTION set_default_brand_profile(p_profile_id UUID, p_user_hash TEXT)
RETURNS void AS $$
BEGIN
    -- Unset all other defaults for this user
    UPDATE brand_profiles
    SET is_default = false
    WHERE user_hash = p_user_hash AND id != p_profile_id;

    -- Set the new default
    UPDATE brand_profiles
    SET is_default = true
    WHERE id = p_profile_id;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security
ALTER TABLE brand_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role has full access to brand_profiles"
    ON brand_profiles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Anonymous users can read their own profiles
CREATE POLICY "Anonymous can read own brand_profiles"
    ON brand_profiles
    FOR SELECT
    TO anon
    USING (user_hash IS NOT NULL);

-- Policy: Anonymous users can create profiles
CREATE POLICY "Anonymous can create brand_profiles"
    ON brand_profiles
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Anonymous users can update their own profiles
CREATE POLICY "Anonymous can update own brand_profiles"
    ON brand_profiles
    FOR UPDATE
    TO anon
    USING (user_hash IS NOT NULL)
    WITH CHECK (user_hash IS NOT NULL);

-- Policy: Anonymous users can delete their own profiles
CREATE POLICY "Anonymous can delete own brand_profiles"
    ON brand_profiles
    FOR DELETE
    TO anon
    USING (user_hash IS NOT NULL);

COMMENT ON TABLE brand_profiles IS 'Stores brand voice profiles for consistent content generation';
COMMENT ON COLUMN brand_profiles.name IS 'Display name of the brand profile';
COMMENT ON COLUMN brand_profiles.slug IS 'URL-friendly unique identifier';
COMMENT ON COLUMN brand_profiles.tone_keywords IS 'Array of tone descriptors (e.g., professional, friendly, casual)';
COMMENT ON COLUMN brand_profiles.writing_style IS 'Overall writing style (e.g., formal, conversational, technical)';
COMMENT ON COLUMN brand_profiles.example_content IS 'Sample content that exemplifies the brand voice';
COMMENT ON COLUMN brand_profiles.industry IS 'Industry or niche for context (e.g., technology, healthcare)';
COMMENT ON COLUMN brand_profiles.target_audience IS 'Description of the target audience';
COMMENT ON COLUMN brand_profiles.preferred_words IS 'Words and phrases to prefer in content';
COMMENT ON COLUMN brand_profiles.avoid_words IS 'Words and phrases to avoid in content';
COMMENT ON COLUMN brand_profiles.brand_values IS 'Core brand values to incorporate';
COMMENT ON COLUMN brand_profiles.content_themes IS 'Common themes or topics for the brand';
COMMENT ON COLUMN brand_profiles.user_hash IS 'Hashed user identifier who owns this profile';
COMMENT ON COLUMN brand_profiles.is_active IS 'Whether this profile is currently active';
COMMENT ON COLUMN brand_profiles.is_default IS 'Whether this is the default profile for the user';
