-- Rollback: 012_blog_posts.sql
-- Description: Drops the blog_posts table, its trigger, and RLS policies.
--
-- WARNING: This will permanently delete all blog post content. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Public read published posts" ON blog_posts;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_blog_posts_updated_at ON blog_posts;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS blog_posts CASCADE;

COMMIT;
