import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../../../lib/db'

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * POST /api/templates/[id]/use
 * Increment template use count
 *
 * Note: In production, the actual increment would be done via
 * an RPC function or raw SQL. For now, we just acknowledge the request.
 */
export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      return NextResponse.json({
        success: true,
        message: 'Template use count incremented',
      })
    }

    const isUuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

    const rows = await sql.query(
      `
        UPDATE templates
        SET use_count = use_count + 1, updated_at = NOW()
        WHERE ${isUuid ? 'id' : 'slug'} = $1
        RETURNING id
      `,
      [id]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Template not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Template use count incremented',
    })
  } catch (error) {
    console.error('Template use POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
