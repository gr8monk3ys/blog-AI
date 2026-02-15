import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../../../lib/db'
import { requireClerkUserId } from '../../../../../lib/clerk-auth'

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * POST /api/brand-profiles/[id]/default
 * Set a brand profile as the default
 */
export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      return NextResponse.json({
        success: true,
        message: 'Brand profile set as default',
      })
    }

    let userId: string
    try {
      userId = await requireClerkUserId()
    } catch {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const isUuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)
    if (!isUuid) {
      return NextResponse.json(
        { success: false, error: 'Invalid brand profile id' },
        { status: 400 }
      )
    }

    const results = await sql.transaction((txn) => [
      txn.query(
        `UPDATE brand_profiles SET is_default = false, updated_at = NOW() WHERE user_id = $1 AND id <> $2`,
        [userId, id]
      ),
      txn.query(
        `UPDATE brand_profiles SET is_default = true, updated_at = NOW() WHERE user_id = $1 AND id = $2 RETURNING id`,
        [userId, id]
      ),
    ])

    const updated = results?.[1] as unknown[] | undefined

    if (!updated || updated.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Brand profile not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Brand profile set as default',
    })
  } catch (error) {
    console.error('Brand profile default POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
