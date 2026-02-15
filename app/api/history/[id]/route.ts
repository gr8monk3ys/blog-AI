import { NextRequest, NextResponse } from 'next/server'

import { requireClerkUserId } from '../../../../lib/clerk-auth'
import { getSqlOrNull } from '../../../../lib/db'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
    }

    const userId = await requireClerkUserId()
    const { id } = await params

    const rows = await sql.query(
      `SELECT * FROM generated_content WHERE user_id = $1 AND id = $2 LIMIT 1`,
      [userId, id]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 })
    }

    return NextResponse.json({ data: rows[0] })
  } catch (error) {
    console.error('History item GET error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
    }

    const userId = await requireClerkUserId()
    const { id } = await params
    const body = await request.json()

    const wantsToggle = body?.toggle === true
    const wantsSet = typeof body?.isFavorite === 'boolean'

    if (!wantsToggle && !wantsSet) {
      return NextResponse.json(
        { error: 'Provide either { toggle: true } or { isFavorite: boolean }' },
        { status: 400 }
      )
    }

    const rows = wantsToggle
      ? await sql.query(
          `
            UPDATE generated_content
            SET is_favorite = NOT is_favorite, updated_at = NOW()
            WHERE user_id = $1 AND id = $2
            RETURNING is_favorite
          `,
          [userId, id]
        )
      : await sql.query(
          `
            UPDATE generated_content
            SET is_favorite = $3, updated_at = NOW()
            WHERE user_id = $1 AND id = $2
            RETURNING is_favorite
          `,
          [userId, id, body.isFavorite]
        )

    if (!rows || rows.length === 0) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 })
    }

    const is_favorite = (rows[0] as { is_favorite: boolean }).is_favorite
    return NextResponse.json({ is_favorite })
  } catch (error) {
    console.error('History item PATCH error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const sql = getSqlOrNull()
    if (!sql) {
      return NextResponse.json({ error: 'Database not configured' }, { status: 503 })
    }

    const userId = await requireClerkUserId()
    const { id } = await params

    const rows = await sql.query(
      `DELETE FROM generated_content WHERE user_id = $1 AND id = $2 RETURNING id`,
      [userId, id]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('History item DELETE error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

