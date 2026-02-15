import { NextRequest, NextResponse } from 'next/server'

import { requireClerkUserId } from '../../../lib/clerk-auth'
import { getSqlOrNull } from '../../../lib/db'

type GeneratedContentRow = {
  id: string
  created_at: string
  updated_at: string
  tool_id: string
  tool_name: string | null
  title: string | null
  inputs: Record<string, unknown>
  output: string
  provider: string
  execution_time_ms: number
  user_id: string
  is_favorite: boolean
}

export async function GET(request: NextRequest) {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json(
        { items: [], total: 0, limit: 20, offset: 0, has_more: false },
        { status: 503 }
      )
    }

    const userId = await requireClerkUserId()

    const { searchParams } = new URL(request.url)
    const favoritesOnly = searchParams.get('favorites_only') === 'true'
    const toolId = searchParams.get('tool_id')
    const dateFrom = searchParams.get('date_from')
    const dateTo = searchParams.get('date_to')
    const search = searchParams.get('search')
    const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10) || 20, 100)
    const offset = Math.max(parseInt(searchParams.get('offset') || '0', 10) || 0, 0)

    const where: string[] = ['user_id = $1']
    const params: unknown[] = [userId]
    let i = 2

    if (favoritesOnly) {
      where.push('is_favorite = true')
    }

    if (toolId) {
      where.push(`tool_id = $${i++}`)
      params.push(toolId)
    }

    if (dateFrom) {
      where.push(`created_at >= $${i++}`)
      params.push(dateFrom)
    }

    if (dateTo) {
      where.push(`created_at <= $${i++}`)
      params.push(dateTo)
    }

    if (search) {
      where.push(`(title ILIKE $${i++} OR output ILIKE $${i++})`)
      const pattern = `%${search}%`
      params.push(pattern, pattern)
    }

    const whereSql = `WHERE ${where.join(' AND ')}`

    const countRows = await sql.query(
      `SELECT COUNT(*)::int AS count FROM generated_content ${whereSql}`,
      params
    )
    const total = Number((countRows?.[0] as { count?: unknown } | undefined)?.count ?? 0)

    const rows = await sql.query(
      `
        SELECT
          id,
          created_at,
          updated_at,
          tool_id,
          tool_name,
          title,
          inputs,
          output,
          provider,
          execution_time_ms,
          user_id,
          is_favorite
        FROM generated_content
        ${whereSql}
        ORDER BY created_at DESC
        LIMIT $${i++}
        OFFSET $${i++}
      `,
      [...params, limit, offset]
    )

    const items = (rows as GeneratedContentRow[] | null) || []

    return NextResponse.json({
      items,
      total,
      limit,
      offset,
      has_more: total > offset + limit,
    })
  } catch (error) {
    console.error('History GET error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
    }

    const userId = await requireClerkUserId()
    const body = await request.json()

    if (
      !body?.tool_id ||
      !body?.inputs ||
      !body?.output ||
      !body?.provider ||
      typeof body?.execution_time_ms !== 'number'
    ) {
      return NextResponse.json(
        {
          error:
            'Missing required fields: tool_id, inputs, output, provider, execution_time_ms',
        },
        { status: 400 }
      )
    }

    const rows = await sql.query(
      `
        INSERT INTO generated_content (
          tool_id,
          tool_name,
          title,
          inputs,
          output,
          provider,
          execution_time_ms,
          user_id,
          is_favorite
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,false)
        RETURNING
          id,
          created_at,
          updated_at,
          tool_id,
          tool_name,
          title,
          inputs,
          output,
          provider,
          execution_time_ms,
          user_id,
          is_favorite
      `,
      [
        body.tool_id,
        body.tool_name ?? null,
        body.title ?? null,
        body.inputs,
        body.output,
        body.provider,
        body.execution_time_ms,
        userId,
      ]
    )

    const data = rows?.[0] ?? null
    return NextResponse.json({ data })
  } catch (error) {
    console.error('History POST error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

