-- Rollback: 011_better_auth.sql
-- Description: Drops the Better Auth tables created by db/migrations/011_better_auth.sql.
--
-- WARNING: This permanently deletes every account, session and JWT signing key.
-- Back up first.

BEGIN;

DROP TABLE IF EXISTS "jwks" CASCADE;
DROP TABLE IF EXISTS "verification" CASCADE;
DROP TABLE IF EXISTS "account" CASCADE;
DROP TABLE IF EXISTS "session" CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

COMMIT;
