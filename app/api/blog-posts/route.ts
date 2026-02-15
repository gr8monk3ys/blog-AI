import { NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../lib/db'

const getAdminKey = () => process.env.BLOG_ADMIN_KEY

const isAuthorized = (request: Request) => {
  const adminKey = getAdminKey()
  if (!adminKey) return false

  const headerKey =
    request.headers.get('x-admin-key') ||
    request.headers.get('authorization')?.replace('Bearer ', '')

  return headerKey === adminKey
}

export async function GET(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const sql = getSqlOrNull()
  if (!sql) {
    return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
  }

  const data = await sql.query(
    `
      SELECT
        id,
        title,
        slug,
        excerpt,
        tags,
        status,
        published_at,
        updated_at,
        created_at
      FROM blog_posts
      ORDER BY published_at DESC NULLS LAST
    `
  )

  return NextResponse.json({ data })
}

export async function POST(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const sql = getSqlOrNull()
  if (!sql) {
    return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
  }

  const payload = await request.json()

  if (!payload?.title || !payload?.slug || !payload?.body) {
    return NextResponse.json(
      { error: 'Missing required fields: title, slug, body' },
      { status: 400 }
      )
  }

  const rows = await sql.query(
    `
      INSERT INTO blog_posts (
        title,
        slug,
        excerpt,
        body,
        tags,
        status,
        published_at,
        cover_image,
        seo_title,
        seo_description,
        updated_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10, NOW())
      ON CONFLICT (slug) DO UPDATE SET
        title = EXCLUDED.title,
        excerpt = EXCLUDED.excerpt,
        body = EXCLUDED.body,
        tags = EXCLUDED.tags,
        status = EXCLUDED.status,
        published_at = EXCLUDED.published_at,
        cover_image = EXCLUDED.cover_image,
        seo_title = EXCLUDED.seo_title,
        seo_description = EXCLUDED.seo_description,
        updated_at = NOW()
      RETURNING
        id,
        title,
        slug,
        excerpt,
        tags,
        status,
        published_at,
        updated_at,
        created_at
    `,
    [
      payload.title,
      payload.slug,
      payload.excerpt || null,
      payload.body,
      Array.isArray(payload.tags) ? payload.tags : [],
      payload.status || 'draft',
      payload.published_at || null,
      payload.cover_image || null,
      payload.seo_title || null,
      payload.seo_description || null,
    ]
  )

  const data = rows?.[0] ?? null
  return NextResponse.json({ data })
}
