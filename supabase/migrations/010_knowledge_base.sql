-- Migration: Create Knowledge Base / RAG System Tables
-- Description: Implements tables for storing uploaded documents and their chunks
--              for the Retrieval Augmented Generation (RAG) system.
--
-- Tables:
--   kb_documents: Uploaded document metadata
--   kb_chunks: Document chunks with references to vectors
--
-- Features:
--   - Multi-tenant isolation via user_id
--   - Row Level Security policies
--   - Efficient indexing for document retrieval
--   - Support for various file types

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Knowledge Base Documents Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS kb_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,

    -- Document information
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx', 'txt', 'md', 'html')),
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    page_count INTEGER,

    -- Processing status
    status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'error', 'deleted')),
    error_message TEXT,
    chunk_count INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    language TEXT DEFAULT 'en',

    -- Source tracking
    source_url TEXT,
    source_hash TEXT,  -- SHA-256 hash of original content for deduplication

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_file_size CHECK (file_size_bytes >= 0),
    CONSTRAINT valid_chunk_count CHECK (chunk_count >= 0)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_kb_documents_user_id
    ON kb_documents(user_id);

CREATE INDEX IF NOT EXISTS idx_kb_documents_user_status
    ON kb_documents(user_id, status);

CREATE INDEX IF NOT EXISTS idx_kb_documents_user_created
    ON kb_documents(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_kb_documents_file_type
    ON kb_documents(user_id, file_type);

CREATE INDEX IF NOT EXISTS idx_kb_documents_source_hash
    ON kb_documents(source_hash) WHERE source_hash IS NOT NULL;

-- Full text search index on title
CREATE INDEX IF NOT EXISTS idx_kb_documents_title_fts
    ON kb_documents USING gin(to_tsvector('english', title));

-- Comments
COMMENT ON TABLE kb_documents IS 'Stores metadata for uploaded documents in the knowledge base';
COMMENT ON COLUMN kb_documents.user_id IS 'ID of the user who uploaded the document';
COMMENT ON COLUMN kb_documents.file_type IS 'Type of document: pdf, docx, txt, md, html';
COMMENT ON COLUMN kb_documents.status IS 'Processing status: processing, ready, error, deleted';
COMMENT ON COLUMN kb_documents.metadata IS 'Additional metadata from document parsing';
COMMENT ON COLUMN kb_documents.source_hash IS 'SHA-256 hash for content deduplication';


-- =============================================================================
-- Knowledge Base Chunks Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS kb_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,

    -- Chunk information
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,  -- SHA-256 hash for deduplication

    -- Position information
    page_number INTEGER,
    section_title TEXT,
    start_char INTEGER NOT NULL DEFAULT 0,
    end_char INTEGER NOT NULL DEFAULT 0,

    -- Token/size information
    token_count INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,

    -- Vector store reference
    vector_id TEXT,  -- ID in the vector store (Pinecone/ChromaDB)
    embedding_model TEXT,  -- Model used to generate embedding

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(document_id, chunk_index),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT valid_char_positions CHECK (start_char >= 0 AND end_char >= start_char)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_kb_chunks_document_id
    ON kb_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_user_id
    ON kb_chunks(user_id);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_document_index
    ON kb_chunks(document_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_vector_id
    ON kb_chunks(vector_id) WHERE vector_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_kb_chunks_content_hash
    ON kb_chunks(content_hash);

-- Full text search index on content
CREATE INDEX IF NOT EXISTS idx_kb_chunks_content_fts
    ON kb_chunks USING gin(to_tsvector('english', content));

-- Comments
COMMENT ON TABLE kb_chunks IS 'Stores document chunks for the knowledge base RAG system';
COMMENT ON COLUMN kb_chunks.chunk_index IS 'Sequential index of this chunk within the document';
COMMENT ON COLUMN kb_chunks.vector_id IS 'Reference to the vector in external vector store';
COMMENT ON COLUMN kb_chunks.embedding_model IS 'Name of the model used to generate the embedding';


-- =============================================================================
-- Function: Update timestamp trigger
-- =============================================================================

CREATE OR REPLACE FUNCTION update_kb_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for kb_documents
DROP TRIGGER IF EXISTS update_kb_documents_updated_at ON kb_documents;
CREATE TRIGGER update_kb_documents_updated_at
    BEFORE UPDATE ON kb_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_kb_updated_at();


-- =============================================================================
-- Function: Get Document Statistics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_kb_document_stats(p_user_id TEXT)
RETURNS TABLE (
    total_documents INTEGER,
    total_chunks INTEGER,
    total_size_bytes BIGINT,
    documents_by_status JSONB,
    documents_by_type JSONB,
    oldest_document TIMESTAMPTZ,
    newest_document TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT d.id)::INTEGER as total_documents,
        COALESCE(SUM(d.chunk_count), 0)::INTEGER as total_chunks,
        COALESCE(SUM(d.file_size_bytes), 0)::BIGINT as total_size_bytes,
        (
            SELECT jsonb_object_agg(status, cnt)
            FROM (
                SELECT status, COUNT(*)::INTEGER as cnt
                FROM kb_documents
                WHERE user_id = p_user_id
                GROUP BY status
            ) s
        ) as documents_by_status,
        (
            SELECT jsonb_object_agg(file_type, cnt)
            FROM (
                SELECT file_type, COUNT(*)::INTEGER as cnt
                FROM kb_documents
                WHERE user_id = p_user_id AND status != 'deleted'
                GROUP BY file_type
            ) t
        ) as documents_by_type,
        MIN(d.created_at) as oldest_document,
        MAX(d.created_at) as newest_document
    FROM kb_documents d
    WHERE d.user_id = p_user_id AND d.status != 'deleted';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_kb_document_stats IS 'Returns aggregated statistics for a user knowledge base';


-- =============================================================================
-- Function: Search Documents by Title
-- =============================================================================

CREATE OR REPLACE FUNCTION search_kb_documents(
    p_user_id TEXT,
    p_query TEXT,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    filename TEXT,
    title TEXT,
    file_type TEXT,
    chunk_count INTEGER,
    created_at TIMESTAMPTZ,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.filename,
        d.title,
        d.file_type,
        d.chunk_count,
        d.created_at,
        ts_rank(to_tsvector('english', d.title), plainto_tsquery('english', p_query)) as rank
    FROM kb_documents d
    WHERE d.user_id = p_user_id
      AND d.status = 'ready'
      AND (
          to_tsvector('english', d.title) @@ plainto_tsquery('english', p_query)
          OR d.title ILIKE '%' || p_query || '%'
      )
    ORDER BY rank DESC, d.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION search_kb_documents IS 'Full-text search on document titles';


-- =============================================================================
-- Function: Get Chunks by Document
-- =============================================================================

CREATE OR REPLACE FUNCTION get_kb_chunks_by_document(
    p_document_id UUID,
    p_user_id TEXT,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    chunk_index INTEGER,
    content TEXT,
    page_number INTEGER,
    section_title TEXT,
    token_count INTEGER,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    -- Verify document belongs to user
    IF NOT EXISTS (
        SELECT 1 FROM kb_documents
        WHERE kb_documents.id = p_document_id
          AND kb_documents.user_id = p_user_id
    ) THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        c.id,
        c.chunk_index,
        c.content,
        c.page_number,
        c.section_title,
        c.token_count,
        c.created_at
    FROM kb_chunks c
    WHERE c.document_id = p_document_id
    ORDER BY c.chunk_index
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_kb_chunks_by_document IS 'Get all chunks for a document';


-- =============================================================================
-- Function: Delete Document and Chunks
-- =============================================================================

CREATE OR REPLACE FUNCTION delete_kb_document(
    p_document_id UUID,
    p_user_id TEXT,
    p_hard_delete BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    success BOOLEAN,
    chunks_deleted INTEGER,
    message TEXT
) AS $$
DECLARE
    v_chunk_count INTEGER;
BEGIN
    -- Verify document belongs to user
    IF NOT EXISTS (
        SELECT 1 FROM kb_documents
        WHERE kb_documents.id = p_document_id
          AND kb_documents.user_id = p_user_id
    ) THEN
        RETURN QUERY SELECT FALSE, 0, 'Document not found or access denied'::TEXT;
        RETURN;
    END IF;

    -- Count chunks to be deleted
    SELECT COUNT(*) INTO v_chunk_count
    FROM kb_chunks WHERE document_id = p_document_id;

    IF p_hard_delete THEN
        -- Hard delete: remove completely
        DELETE FROM kb_chunks WHERE document_id = p_document_id;
        DELETE FROM kb_documents WHERE id = p_document_id;
    ELSE
        -- Soft delete: mark as deleted
        UPDATE kb_documents
        SET status = 'deleted', updated_at = NOW()
        WHERE id = p_document_id;
    END IF;

    RETURN QUERY SELECT
        TRUE as success,
        v_chunk_count as chunks_deleted,
        format('Document %s deleted with %s chunks', p_document_id, v_chunk_count)::TEXT as message;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION delete_kb_document IS 'Soft or hard delete a document and its chunks';


-- =============================================================================
-- Function: Check for Duplicate Document
-- =============================================================================

CREATE OR REPLACE FUNCTION check_kb_duplicate(
    p_user_id TEXT,
    p_source_hash TEXT
)
RETURNS TABLE (
    is_duplicate BOOLEAN,
    existing_document_id UUID,
    existing_title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TRUE as is_duplicate,
        d.id as existing_document_id,
        d.title as existing_title
    FROM kb_documents d
    WHERE d.user_id = p_user_id
      AND d.source_hash = p_source_hash
      AND d.status = 'ready'
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_kb_duplicate IS 'Check if a document with the same content hash already exists';


-- =============================================================================
-- Row Level Security Policies
-- =============================================================================

-- Enable RLS
ALTER TABLE kb_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_chunks ENABLE ROW LEVEL SECURITY;

-- Service role has full access to kb_documents
CREATE POLICY "Service role has full access to kb_documents"
    ON kb_documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Service role has full access to kb_chunks
CREATE POLICY "Service role has full access to kb_chunks"
    ON kb_chunks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Users can read their own documents
CREATE POLICY "Users can read own kb_documents"
    ON kb_documents
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can insert their own documents
CREATE POLICY "Users can insert own kb_documents"
    ON kb_documents
    FOR INSERT
    TO authenticated
    WITH CHECK (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can update their own documents
CREATE POLICY "Users can update own kb_documents"
    ON kb_documents
    FOR UPDATE
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    )
    WITH CHECK (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can delete their own documents
CREATE POLICY "Users can delete own kb_documents"
    ON kb_documents
    FOR DELETE
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can read chunks of their documents
CREATE POLICY "Users can read own kb_chunks"
    ON kb_chunks
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can insert chunks for their documents
CREATE POLICY "Users can insert own kb_chunks"
    ON kb_chunks
    FOR INSERT
    TO authenticated
    WITH CHECK (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Users can delete chunks of their documents
CREATE POLICY "Users can delete own kb_chunks"
    ON kb_chunks
    FOR DELETE
    TO authenticated
    USING (
        user_id = auth.uid()::TEXT
        OR user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    );

-- Anonymous access is denied (no policies for anon role)


-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION get_kb_document_stats(TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION search_kb_documents(TEXT, TEXT, INTEGER, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_kb_chunks_by_document(UUID, TEXT, INTEGER, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION delete_kb_document(UUID, TEXT, BOOLEAN) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION check_kb_duplicate(TEXT, TEXT) TO authenticated, service_role;


-- =============================================================================
-- Create Usage Tracking View (Optional)
-- =============================================================================

CREATE OR REPLACE VIEW kb_usage_by_user AS
SELECT
    user_id,
    COUNT(DISTINCT id) as document_count,
    SUM(chunk_count) as total_chunks,
    SUM(file_size_bytes) as total_size_bytes,
    MIN(created_at) as first_upload,
    MAX(created_at) as last_upload
FROM kb_documents
WHERE status != 'deleted'
GROUP BY user_id;

COMMENT ON VIEW kb_usage_by_user IS 'Aggregated knowledge base usage per user';

GRANT SELECT ON kb_usage_by_user TO service_role;
