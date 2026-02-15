import { NextResponse } from 'next/server'

import { requireClerkUserId } from '../../../../lib/clerk-auth'
import { getSqlOrNull } from '../../../../lib/db'

export async function GET() {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
    }

    const userId = await requireClerkUserId()

    const [totalRows, favRows, recentRows, byToolRows] = await Promise.all([
      sql.query(
        `SELECT COUNT(*)::int AS count FROM generated_content WHERE user_id = $1`,
        [userId]
      ),
      sql.query(
        `SELECT COUNT(*)::int AS count FROM generated_content WHERE user_id = $1 AND is_favorite = true`,
        [userId]
      ),
      sql.query(
        `SELECT COUNT(*)::int AS count FROM generated_content WHERE user_id = $1 AND created_at >= (NOW() - INTERVAL '7 days')`,
        [userId]
      ),
      sql.query(
        `SELECT tool_id, COUNT(*)::int AS count FROM generated_content WHERE user_id = $1 GROUP BY tool_id`,
        [userId]
      ),
    ])

    const total_generations = Number(
      (totalRows?.[0] as { count?: unknown } | undefined)?.count ?? 0
    )
    const total_favorites = Number(
      (favRows?.[0] as { count?: unknown } | undefined)?.count ?? 0
    )
    const recent_count = Number(
      (recentRows?.[0] as { count?: unknown } | undefined)?.count ?? 0
    )

    const by_tool: Record<string, number> = {}
    for (const row of (byToolRows as any[]) || []) {
      by_tool[row.tool_id] = Number(row.count) || 0
    }

    return NextResponse.json({
      total_generations,
      total_favorites,
      by_category: {}, // computed client-side using tool_id -> category mapping
      by_tool,
      recent_count,
    })
  } catch (error) {
    console.error('History stats GET error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

