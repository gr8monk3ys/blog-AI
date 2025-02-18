import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../../lib/db'

const getAdminKey = () => process.env.BLOG_ADMIN_KEY

const isAuthorized = (request: Request) => {
  const adminKey = getAdminKey()
  if (!adminKey) return false

  const headerKey =
    request.headers.get('x-admin-key') ||
    request.headers.get('authorization')?.replace('Bearer ', '')

  return headerKey === adminKey
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const resolvedParams = await params
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const sql = getSqlOrNull()
  if (!sql) {
    return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
  }

  const rows = await sql.query(`SELECT * FROM blog_posts WHERE slug = $1 LIMIT 1`, [
    resolvedParams.slug,
  ])

  if (!rows || rows.length === 0) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  const data = rows[0] ?? null
  return NextResponse.json({ data })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const resolvedParams = await params
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const sql = getSqlOrNull()
  if (!sql) {
    return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
  }

  const rows = await sql.query(`DELETE FROM blog_posts WHERE slug = $1 RETURNING id`, [
    resolvedParams.slug,
  ])

  if (!rows || rows.length === 0) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  return NextResponse.json({ success: true })
}
