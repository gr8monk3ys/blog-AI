-- Migration 007: Content versioning (Neon/asyncpg port of the Supabase module)
--
-- Backs NeonVersionService (src/content/version_service.py), the asyncpg
-- implementation of content versioning. Previously this feature only worked
-- against a separate Supabase project (supabase/migrations/009) via supabase-py;
-- this brings it onto the Neon datastore the rest of the app uses.
--
-- Feature stays gated behind ENABLE_CONTENT_VERSIONING (default off); these
-- tables are inert until it's enabled. Portable/idempotent: no RLS, no Supabase
-- role grants. content_id is an opaque TEXT key (not FK'd to generated_content,
-- whose id is UUID) so any content identifier can be versioned, matching the
-- in-memory implementation's contract.

CREATE TABLE IF NOT EXISTS content_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id text NOT NULL,
  version_number integer NOT NULL,
  content text NOT NULL,
  content_hash text NOT NULL,
  diff_from_previous text,
  change_type text NOT NULL DEFAULT 'manual'
    CHECK (change_type IN ('manual', 'auto', 'restore', 'initial')),
  change_summary text,
  word_count integer NOT NULL DEFAULT 0,
  character_count integer NOT NULL DEFAULT 0,
  created_by text,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  is_current boolean NOT NULL DEFAULT true,
  UNIQUE (content_id, version_number)
);

-- History lookups (newest first) and duplicate detection by hash.
CREATE INDEX IF NOT EXISTS idx_content_versions_content_id
  ON content_versions(content_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_content_versions_hash
  ON content_versions(content_id, content_hash);

-- Per-content organization ownership, registered on first version create and
-- checked on every subsequent operation (the Neon equivalent of the in-memory
-- ownership map; the Supabase path read generated_content.organization_id, a
-- column the Neon generated_content table does not have).
CREATE TABLE IF NOT EXISTS content_version_organizations (
  content_id text PRIMARY KEY,
  organization_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW()
);
