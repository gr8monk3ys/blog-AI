-- Rollback: 002_brand_voice.sql
-- Description: Drops voice_samples, voice_fingerprints tables, and the
--              composite unique index on brand_profiles added by this migration.
--
-- WARNING: This will permanently delete all voice training data. Back up first.

BEGIN;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS voice_fingerprints CASCADE;
DROP TABLE IF EXISTS voice_samples CASCADE;

-- =========================================================================
-- Drop the composite unique index added to brand_profiles
-- =========================================================================
DROP INDEX IF EXISTS idx_brand_profiles_id_user_id;

COMMIT;
