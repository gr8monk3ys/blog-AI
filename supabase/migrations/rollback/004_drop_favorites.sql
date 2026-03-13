-- Rollback: 004_add_favorites.sql
-- Description: Removes is_favorite, tool_name, and title columns from
--              generated_content, and drops the toggle/set favorite functions.
--
-- WARNING: Favorite status and titles for generated content will be lost. Back up first.

BEGIN;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS toggle_favorite(UUID) CASCADE;
DROP FUNCTION IF EXISTS set_favorite(UUID, BOOLEAN) CASCADE;

-- =========================================================================
-- Drop Indexes
-- =========================================================================
DROP INDEX IF EXISTS idx_generated_content_is_favorite;
DROP INDEX IF EXISTS idx_generated_content_user_favorites;
DROP INDEX IF EXISTS idx_generated_content_title;

-- =========================================================================
-- Remove columns from generated_content
-- =========================================================================
ALTER TABLE generated_content DROP COLUMN IF EXISTS is_favorite;
ALTER TABLE generated_content DROP COLUMN IF EXISTS tool_name;
ALTER TABLE generated_content DROP COLUMN IF EXISTS title;

COMMIT;
