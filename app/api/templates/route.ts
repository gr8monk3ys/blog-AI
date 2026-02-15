import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../lib/db'
import { requireClerkUserId } from '../../../lib/clerk-auth'
import { SAMPLE_TEMPLATES } from '../../../types/templates'

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

/**
 * Generate a URL-friendly slug from a name
 */
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

/**
 * GET /api/templates
 * List all public templates with optional filtering
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get('category')
    const toolId = searchParams.get('toolId')
    const search = searchParams.get('search')
    const limit = parseInt(searchParams.get('limit') || '50', 10)
    const offset = parseInt(searchParams.get('offset') || '0', 10)

    const sql = getSqlOrNull()

    // If DB is not configured, return sample data
    if (!sql) {
      let filteredTemplates = [...SAMPLE_TEMPLATES]

      if (category && category !== 'all') {
        filteredTemplates = filteredTemplates.filter((t) => t.category === category)
      }

      if (toolId) {
        filteredTemplates = filteredTemplates.filter((t) => t.toolId === toolId)
      }

      if (search) {
        const searchLower = search.toLowerCase()
        filteredTemplates = filteredTemplates.filter(
          (t) =>
            t.name.toLowerCase().includes(searchLower) ||
            t.description?.toLowerCase().includes(searchLower) ||
            t.tags.some((tag) => tag.toLowerCase().includes(searchLower))
        )
      }

      return NextResponse.json({
        success: true,
        data: filteredTemplates.slice(offset, offset + limit),
        total: filteredTemplates.length,
      })
    }

    const where: string[] = ['is_public = true']
    const params: unknown[] = []
    let i = 1

    if (category && category !== 'all') {
      where.push(`category = $${i++}`)
      params.push(category)
    }

    if (toolId) {
      where.push(`tool_id = $${i++}`)
      params.push(toolId)
    }

    if (search) {
      where.push(`(name ILIKE $${i++} OR description ILIKE $${i++})`)
      const pattern = `%${search}%`
      params.push(pattern, pattern)
    }

    const whereSql = where.length > 0 ? `WHERE ${where.join(' AND ')}` : ''

    const countRows = await sql.query(
      `SELECT COUNT(*)::int AS count FROM templates ${whereSql}`,
      params
    )
    const total = Number((countRows?.[0] as { count?: unknown } | undefined)?.count ?? 0)

    const dataRows = await sql.query(
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
        ${whereSql}
        ORDER BY use_count DESC
        LIMIT $${i++}
        OFFSET $${i++}
      `,
      [...params, limit, offset]
    )

    if (!dataRows) {
      return NextResponse.json(
        { success: false, error: 'Failed to fetch templates' },
        { status: 500 }
      )
    }

    // Transform database rows to API format
    const templates = (dataRows as TemplateRow[]).map((row) => ({
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
    }))

    return NextResponse.json({
      success: true,
      data: templates,
      total,
    })
  } catch (error) {
    console.error('Templates GET error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/templates
 * Create a new template
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate required fields
    if (!body.name || !body.toolId || !body.category) {
      return NextResponse.json(
        { success: false, error: 'Name, toolId, and category are required' },
        { status: 400 }
      )
    }

    // Generate slug from name
    const slug = generateSlug(body.name)

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      const newTemplate = {
        id: `tpl-${Date.now()}`,
        name: body.name,
        description: body.description || null,
        slug,
        toolId: body.toolId,
        presetInputs: body.presetInputs || {},
        category: body.category,
        tags: body.tags || [],
        isPublic: body.isPublic ?? true,
        useCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      return NextResponse.json({
        success: true,
        data: newTemplate,
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

    let row: TemplateRow
    try {
      const rows = await sql.query(
        `
          INSERT INTO templates (
            name,
            description,
            slug,
            tool_id,
            preset_inputs,
            category,
            tags,
            is_public,
            user_id
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
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
        [
          body.name,
          body.description ?? null,
          slug,
          body.toolId,
          body.presetInputs || {},
          body.category,
          Array.isArray(body.tags) ? body.tags : [],
          body.isPublic ?? true,
          userId,
        ]
      )

      if (!rows || rows.length === 0) {
        return NextResponse.json(
          { success: false, error: 'Failed to create template' },
          { status: 500 }
        )
      }

      row = rows[0] as TemplateRow
    } catch (e: any) {
      // Unique constraint violation (e.g., slug)
      if (e?.code === '23505') {
        return NextResponse.json(
          { success: false, error: 'A template with this name already exists' },
          { status: 409 }
        )
      }

      console.error('Error creating template:', e)
      return NextResponse.json(
        { success: false, error: 'Failed to create template' },
        { status: 500 }
      )
    }

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
    console.error('Templates POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
