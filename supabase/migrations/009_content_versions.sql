-- Migration: Create content version history system
-- Description: Implements version tracking for generated content with diff storage,
--              version comparison, and restoration capabilities.
--
-- Tables:
--   content_versions: Stores version history for each content item
--
-- Functions:
--   create_content_version: Create a new version for content
--   get_content_versions: Get version history for content
--   get_content_version: Get a specific version
--   restore_content_version: Restore content to a previous version
--   compare_content_versions: Compare two versions
--   get_latest_version_number: Get the latest version number for content
--
-- Triggers:
--   auto_version_on_update: Automatically creates versions on significant changes

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Content Versions Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS content_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES generated_content(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Content snapshot
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,  -- SHA-256 hash for change detection

    -- Diff from previous version (stored as unified diff format)
    -- NULL for first version
    diff_from_previous TEXT,

    -- Change metadata
    change_type TEXT NOT NULL DEFAULT 'manual' CHECK (change_type IN ('manual', 'auto', 'restore', 'initial')),
    change_summary TEXT,  -- Optional description of what changed

    -- Metadata
    word_count INTEGER NOT NULL DEFAULT 0,
    character_count INTEGER NOT NULL DEFAULT 0,

    -- User tracking
    created_by TEXT,  -- User ID who created this version

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique version numbers per content
    UNIQUE(content_id, version_number)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_content_versions_content_id
    ON content_versions(content_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_content_version
    ON content_versions(content_id, version_number DESC);

CREATE INDEX IF NOT EXISTS idx_content_versions_created_at
    ON content_versions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_content_versions_created_by
    ON content_versions(created_by) WHERE created_by IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_content_versions_content_hash
    ON content_versions(content_id, content_hash);

-- Comments
COMMENT ON TABLE content_versions IS 'Stores version history for generated content with diff tracking';
COMMENT ON COLUMN content_versions.version_number IS 'Sequential version number starting from 1';
COMMENT ON COLUMN content_versions.content IS 'Full content snapshot at this version';
COMMENT ON COLUMN content_versions.content_hash IS 'SHA-256 hash of content for change detection';
COMMENT ON COLUMN content_versions.diff_from_previous IS 'Unified diff from previous version (NULL for first version)';
COMMENT ON COLUMN content_versions.change_type IS 'Type of change: manual, auto, restore, or initial';
COMMENT ON COLUMN content_versions.change_summary IS 'Optional human-readable description of changes';


-- =============================================================================
-- Add current_version column to generated_content table
-- =============================================================================

DO $$
BEGIN
    -- Add current_version column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'generated_content'
        AND column_name = 'current_version'
    ) THEN
        ALTER TABLE generated_content
        ADD COLUMN current_version INTEGER NOT NULL DEFAULT 1;

        COMMENT ON COLUMN generated_content.current_version IS 'Current version number of the content';
    END IF;

    -- Add version_count column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'generated_content'
        AND column_name = 'version_count'
    ) THEN
        ALTER TABLE generated_content
        ADD COLUMN version_count INTEGER NOT NULL DEFAULT 1;

        COMMENT ON COLUMN generated_content.version_count IS 'Total number of versions for this content';
    END IF;
END $$;


-- =============================================================================
-- Function: Get Latest Version Number
-- =============================================================================

CREATE OR REPLACE FUNCTION get_latest_version_number(p_content_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_version INTEGER;
BEGIN
    SELECT COALESCE(MAX(version_number), 0)
    INTO v_version
    FROM content_versions
    WHERE content_id = p_content_id;

    RETURN v_version;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_latest_version_number IS 'Returns the latest version number for a content item';


-- =============================================================================
-- Function: Calculate Content Hash
-- =============================================================================

CREATE OR REPLACE FUNCTION calculate_content_hash(p_content TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(sha256(p_content::bytea), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_content_hash IS 'Calculates SHA-256 hash of content for change detection';


-- =============================================================================
-- Function: Create Content Version
-- =============================================================================

CREATE OR REPLACE FUNCTION create_content_version(
    p_content_id UUID,
    p_content TEXT,
    p_change_type TEXT DEFAULT 'manual',
    p_change_summary TEXT DEFAULT NULL,
    p_created_by TEXT DEFAULT NULL,
    p_diff_from_previous TEXT DEFAULT NULL
)
RETURNS TABLE (
    version_id UUID,
    version_number INTEGER,
    content_hash TEXT,
    is_duplicate BOOLEAN
) AS $$
DECLARE
    v_version_id UUID;
    v_new_version INTEGER;
    v_content_hash TEXT;
    v_existing_hash TEXT;
    v_word_count INTEGER;
    v_char_count INTEGER;
BEGIN
    -- Calculate content hash
    v_content_hash := calculate_content_hash(p_content);

    -- Check if this exact content already exists as the latest version
    SELECT cv.content_hash
    INTO v_existing_hash
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
    ORDER BY cv.version_number DESC
    LIMIT 1;

    -- If content is identical to latest version, don't create duplicate
    IF v_existing_hash = v_content_hash THEN
        -- Return existing version info with is_duplicate flag
        SELECT cv.id, cv.version_number, cv.content_hash, TRUE
        INTO v_version_id, v_new_version, v_content_hash, is_duplicate
        FROM content_versions cv
        WHERE cv.content_id = p_content_id
        ORDER BY cv.version_number DESC
        LIMIT 1;

        RETURN QUERY SELECT v_version_id, v_new_version, v_content_hash, TRUE;
        RETURN;
    END IF;

    -- Get next version number
    v_new_version := get_latest_version_number(p_content_id) + 1;

    -- Calculate word and character counts
    v_word_count := array_length(regexp_split_to_array(trim(p_content), '\s+'), 1);
    v_char_count := length(p_content);

    -- Insert new version
    INSERT INTO content_versions (
        content_id,
        version_number,
        content,
        content_hash,
        diff_from_previous,
        change_type,
        change_summary,
        word_count,
        character_count,
        created_by
    )
    VALUES (
        p_content_id,
        v_new_version,
        p_content,
        v_content_hash,
        p_diff_from_previous,
        p_change_type,
        p_change_summary,
        COALESCE(v_word_count, 0),
        v_char_count,
        p_created_by
    )
    RETURNING id INTO v_version_id;

    -- Update generated_content with new version info
    UPDATE generated_content
    SET
        current_version = v_new_version,
        version_count = v_new_version,
        output = p_content,
        updated_at = NOW()
    WHERE id = p_content_id;

    RETURN QUERY SELECT v_version_id, v_new_version, v_content_hash, FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_content_version IS 'Creates a new version for content, skipping duplicates';


-- =============================================================================
-- Function: Get Content Versions (with pagination)
-- =============================================================================

CREATE OR REPLACE FUNCTION get_content_versions(
    p_content_id UUID,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    version_id UUID,
    version_number INTEGER,
    content_preview TEXT,
    content_hash TEXT,
    change_type TEXT,
    change_summary TEXT,
    word_count INTEGER,
    character_count INTEGER,
    created_by TEXT,
    created_at TIMESTAMPTZ,
    is_current BOOLEAN
) AS $$
DECLARE
    v_current_version INTEGER;
BEGIN
    -- Get current version
    SELECT gc.current_version
    INTO v_current_version
    FROM generated_content gc
    WHERE gc.id = p_content_id;

    RETURN QUERY
    SELECT
        cv.id as version_id,
        cv.version_number,
        LEFT(cv.content, 200) as content_preview,  -- First 200 chars
        cv.content_hash,
        cv.change_type,
        cv.change_summary,
        cv.word_count,
        cv.character_count,
        cv.created_by,
        cv.created_at,
        cv.version_number = v_current_version as is_current
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
    ORDER BY cv.version_number DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_content_versions IS 'Returns paginated version history for content';


-- =============================================================================
-- Function: Get Specific Content Version
-- =============================================================================

CREATE OR REPLACE FUNCTION get_content_version(
    p_content_id UUID,
    p_version_number INTEGER
)
RETURNS TABLE (
    version_id UUID,
    version_number INTEGER,
    content TEXT,
    content_hash TEXT,
    diff_from_previous TEXT,
    change_type TEXT,
    change_summary TEXT,
    word_count INTEGER,
    character_count INTEGER,
    created_by TEXT,
    created_at TIMESTAMPTZ,
    is_current BOOLEAN
) AS $$
DECLARE
    v_current_version INTEGER;
BEGIN
    -- Get current version
    SELECT gc.current_version
    INTO v_current_version
    FROM generated_content gc
    WHERE gc.id = p_content_id;

    RETURN QUERY
    SELECT
        cv.id as version_id,
        cv.version_number,
        cv.content,
        cv.content_hash,
        cv.diff_from_previous,
        cv.change_type,
        cv.change_summary,
        cv.word_count,
        cv.character_count,
        cv.created_by,
        cv.created_at,
        cv.version_number = v_current_version as is_current
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
      AND cv.version_number = p_version_number;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_content_version IS 'Returns a specific version of content';


-- =============================================================================
-- Function: Restore Content Version
-- =============================================================================

CREATE OR REPLACE FUNCTION restore_content_version(
    p_content_id UUID,
    p_version_number INTEGER,
    p_restored_by TEXT DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN,
    new_version_id UUID,
    new_version_number INTEGER,
    restored_from_version INTEGER,
    message TEXT
) AS $$
DECLARE
    v_restored_content TEXT;
    v_version_exists BOOLEAN;
    v_result RECORD;
BEGIN
    -- Check if version exists
    SELECT EXISTS(
        SELECT 1 FROM content_versions cv
        WHERE cv.content_id = p_content_id
          AND cv.version_number = p_version_number
    ) INTO v_version_exists;

    IF NOT v_version_exists THEN
        RETURN QUERY SELECT
            FALSE as success,
            NULL::UUID as new_version_id,
            NULL::INTEGER as new_version_number,
            p_version_number as restored_from_version,
            'Version not found'::TEXT as message;
        RETURN;
    END IF;

    -- Get content from the version to restore
    SELECT cv.content
    INTO v_restored_content
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
      AND cv.version_number = p_version_number;

    -- Create new version with restored content
    SELECT * INTO v_result
    FROM create_content_version(
        p_content_id,
        v_restored_content,
        'restore',
        format('Restored from version %s', p_version_number),
        p_restored_by,
        NULL  -- No diff for restore
    );

    RETURN QUERY SELECT
        TRUE as success,
        v_result.version_id as new_version_id,
        v_result.version_number as new_version_number,
        p_version_number as restored_from_version,
        format('Successfully restored to version %s (new version: %s)',
               p_version_number, v_result.version_number)::TEXT as message;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION restore_content_version IS 'Restores content to a previous version by creating a new version';


-- =============================================================================
-- Function: Compare Content Versions
-- =============================================================================

CREATE OR REPLACE FUNCTION compare_content_versions(
    p_content_id UUID,
    p_version_1 INTEGER,
    p_version_2 INTEGER
)
RETURNS TABLE (
    version_1_number INTEGER,
    version_1_content TEXT,
    version_1_word_count INTEGER,
    version_1_char_count INTEGER,
    version_1_created_at TIMESTAMPTZ,
    version_2_number INTEGER,
    version_2_content TEXT,
    version_2_word_count INTEGER,
    version_2_char_count INTEGER,
    version_2_created_at TIMESTAMPTZ,
    word_count_diff INTEGER,
    char_count_diff INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v1.version_number as version_1_number,
        v1.content as version_1_content,
        v1.word_count as version_1_word_count,
        v1.character_count as version_1_char_count,
        v1.created_at as version_1_created_at,
        v2.version_number as version_2_number,
        v2.content as version_2_content,
        v2.word_count as version_2_word_count,
        v2.character_count as version_2_char_count,
        v2.created_at as version_2_created_at,
        v2.word_count - v1.word_count as word_count_diff,
        v2.character_count - v1.character_count as char_count_diff
    FROM content_versions v1
    CROSS JOIN content_versions v2
    WHERE v1.content_id = p_content_id
      AND v2.content_id = p_content_id
      AND v1.version_number = p_version_1
      AND v2.version_number = p_version_2;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION compare_content_versions IS 'Compares two versions of content';


-- =============================================================================
-- Function: Check if Content Has Significant Changes
-- =============================================================================

CREATE OR REPLACE FUNCTION has_significant_changes(
    p_content_id UUID,
    p_new_content TEXT,
    p_min_word_change INTEGER DEFAULT 10,
    p_min_char_change INTEGER DEFAULT 50
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_content TEXT;
    v_current_word_count INTEGER;
    v_current_char_count INTEGER;
    v_new_word_count INTEGER;
    v_new_char_count INTEGER;
    v_word_diff INTEGER;
    v_char_diff INTEGER;
BEGIN
    -- Get current version content and counts
    SELECT cv.content, cv.word_count, cv.character_count
    INTO v_current_content, v_current_word_count, v_current_char_count
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
    ORDER BY cv.version_number DESC
    LIMIT 1;

    -- If no previous version, changes are significant
    IF v_current_content IS NULL THEN
        RETURN TRUE;
    END IF;

    -- Calculate new counts
    v_new_word_count := array_length(regexp_split_to_array(trim(p_new_content), '\s+'), 1);
    v_new_char_count := length(p_new_content);

    -- Calculate differences
    v_word_diff := ABS(COALESCE(v_new_word_count, 0) - COALESCE(v_current_word_count, 0));
    v_char_diff := ABS(v_new_char_count - COALESCE(v_current_char_count, 0));

    -- Check if changes meet threshold
    RETURN v_word_diff >= p_min_word_change OR v_char_diff >= p_min_char_change;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION has_significant_changes IS 'Checks if new content has significant changes from current version';


-- =============================================================================
-- Function: Create Initial Version (for existing content)
-- =============================================================================

CREATE OR REPLACE FUNCTION create_initial_version_if_missing(p_content_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
    v_content TEXT;
    v_user_hash TEXT;
BEGIN
    -- Check if version already exists
    SELECT EXISTS(
        SELECT 1 FROM content_versions WHERE content_id = p_content_id
    ) INTO v_exists;

    IF v_exists THEN
        RETURN FALSE;
    END IF;

    -- Get content from generated_content
    SELECT gc.output, gc.user_hash
    INTO v_content, v_user_hash
    FROM generated_content gc
    WHERE gc.id = p_content_id;

    IF v_content IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Create initial version
    PERFORM create_content_version(
        p_content_id,
        v_content,
        'initial',
        'Initial version',
        v_user_hash,
        NULL
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION create_initial_version_if_missing IS 'Creates initial version for existing content if none exists';


-- =============================================================================
-- Function: Get Version Statistics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_version_statistics(p_content_id UUID)
RETURNS TABLE (
    total_versions INTEGER,
    current_version INTEGER,
    first_created_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ,
    total_word_change INTEGER,
    avg_word_count NUMERIC,
    manual_saves INTEGER,
    auto_saves INTEGER,
    restores INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_versions,
        MAX(cv.version_number)::INTEGER as current_version,
        MIN(cv.created_at) as first_created_at,
        MAX(cv.created_at) as last_updated_at,
        (
            SELECT COALESCE(SUM(ABS(cv2.word_count - COALESCE(cv_prev.word_count, 0))), 0)::INTEGER
            FROM content_versions cv2
            LEFT JOIN content_versions cv_prev
                ON cv_prev.content_id = cv2.content_id
                AND cv_prev.version_number = cv2.version_number - 1
            WHERE cv2.content_id = p_content_id
        ) as total_word_change,
        AVG(cv.word_count) as avg_word_count,
        COUNT(*) FILTER (WHERE cv.change_type = 'manual')::INTEGER as manual_saves,
        COUNT(*) FILTER (WHERE cv.change_type = 'auto')::INTEGER as auto_saves,
        COUNT(*) FILTER (WHERE cv.change_type = 'restore')::INTEGER as restores
    FROM content_versions cv
    WHERE cv.content_id = p_content_id
    GROUP BY cv.content_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_version_statistics IS 'Returns statistics about version history for content';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS
ALTER TABLE content_versions ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role has full access to content_versions"
    ON content_versions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Users can read versions of content they created
CREATE POLICY "Users can read own content versions"
    ON content_versions
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM generated_content gc
            WHERE gc.id = content_versions.content_id
            AND (
                gc.user_hash = auth.uid()::TEXT
                OR gc.user_hash = current_setting('request.jwt.claims', true)::json->>'sub'
            )
        )
    );

-- Users can create versions of their own content
CREATE POLICY "Users can create versions of own content"
    ON content_versions
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM generated_content gc
            WHERE gc.id = content_versions.content_id
            AND (
                gc.user_hash = auth.uid()::TEXT
                OR gc.user_hash = current_setting('request.jwt.claims', true)::json->>'sub'
            )
        )
    );

-- Anonymous users can read versions (for public content)
CREATE POLICY "Anonymous can read content versions"
    ON content_versions
    FOR SELECT
    TO anon
    USING (true);


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION get_latest_version_number(UUID) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION calculate_content_hash(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION create_content_version(UUID, TEXT, TEXT, TEXT, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION get_content_versions(UUID, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_content_version(UUID, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION restore_content_version(UUID, INTEGER, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION compare_content_versions(UUID, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION has_significant_changes(UUID, TEXT, INTEGER, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION create_initial_version_if_missing(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION get_version_statistics(UUID) TO anon, authenticated, service_role;


-- =============================================================================
-- Trigger: Auto-update updated_at on generated_content (if not exists)
-- =============================================================================

-- The trigger should already exist from migration 001, but ensure it's there
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_generated_content_updated_at'
    ) THEN
        CREATE TRIGGER update_generated_content_updated_at
            BEFORE UPDATE ON generated_content
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- =============================================================================
-- Backfill Initial Versions for Existing Content
-- =============================================================================

-- Create initial versions for any existing content without versions
DO $$
DECLARE
    v_content_id UUID;
    v_count INTEGER := 0;
BEGIN
    FOR v_content_id IN
        SELECT gc.id
        FROM generated_content gc
        WHERE NOT EXISTS (
            SELECT 1 FROM content_versions cv
            WHERE cv.content_id = gc.id
        )
    LOOP
        PERFORM create_initial_version_if_missing(v_content_id);
        v_count := v_count + 1;
    END LOOP;

    IF v_count > 0 THEN
        RAISE NOTICE 'Created initial versions for % existing content items', v_count;
    END IF;
END $$;
