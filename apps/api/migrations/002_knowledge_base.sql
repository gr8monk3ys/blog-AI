-- Knowledge Base tables for pgvector-based RAG system
-- Requires: PostgreSQL 15+ with pgvector extension

BEGIN;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- kb_documents: Document metadata for uploaded knowledge base files
-- =============================================================================
CREATE TABLE IF NOT EXISTS kb_documents (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    filename    TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    file_type   TEXT NOT NULL DEFAULT 'txt',
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'processing',
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_documents_user_id
    ON kb_documents (user_id);

CREATE INDEX IF NOT EXISTS idx_kb_documents_status
    ON kb_documents (status);

CREATE INDEX IF NOT EXISTS idx_kb_documents_user_created
    ON kb_documents (user_id, created_at DESC);

-- =============================================================================
-- kb_embeddings: Vector embeddings for document chunks
-- =============================================================================
CREATE TABLE IF NOT EXISTS kb_embeddings (
    id              TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL DEFAULT 0,
    content         TEXT NOT NULL,
    embedding       vector(1536) NOT NULL,
    page_number     INTEGER,
    section_title   TEXT,
    token_count     INTEGER NOT NULL DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_embeddings_document_id
    ON kb_embeddings (document_id);

CREATE INDEX IF NOT EXISTS idx_kb_embeddings_user_id
    ON kb_embeddings (user_id);

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_kb_embeddings_hnsw
    ON kb_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- =============================================================================
-- kb_usage_stats: Aggregated per-user document count and storage
-- =============================================================================
CREATE OR REPLACE VIEW kb_usage_stats AS
SELECT
    user_id,
    COUNT(*)            AS document_count,
    COALESCE(SUM(file_size_bytes), 0) AS total_storage_bytes,
    COALESCE(SUM(chunk_count), 0)     AS total_chunks
FROM kb_documents
WHERE status != 'deleted'
GROUP BY user_id;

COMMIT;
