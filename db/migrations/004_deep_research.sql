-- Deep Research tables
-- Stores research queries and their quality-rated sources

CREATE TABLE IF NOT EXISTS research_queries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    depth TEXT NOT NULL DEFAULT 'basic',
    results_json JSONB,
    summary TEXT DEFAULT '',
    total_sources INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_queries_user_id ON research_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_research_queries_query ON research_queries USING gin(to_tsvector('english', query));
CREATE INDEX IF NOT EXISTS idx_research_queries_created_at ON research_queries(created_at DESC);

CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL REFERENCES research_queries(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    quality_score REAL DEFAULT 0,
    credibility_tier TEXT DEFAULT 'unknown',
    quality_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_sources_query_id ON research_sources(query_id);
CREATE INDEX IF NOT EXISTS idx_research_sources_quality ON research_sources(quality_score DESC);
