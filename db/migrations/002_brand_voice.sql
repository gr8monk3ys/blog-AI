-- Brand voice persistence (Neon/Postgres)
--
-- Tables:
-- - voice_samples: training samples per user/profile
-- - voice_fingerprints: aggregated fingerprint per user/profile

-- Foreign keys reference (id, user_id) so a user cannot write samples/fingerprints
-- against another user's brand profile.
CREATE UNIQUE INDEX IF NOT EXISTS idx_brand_profiles_id_user_id
  ON brand_profiles(id, user_id);

CREATE TABLE IF NOT EXISTS voice_samples (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  profile_id uuid NOT NULL,
  title text,
  content text NOT NULL,
  content_type text NOT NULL DEFAULT 'text',
  word_count integer NOT NULL DEFAULT 0,
  source_url text,
  source_platform text,
  is_analyzed boolean NOT NULL DEFAULT false,
  analysis_result jsonb,
  quality_score double precision NOT NULL DEFAULT 0,
  is_primary_example boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT voice_samples_profile_owner_fk FOREIGN KEY (profile_id, user_id)
    REFERENCES brand_profiles(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_voice_samples_user_profile_created
  ON voice_samples(user_id, profile_id, created_at);
CREATE INDEX IF NOT EXISTS idx_voice_samples_user_created
  ON voice_samples(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS voice_fingerprints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  profile_id uuid NOT NULL,
  vocabulary_profile jsonb NOT NULL DEFAULT '{}'::jsonb,
  sentence_patterns jsonb NOT NULL DEFAULT '{}'::jsonb,
  tone_distribution jsonb NOT NULL DEFAULT '{}'::jsonb,
  style_metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
  voice_summary text NOT NULL DEFAULT '',
  sample_count integer NOT NULL DEFAULT 0,
  training_quality double precision NOT NULL DEFAULT 0,
  last_trained_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT voice_fingerprints_user_profile_unique UNIQUE (user_id, profile_id),
  CONSTRAINT voice_fingerprints_profile_owner_fk FOREIGN KEY (profile_id, user_id)
    REFERENCES brand_profiles(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_voice_fingerprints_user_id
  ON voice_fingerprints(user_id);

