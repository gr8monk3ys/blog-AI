-- Migration: Enhance brand voice training with samples and fingerprints
-- Description: Adds voice samples, embeddings, and analytics for advanced brand voice training

-- Voice samples table for training
CREATE TABLE IF NOT EXISTS voice_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES brand_profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Sample content
    title TEXT,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text', -- text, blog, email, social
    word_count INT NOT NULL DEFAULT 0,

    -- Source metadata
    source_url TEXT,
    source_platform TEXT, -- website, linkedin, twitter, email

    -- Analysis results (populated by AI)
    is_analyzed BOOLEAN NOT NULL DEFAULT false,
    analysis_result JSONB DEFAULT '{}',

    -- Quality indicators
    quality_score FLOAT DEFAULT 0.0,
    is_primary_example BOOLEAN DEFAULT false
);

-- Voice fingerprint table for style embeddings
CREATE TABLE IF NOT EXISTS voice_fingerprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES brand_profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Aggregated voice characteristics (from analyzed samples)
    vocabulary_profile JSONB DEFAULT '{}', -- common words, phrases, patterns
    sentence_patterns JSONB DEFAULT '{}', -- avg length, structure types
    tone_distribution JSONB DEFAULT '{}', -- tone scores across samples
    style_metrics JSONB DEFAULT '{}', -- formality, complexity, etc.

    -- Synthesized voice description (for prompts)
    voice_summary TEXT,

    -- Embedding vector (if using vector similarity)
    embedding_vector FLOAT[] DEFAULT '{}',
    embedding_model TEXT,

    -- Training metadata
    sample_count INT DEFAULT 0,
    last_trained_at TIMESTAMPTZ,
    training_quality FLOAT DEFAULT 0.0
);

-- Voice consistency scores for generated content
CREATE TABLE IF NOT EXISTS voice_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES brand_profiles(id) ON DELETE CASCADE,
    content_id TEXT NOT NULL, -- reference to generated content
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Scores (0-1)
    overall_score FLOAT NOT NULL,
    tone_match FLOAT NOT NULL,
    vocabulary_match FLOAT NOT NULL,
    style_match FLOAT NOT NULL,

    -- Detailed feedback
    feedback JSONB DEFAULT '{}',

    -- Comparison to fingerprint
    deviations JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_voice_samples_profile ON voice_samples(profile_id);
CREATE INDEX idx_voice_samples_analyzed ON voice_samples(is_analyzed) WHERE is_analyzed = false;
CREATE INDEX idx_voice_samples_primary ON voice_samples(profile_id) WHERE is_primary_example = true;

CREATE UNIQUE INDEX idx_voice_fingerprints_profile ON voice_fingerprints(profile_id);

CREATE INDEX idx_voice_scores_profile ON voice_scores(profile_id);
CREATE INDEX idx_voice_scores_content ON voice_scores(content_id);
CREATE INDEX idx_voice_scores_created ON voice_scores(created_at DESC);

-- Triggers
CREATE TRIGGER update_voice_fingerprints_updated_at
    BEFORE UPDATE ON voice_fingerprints
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add enhanced columns to brand_profiles
ALTER TABLE brand_profiles
    ADD COLUMN IF NOT EXISTS voice_fingerprint_id UUID REFERENCES voice_fingerprints(id),
    ADD COLUMN IF NOT EXISTS training_status TEXT DEFAULT 'untrained', -- untrained, training, trained
    ADD COLUMN IF NOT EXISTS training_quality FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS sample_count INT DEFAULT 0;

-- RLS Policies for voice_samples
ALTER TABLE voice_samples ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to voice_samples"
    ON voice_samples FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Users can manage samples via profile"
    ON voice_samples FOR ALL TO anon
    USING (EXISTS (
        SELECT 1 FROM brand_profiles bp
        WHERE bp.id = profile_id AND bp.user_hash IS NOT NULL
    ));

-- RLS Policies for voice_fingerprints
ALTER TABLE voice_fingerprints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to voice_fingerprints"
    ON voice_fingerprints FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Users can read fingerprints via profile"
    ON voice_fingerprints FOR SELECT TO anon
    USING (EXISTS (
        SELECT 1 FROM brand_profiles bp
        WHERE bp.id = profile_id AND bp.user_hash IS NOT NULL
    ));

-- RLS Policies for voice_scores
ALTER TABLE voice_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to voice_scores"
    ON voice_scores FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Users can read scores via profile"
    ON voice_scores FOR SELECT TO anon
    USING (EXISTS (
        SELECT 1 FROM brand_profiles bp
        WHERE bp.id = profile_id AND bp.user_hash IS NOT NULL
    ));

-- Comments
COMMENT ON TABLE voice_samples IS 'Content samples used to train brand voice profiles';
COMMENT ON TABLE voice_fingerprints IS 'Aggregated voice characteristics extracted from samples';
COMMENT ON TABLE voice_scores IS 'Consistency scores for generated content against brand voice';

COMMENT ON COLUMN voice_samples.analysis_result IS 'JSON with extracted patterns: {vocabulary, sentences, tone, style}';
COMMENT ON COLUMN voice_fingerprints.voice_summary IS 'AI-generated natural language description of the voice for prompting';
COMMENT ON COLUMN voice_fingerprints.embedding_vector IS 'Optional vector representation for similarity matching';
