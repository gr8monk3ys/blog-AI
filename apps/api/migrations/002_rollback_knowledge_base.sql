-- Rollback: Knowledge Base tables
-- Drops tables and extension added by 002_knowledge_base.sql

BEGIN;

DROP VIEW IF EXISTS kb_usage_stats;
DROP TABLE IF EXISTS kb_embeddings;
DROP TABLE IF EXISTS kb_documents;
-- NOTE: Only drop pgvector if no other tables use it
-- DROP EXTENSION IF EXISTS vector;

COMMIT;
