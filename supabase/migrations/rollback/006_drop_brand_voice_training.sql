-- Rollback: 006_enhance_brand_voice_training.sql
-- Description: Drops voice_samples, voice_fingerprints, and voice_scores tables
--              created by the enhanced brand voice training migration.
--              Also removes columns added to brand_profiles.
--
-- WARNING: This will permanently delete all voice training data. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- voice_samples
DROP POLICY IF EXISTS "Service role has full access to voice_samples" ON voice_samples;
DROP POLICY IF EXISTS "Users can manage samples via profile" ON voice_samples;

-- voice_fingerprints
DROP POLICY IF EXISTS "Service role has full access to voice_fingerprints" ON voice_fingerprints;
DROP POLICY IF EXISTS "Users can read fingerprints via profile" ON voice_fingerprints;

-- voice_scores
DROP POLICY IF EXISTS "Service role has full access to voice_scores" ON voice_scores;
DROP POLICY IF EXISTS "Users can read scores via profile" ON voice_scores;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_voice_fingerprints_updated_at ON voice_fingerprints;

-- =========================================================================
-- Remove columns added to brand_profiles
-- =========================================================================
ALTER TABLE brand_profiles DROP COLUMN IF EXISTS voice_fingerprint_id;
ALTER TABLE brand_profiles DROP COLUMN IF EXISTS training_status;
ALTER TABLE brand_profiles DROP COLUMN IF EXISTS training_quality;
ALTER TABLE brand_profiles DROP COLUMN IF EXISTS sample_count;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS voice_scores CASCADE;
DROP TABLE IF EXISTS voice_fingerprints CASCADE;
DROP TABLE IF EXISTS voice_samples CASCADE;

COMMIT;
