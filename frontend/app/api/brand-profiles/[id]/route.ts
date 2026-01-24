import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../../lib/supabase'
import { SAMPLE_BRAND_PROFILES } from '../../../../types/brand'
import type { Database } from '../../../../types/database'

type BrandProfileRow = Database['public']['Tables']['brand_profiles']['Row']

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * GET /api/brand-profiles/[id]
 * Get a specific brand profile by ID or slug
 */
export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    // If Supabase is not configured, return sample data
    if (!isSupabaseConfigured()) {
      const profile = SAMPLE_BRAND_PROFILES.find((p) => p.id === id || p.slug === id)

      if (!profile) {
        return NextResponse.json(
          { success: false, error: 'Brand profile not found' },
          { status: 404 }
        )
      }

      return NextResponse.json({
        success: true,
        data: profile,
      })
    }

    const supabase = getSupabase()

    // Try to find by ID first, then by slug
    let query = supabase.from('brand_profiles').select('*')

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
          { success: false, error: 'Brand profile not found' },
          { status: 404 }
        )
      }

      console.error('Error fetching brand profile:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to fetch brand profile' },
        { status: 500 }
      )
    }

    const row = data as BrandProfileRow
    const profile = {
      id: row.id,
      name: row.name,
      slug: row.slug,
      toneKeywords: row.tone_keywords || [],
      writingStyle: row.writing_style,
      exampleContent: row.example_content,
      industry: row.industry,
      targetAudience: row.target_audience,
      preferredWords: row.preferred_words || [],
      avoidWords: row.avoid_words || [],
      brandValues: row.brand_values || [],
      contentThemes: row.content_themes || [],
      isActive: row.is_active,
      isDefault: row.is_default,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }

    return NextResponse.json({
      success: true,
      data: profile,
    })
  } catch (error) {
    console.error('Brand profile GET error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/brand-profiles/[id]
 * Update a brand profile
 */
export async function PATCH(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params
    const body = await request.json()

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      const profileIndex = SAMPLE_BRAND_PROFILES.findIndex((p) => p.id === id || p.slug === id)

      if (profileIndex === -1) {
        return NextResponse.json(
          { success: false, error: 'Brand profile not found' },
          { status: 404 }
        )
      }

      const updatedProfile = {
        ...SAMPLE_BRAND_PROFILES[profileIndex],
        ...body,
        updatedAt: new Date().toISOString(),
      }

      return NextResponse.json({
        success: true,
        data: updatedProfile,
      })
    }

    const supabase = getSupabase()

    // Build update object
    const updates: Record<string, unknown> = {}
    if (body.name !== undefined) updates.name = body.name
    if (body.toneKeywords !== undefined) updates.tone_keywords = body.toneKeywords
    if (body.writingStyle !== undefined) updates.writing_style = body.writingStyle
    if (body.exampleContent !== undefined) updates.example_content = body.exampleContent
    if (body.industry !== undefined) updates.industry = body.industry
    if (body.targetAudience !== undefined) updates.target_audience = body.targetAudience
    if (body.preferredWords !== undefined) updates.preferred_words = body.preferredWords
    if (body.avoidWords !== undefined) updates.avoid_words = body.avoidWords
    if (body.brandValues !== undefined) updates.brand_values = body.brandValues
    if (body.contentThemes !== undefined) updates.content_themes = body.contentThemes
    if (body.isActive !== undefined) updates.is_active = body.isActive

    const { data, error } = await supabase
      .from('brand_profiles')
      .update(updates as never)
      .eq('id', id)
      .select()
      .single()

    if (error) {
      if (error.code === 'PGRST116') {
        return NextResponse.json(
          { success: false, error: 'Brand profile not found' },
          { status: 404 }
        )
      }

      console.error('Error updating brand profile:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to update brand profile' },
        { status: 500 }
      )
    }

    const row = data as BrandProfileRow
    const profile = {
      id: row.id,
      name: row.name,
      slug: row.slug,
      toneKeywords: row.tone_keywords || [],
      writingStyle: row.writing_style,
      exampleContent: row.example_content,
      industry: row.industry,
      targetAudience: row.target_audience,
      preferredWords: row.preferred_words || [],
      avoidWords: row.avoid_words || [],
      brandValues: row.brand_values || [],
      contentThemes: row.content_themes || [],
      isActive: row.is_active,
      isDefault: row.is_default,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }

    return NextResponse.json({
      success: true,
      data: profile,
    })
  } catch (error) {
    console.error('Brand profile PATCH error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/brand-profiles/[id]
 * Delete a brand profile
 */
export async function DELETE(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      return NextResponse.json({
        success: true,
        message: 'Brand profile deleted',
      })
    }

    const supabase = getSupabase()
    const { error } = await supabase.from('brand_profiles').delete().eq('id', id)

    if (error) {
      console.error('Error deleting brand profile:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to delete brand profile' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Brand profile deleted',
    })
  } catch (error) {
    console.error('Brand profile DELETE error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
