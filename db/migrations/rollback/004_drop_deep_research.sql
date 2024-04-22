-- Rollback: 004_deep_research.sql
-- Description: Drops research_queries and research_sources tables.
--
-- WARNING: This will permanently delete all research data. Back up first.

BEGIN;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS research_sources CASCADE;
DROP TABLE IF EXISTS research_queries CASCADE;

COMMIT;
