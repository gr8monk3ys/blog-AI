import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../lib/supabase'
import { SAMPLE_TEMPLATES } from '../../../types/templates'
import type { Database } from '../../../types/database'

type TemplateRow = Database['public']['Tables']['templates']['Row']

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

    // If Supabase is not configured, return sample data
    if (!isSupabaseConfigured()) {
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

    const supabase = getSupabase()
    let query = supabase
      .from('templates')
      .select('*', { count: 'exact' })
      .eq('is_public', true)
      .order('use_count', { ascending: false })
      .range(offset, offset + limit - 1)

    if (category && category !== 'all') {
      query = query.eq('category', category)
    }

    if (toolId) {
      query = query.eq('tool_id', toolId)
    }

    if (search) {
      query = query.or(`name.ilike.%${search}%,description.ilike.%${search}%`)
    }

    const { data, error, count } = await query

    if (error) {
      console.error('Error fetching templates:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to fetch templates' },
        { status: 500 }
      )
    }

    // Transform database rows to API format
    const templates = (data as TemplateRow[] | null)?.map((row) => ({
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
      total: count || 0,
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

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
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

    const supabase = getSupabase()
    const insertData: Database['public']['Tables']['templates']['Insert'] = {
      name: body.name,
      description: body.description,
      slug,
      tool_id: body.toolId,
      preset_inputs: body.presetInputs || {},
      category: body.category,
      tags: body.tags || [],
      is_public: body.isPublic ?? true,
      user_hash: body.userHash || null,
    }
    const { data, error } = await supabase
      .from('templates')
      .insert(insertData as never)
      .select()
      .single()

    if (error) {
      console.error('Error creating template:', error)

      // Handle unique constraint violation
      if (error.code === '23505') {
        return NextResponse.json(
          { success: false, error: 'A template with this name already exists' },
          { status: 409 }
        )
      }

      return NextResponse.json(
        { success: false, error: 'Failed to create template' },
        { status: 500 }
      )
    }

    const row = data as TemplateRow
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
