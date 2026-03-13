-- Rollback: 003_create_conversations.sql
-- Description: Drops the conversations table, its functions, trigger,
--              and RLS policies.
--
-- WARNING: This will permanently delete all conversation history. Back up first.

BEGIN;

-- =========================================================================
-- Drop RLS Policies
-- =========================================================================
DROP POLICY IF EXISTS "Service role has full access to conversations" ON conversations;
DROP POLICY IF EXISTS "Anonymous can manage conversations" ON conversations;

-- =========================================================================
-- Drop Trigger
-- =========================================================================
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;

-- =========================================================================
-- Drop Functions
-- =========================================================================
DROP FUNCTION IF EXISTS upsert_conversation(TEXT, JSONB, JSONB) CASCADE;
DROP FUNCTION IF EXISTS add_conversation_message(TEXT, JSONB) CASCADE;

-- =========================================================================
-- Drop Table
-- =========================================================================
DROP TABLE IF EXISTS conversations CASCADE;

COMMIT;
