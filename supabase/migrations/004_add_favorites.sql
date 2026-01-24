-- Migration: Add favorites functionality to generated_content
-- Description: Adds is_favorite column and toggle function for bookmarking content

-- Add is_favorite column to generated_content table
ALTER TABLE generated_content
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT false;

-- Create index for filtering favorites
CREATE INDEX IF NOT EXISTS idx_generated_content_is_favorite
    ON generated_content(is_favorite)
    WHERE is_favorite = true;

-- Create composite index for common query pattern (user's favorites)
CREATE INDEX IF NOT EXISTS idx_generated_content_user_favorites
    ON generated_content(user_hash, is_favorite, created_at DESC)
    WHERE user_hash IS NOT NULL AND is_favorite = true;

-- Function to toggle favorite status
-- Returns the new is_favorite value
CREATE OR REPLACE FUNCTION toggle_favorite(content_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    new_status BOOLEAN;
BEGIN
    UPDATE generated_content
    SET
        is_favorite = NOT is_favorite,
        updated_at = NOW()
    WHERE id = content_id
    RETURNING is_favorite INTO new_status;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Content with id % not found', content_id;
    END IF;

    RETURN new_status;
END;
$$;

-- Function to set favorite status explicitly
CREATE OR REPLACE FUNCTION set_favorite(content_id UUID, favorite_status BOOLEAN)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE generated_content
    SET
        is_favorite = favorite_status,
        updated_at = NOW()
    WHERE id = content_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Content with id % not found', content_id;
    END IF;

    RETURN favorite_status;
END;
$$;

-- Add tool_name column for better display (denormalized for performance)
ALTER TABLE generated_content
ADD COLUMN IF NOT EXISTS tool_name TEXT;

-- Add title column for better identification
ALTER TABLE generated_content
ADD COLUMN IF NOT EXISTS title TEXT;

-- Create index on title for search
CREATE INDEX IF NOT EXISTS idx_generated_content_title
    ON generated_content USING gin(to_tsvector('english', COALESCE(title, '')));

-- Grant execute permission on functions to anon users
GRANT EXECUTE ON FUNCTION toggle_favorite(UUID) TO anon;
GRANT EXECUTE ON FUNCTION set_favorite(UUID, BOOLEAN) TO anon;

COMMENT ON COLUMN generated_content.is_favorite IS 'Whether this content is bookmarked/favorited by the user';
COMMENT ON COLUMN generated_content.tool_name IS 'Display name of the tool used (denormalized for performance)';
COMMENT ON COLUMN generated_content.title IS 'Optional title for the generated content';
COMMENT ON FUNCTION toggle_favorite(UUID) IS 'Toggles the favorite status of generated content and returns the new status';
COMMENT ON FUNCTION set_favorite(UUID, BOOLEAN) IS 'Explicitly sets the favorite status of generated content';
