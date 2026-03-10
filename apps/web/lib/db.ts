/**
 * Neon Postgres client (server-only)
 *
 * Uses Neon's serverless driver which is safe for Vercel serverless runtimes.
 * Never import this from client components.
 */

import { neon, type NeonQueryFunction } from '@neondatabase/serverless'

// `ReturnType<typeof neon>` widens generics to `<boolean, boolean>` which makes
// `.query()` appear to sometimes return full results objects. We only use the
// default mode: object rows + rows-only results.
type NeonSql = NeonQueryFunction<false, false>

let sqlInstance: NeonSql | null = null

/**
 * Returns true when a database connection string is configured.
 */
export function isDatabaseConfigured(): boolean {
  return !!process.env.DATABASE_URL
}

/**
 * Get a singleton Neon SQL client, or null if DATABASE_URL is not set.
 *
 * Prefer this in route handlers when you want to gracefully degrade in dev/tests.
 */
export function getSqlOrNull() {
  if (sqlInstance) return sqlInstance
  const url = process.env.DATABASE_URL
  if (!url) return null
  sqlInstance = neon(url)
  return sqlInstance
}

/**
 * Get a singleton Neon SQL client.
 * Throws if DATABASE_URL is not set.
 */
export function getSql() {
  const sql = getSqlOrNull()
  if (!sql) {
    throw new Error('DATABASE_URL is not configured')
  }
  return sql
}
