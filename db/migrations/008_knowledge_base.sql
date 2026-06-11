-- Migration 008: Knowledge-base document metadata (Neon/asyncpg port)
--
-- Second module in the Supabase -> Neon migration (see docs/SCHEMA_AUDIT.md).
-- Backs the document-metadata layer of src/knowledge/knowledge_service.py, which
-- previously stored kb_documents in a separate Supabase project (with an
-- in-memory cache fallback). The vector embeddings remain in the pluggable
-- VectorStore (Chroma/Pinecone); only the relational metadata moves to Neon.
--
-- Columns mirror exactly what knowledge_service reads/writes (the upsert dict and
-- _row_to_document). Plain relational types only — no pgvector — so this runs on
-- the standard Postgres CI image. Feature stays gated behind ENABLE_KNOWLEDGE_BASE
-- (default off). Idempotent and portable (no RLS/role grants).

CREATE TABLE IF NOT EXISTS kb_documents (
  id text PRIMARY KEY,
  user_id text NOT NULL,
  filename text NOT NULL DEFAULT '',
  title text NOT NULL DEFAULT '',
  file_type text NOT NULL DEFAULT 'txt',
  file_size_bytes bigint NOT NULL DEFAULT 0,
  page_count integer,
  chunk_count integer NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'ready',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

-- List documents per user, newest first.
CREATE INDEX IF NOT EXISTS idx_kb_documents_user_created
  ON kb_documents(user_id, created_at DESC);

-- Per-user usage aggregate consumed by src/knowledge/quota.py (_get_kb_usage,
-- which already reads this view through the Neon pool).
CREATE OR REPLACE VIEW kb_usage_stats AS
SELECT
  user_id,
  COUNT(*)                                  AS document_count,
  COALESCE(SUM(file_size_bytes), 0)::bigint AS total_storage_bytes
FROM kb_documents
GROUP BY user_id;
