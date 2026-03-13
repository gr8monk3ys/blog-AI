-- Rollback: 010_knowledge_base.sql
-- Description: Drops kb_documents, kb_chunks tables, the kb_usage_by_user view,
--              their functions, triggers, and RLS policies.
--
-- WARNING: This will permanently delete all knowledge base documents and chunks.
--          Vector store references will become orphaned. Back up first.

BEGIN;

-- =========================================================================
-- Drop View
-- =========================================================================
DROP VIEW IF EXISTS kb_usage_by_user CASCADE;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
-- kb_documents
DROP POLICY IF EXISTS "Service role has full access to kb_documents" ON kb_documents;
DROP POLICY IF EXISTS "Users can read own kb_documents" ON kb_documents;
DROP POLICY IF EXISTS "Users can insert own kb_documents" ON kb_documents;
DROP POLICY IF EXISTS "Users can update own kb_documents" ON kb_documents;
DROP POLICY IF EXISTS "Users can delete own kb_documents" ON kb_documents;

-- kb_chunks
DROP POLICY IF EXISTS "Service role has full access to kb_chunks" ON kb_chunks;
DROP POLICY IF EXISTS "Users can read own kb_chunks" ON kb_chunks;
DROP POLICY IF EXISTS "Users can insert own kb_chunks" ON kb_chunks;
DROP POLICY IF EXISTS "Users can delete own kb_chunks" ON kb_chunks;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_kb_documents_updated_at ON kb_documents;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS update_kb_updated_at() CASCADE;
DROP FUNCTION IF EXISTS get_kb_document_stats(TEXT) CASCADE;
DROP FUNCTION IF EXISTS search_kb_documents(TEXT, TEXT, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_kb_chunks_by_document(UUID, TEXT, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS delete_kb_document(UUID, TEXT, BOOLEAN) CASCADE;
DROP FUNCTION IF EXISTS check_kb_duplicate(TEXT, TEXT) CASCADE;

-- =========================================================================
-- Drop Tables (order matters due to foreign keys)
-- =========================================================================
DROP TABLE IF EXISTS kb_chunks CASCADE;
DROP TABLE IF EXISTS kb_documents CASCADE;

COMMIT;
