import fs from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

import { Pool } from '@neondatabase/serverless'

const DATABASE_URL =
  process.env.DATABASE_URL_DIRECT || process.env.DATABASE_URL || ''

if (!DATABASE_URL) {
  console.error(
    'Missing DATABASE_URL (or DATABASE_URL_DIRECT) for migrations.'
  )
  process.exit(1)
}

const migrationsDir = path.join(process.cwd(), 'db', 'migrations')

const files = (await fs.readdir(migrationsDir))
  .filter((f) => f.endsWith('.sql'))
  .sort((a, b) => a.localeCompare(b))

if (files.length === 0) {
  console.log('No migrations found.')
  process.exit(0)
}

const pool = new Pool({ connectionString: DATABASE_URL })

try {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      filename text PRIMARY KEY,
      applied_at timestamptz NOT NULL DEFAULT NOW()
    )
  `)

  for (const filename of files) {
    const already = await pool.query(
      `SELECT 1 FROM schema_migrations WHERE filename = $1 LIMIT 1`,
      [filename]
    )
    if (already.rows.length > 0) {
      continue
    }

    const sql = await fs.readFile(path.join(migrationsDir, filename), 'utf8')

    await pool.query('BEGIN')
    try {
      await pool.query(sql)
      await pool.query(
        `INSERT INTO schema_migrations (filename) VALUES ($1)`,
        [filename]
      )
      await pool.query('COMMIT')
      console.log(`Applied migration: ${filename}`)
    } catch (err) {
      await pool.query('ROLLBACK')
      console.error(`Failed migration: ${filename}`)
      throw err
    }
  }

  console.log('Migrations complete.')
} finally {
  await pool.end()
}

