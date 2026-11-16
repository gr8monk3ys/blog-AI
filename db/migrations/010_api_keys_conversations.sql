-- Migration 010: API keys and conversation history in Postgres
--
-- On Vercel's Python runtime the API's disk is ephemeral, so the file stores
-- behind app/auth/api_key.py (API_KEY_STORAGE_PATH) and
-- app/storage/conversations.py (CONVERSATION_STORAGE_DIR) lost every key and
-- conversation on each cold start. With DATABASE_URL set the API now uses these
-- tables instead; the file stores remain the local-dev fallback.
-- Portable/idempotent, no RLS or role grants (the app authorizes in Python).

-- One active key per user. Only hashes are stored, never the plaintext key:
--   key_hash   bcrypt hash, the verifier
--   key_lookup SHA-256 hex of the key, so verification finds the one candidate
--              row by index instead of running bcrypt against every user
CREATE TABLE IF NOT EXISTS api_keys (
  user_id text PRIMARY KEY,
  key_hash text NOT NULL,
  key_lookup text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

-- Messages are appended to a jsonb array. owner_id is set once, when the first
-- message creates the row, and is what conversation access is checked against.
CREATE TABLE IF NOT EXISTS conversations (
  id text PRIMARY KEY,
  owner_id text,
  messages jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);
