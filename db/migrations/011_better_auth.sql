-- Migration 011: Better Auth tables (email + password, email verification, JWT plugin)
--
-- The web app's Better Auth instance (apps/web/lib/auth.ts) reads and
-- writes these through `pg`; the API never touches them, it verifies the JWTs Better Auth
-- signs with the keys in "jwks" via GET /api/auth/jwks. user.id is the `sub` claim and
-- the user_id every other table is scoped by.
--
-- Generated from better-auth 1.7.27's getMigrations() for the options in lib/auth.ts,
-- then made idempotent. Column names are Better Auth's camelCase, hence the quoting.
-- Regenerate (and add a new migration) when a Better Auth upgrade or a new plugin
-- changes the schema.

CREATE TABLE IF NOT EXISTS "user" (
  "id" text NOT NULL PRIMARY KEY,
  "name" text NOT NULL,
  "email" text NOT NULL UNIQUE,
  "emailVerified" boolean NOT NULL,
  "image" text,
  "createdAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updatedAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS "session" (
  "id" text NOT NULL PRIMARY KEY,
  "expiresAt" timestamptz NOT NULL,
  "token" text NOT NULL UNIQUE,
  "createdAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updatedAt" timestamptz NOT NULL,
  "ipAddress" text,
  "userAgent" text,
  "userId" text NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "account" (
  "id" text NOT NULL PRIMARY KEY,
  "accountId" text NOT NULL,
  "providerId" text NOT NULL,
  "userId" text NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
  "accessToken" text,
  "refreshToken" text,
  "idToken" text,
  "accessTokenExpiresAt" timestamptz,
  "refreshTokenExpiresAt" timestamptz,
  "scope" text,
  "password" text,
  "createdAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS "verification" (
  "id" text NOT NULL PRIMARY KEY,
  "identifier" text NOT NULL,
  "value" text NOT NULL,
  "expiresAt" timestamptz NOT NULL,
  "createdAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updatedAt" timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS "jwks" (
  "id" text NOT NULL PRIMARY KEY,
  "publicKey" text NOT NULL,
  "privateKey" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  "expiresAt" timestamptz,
  "alg" text,
  "crv" text
);

CREATE INDEX IF NOT EXISTS "session_userId_idx" ON "session" ("userId");
CREATE INDEX IF NOT EXISTS "account_userId_idx" ON "account" ("userId");
CREATE INDEX IF NOT EXISTS "verification_identifier_idx" ON "verification" ("identifier");
