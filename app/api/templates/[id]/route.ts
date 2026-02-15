import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../../lib/db'
import { getClerkUserIdOrNull, requireClerkUserId } from '../../../../lib/clerk-auth'
import { SAMPLE_TEMPLATES } from '../../../../types/templates'

type TemplateRow = {
  id: string
  name: string
  description: string | null
  slug: string
  tool_id: string
  preset_inputs: Record<string, unknown>
  category: string
  tags: string[] | null
  is_public: boolean
  use_count: number
  created_at: string
  updated_at: string
}

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * GET /api/templates/[id]
 * Get a specific template by ID or slug
 */
export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    const sql = getSqlOrNull()

    // If DB is not configured, return sample data
    if (!sql) {
      const template = SAMPLE_TEMPLATES.find((t) => t.id === id || t.slug === id)

      if (!template) {
        return NextResponse.json(
          { success: false, error: 'Template not found' },
          { status: 404 }
        )
      }

      return NextResponse.json({
        success: true,
        data: template,
      })
    }

    const userId = await getClerkUserIdOrNull()

    // Check if it's a UUID
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

    const rows = await sql.query(
      `
        SELECT
          id,
          name,
          description,
          slug,
          tool_id,
          preset_inputs,
          category,
          tags,
          is_public,
          use_count,
          created_at,
          updated_at
        FROM templates
        WHERE
          (${userId ? '(is_public = true OR user_id = $1)' : 'is_public = true'})
          AND ${isUuid ? 'id' : 'slug'} = ${userId ? '$2' : '$1'}
        LIMIT 1
      `,
      userId ? [userId, id] : [id]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Template not found' },
        { status: 404 }
      )
    }

    const row = rows[0] as TemplateRow
    const template = {
      id: row.id,
      name: row.name,
      description: row.description,
      slug: row.slug,
      toolId: row.tool_id,
      presetInputs: row.preset_inputs,
      category: row.category,
      tags: row.tags || [],
      isPublic: row.is_public,
      useCount: row.use_count,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }

    return NextResponse.json({
      success: true,
      data: template,
    })
  } catch (error) {
    console.error('Template GET error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/templates/[id]
 * Update a template
 */
export async function PATCH(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params
    const body = await request.json()

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      const templateIndex = SAMPLE_TEMPLATES.findIndex((t) => t.id === id || t.slug === id)

      if (templateIndex === -1) {
        return NextResponse.json(
          { success: false, error: 'Template not found' },
          { status: 404 }
        )
      }

      const updatedTemplate = {
        ...SAMPLE_TEMPLATES[templateIndex],
        ...body,
        updatedAt: new Date().toISOString(),
      }

      return NextResponse.json({
        success: true,
        data: updatedTemplate,
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

    const sets: string[] = []
    const params: unknown[] = []
    let i = 1

    if (body.name !== undefined) {
      sets.push(`name = $${i++}`)
      params.push(body.name)
    }
    if (body.description !== undefined) {
      sets.push(`description = $${i++}`)
      params.push(body.description ?? null)
    }
    if (body.presetInputs !== undefined) {
      sets.push(`preset_inputs = $${i++}`)
      params.push(body.presetInputs || {})
    }
    if (body.category !== undefined) {
      sets.push(`category = $${i++}`)
      params.push(body.category)
    }
    if (body.tags !== undefined) {
      sets.push(`tags = $${i++}`)
      params.push(Array.isArray(body.tags) ? body.tags : [])
    }
    if (body.isPublic !== undefined) {
      sets.push(`is_public = $${i++}`)
      params.push(!!body.isPublic)
    }

    if (sets.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No fields to update' },
        { status: 400 }
      )
    }

    sets.push('updated_at = NOW()')

    const rows = await sql.query(
      `
        UPDATE templates
        SET ${sets.join(', ')}
        WHERE id = $${i++} AND user_id = $${i++}
        RETURNING
          id,
          name,
          description,
          slug,
          tool_id,
          preset_inputs,
          category,
          tags,
          is_public,
          use_count,
          created_at,
          updated_at
      `,
      [...params, id, userId]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Template not found' },
        { status: 404 }
      )
    }

    const row = rows[0] as TemplateRow
    const template = {
      id: row.id,
      name: row.name,
      description: row.description,
      slug: row.slug,
      toolId: row.tool_id,
      presetInputs: row.preset_inputs,
      category: row.category,
      tags: row.tags || [],
      isPublic: row.is_public,
      useCount: row.use_count,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }

    return NextResponse.json({
      success: true,
      data: template,
    })
  } catch (error) {
    console.error('Template PATCH error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/templates/[id]
 * Delete a template
 */
export async function DELETE(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      return NextResponse.json({
        success: true,
        message: 'Template deleted',
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

    const rows = await sql.query(
      `DELETE FROM templates WHERE id = $1 AND user_id = $2 RETURNING id`,
      [id, userId]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Template not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Template deleted',
    })
  } catch (error) {
    console.error('Template DELETE error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
