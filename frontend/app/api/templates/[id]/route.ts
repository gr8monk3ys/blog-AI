import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../../lib/supabase'
import { SAMPLE_TEMPLATES } from '../../../../types/templates'
import type { Database } from '../../../../types/database'

type TemplateRow = Database['public']['Tables']['templates']['Row']

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

    // If Supabase is not configured, return sample data
    if (!isSupabaseConfigured()) {
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

    const supabase = getSupabase()

    // Try to find by ID first, then by slug
    let query = supabase.from('templates').select('*')

    // Check if it's a UUID
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

    if (isUuid) {
      query = query.eq('id', id)
    } else {
      query = query.eq('slug', id)
    }

    const { data, error } = await query.single()

    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json(
          { success: false, error: 'Template not found' },
          { status: 404 }
        )
      }

      console.error('Error fetching template:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to fetch template' },
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

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
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

    const supabase = getSupabase()

    // Build update object
    const updates: Record<string, unknown> = {}
    if (body.name !== undefined) updates.name = body.name
    if (body.description !== undefined) updates.description = body.description
    if (body.presetInputs !== undefined) updates.preset_inputs = body.presetInputs
    if (body.category !== undefined) updates.category = body.category
    if (body.tags !== undefined) updates.tags = body.tags
    if (body.isPublic !== undefined) updates.is_public = body.isPublic

    const { data, error } = await supabase
      .from('templates')
      .update(updates as never)
      .eq('id', id)
      .select()
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json(
          { success: false, error: 'Template not found' },
          { status: 404 }
        )
      }

      console.error('Error updating template:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to update template' },
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

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      return NextResponse.json({
        success: true,
        message: 'Template deleted',
      })
    }

    const supabase = getSupabase()
    const { error } = await supabase.from('templates').delete().eq('id', id)

    if (error) {
      console.error('Error deleting template:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to delete template' },
        { status: 500 }
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
