import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../lib/supabase'
import { SAMPLE_BRAND_PROFILES } from '../../../types/brand'
import type { Database } from '../../../types/database'

type BrandProfileRow = Database['public']['Tables']['brand_profiles']['Row']

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
 * GET /api/brand-profiles
 * List all brand profiles
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const activeOnly = searchParams.get('activeOnly') === 'true'
    const limit = parseInt(searchParams.get('limit') || '50', 10)
    const offset = parseInt(searchParams.get('offset') || '0', 10)

    // If Supabase is not configured, return sample data
    if (!isSupabaseConfigured()) {
      let filteredProfiles = [...SAMPLE_BRAND_PROFILES]

      if (activeOnly) {
        filteredProfiles = filteredProfiles.filter((p) => p.isActive)
      }

      return NextResponse.json({
        success: true,
        data: filteredProfiles.slice(offset, offset + limit),
        total: filteredProfiles.length,
      })
    }

    const supabase = getSupabase()
    let query = supabase
      .from('brand_profiles')
      .select('*', { count: 'exact' })
      .order('is_default', { ascending: false })
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (activeOnly) {
      query = query.eq('is_active', true)
    }

    const { data, error, count } = await query

    if (error) {
      console.error('Error fetching brand profiles:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to fetch brand profiles' },
        { status: 500 }
      )
    }

    // Transform database rows to API format
    const profiles = (data as BrandProfileRow[] | null)?.map((row) => ({
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
    }))

    return NextResponse.json({
      success: true,
      data: profiles,
      total: count || 0,
    })
  } catch (error) {
    console.error('Brand profiles GET error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/brand-profiles
 * Create a new brand profile
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate required fields
    if (!body.name || !body.toneKeywords || body.toneKeywords.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Name and at least one tone keyword are required' },
        { status: 400 }
      )
    }

    // Generate slug from name
    const slug = generateSlug(body.name)

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      const newProfile = {
        id: `bp-${Date.now()}`,
        name: body.name,
        slug,
        toneKeywords: body.toneKeywords,
        writingStyle: body.writingStyle || 'balanced',
        exampleContent: body.exampleContent || null,
        industry: body.industry || null,
        targetAudience: body.targetAudience || null,
        preferredWords: body.preferredWords || [],
        avoidWords: body.avoidWords || [],
        brandValues: body.brandValues || [],
        contentThemes: body.contentThemes || [],
        isActive: true,
        isDefault: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      return NextResponse.json({
        success: true,
        data: newProfile,
      })
    }

    const supabase = getSupabase()
    const insertData: Database['public']['Tables']['brand_profiles']['Insert'] = {
      name: body.name,
      slug,
      tone_keywords: body.toneKeywords,
      writing_style: body.writingStyle || 'balanced',
      example_content: body.exampleContent,
      industry: body.industry,
      target_audience: body.targetAudience,
      preferred_words: body.preferredWords || [],
      avoid_words: body.avoidWords || [],
      brand_values: body.brandValues || [],
      content_themes: body.contentThemes || [],
      user_hash: body.userHash || null,
    }
    const { data, error } = await supabase
      .from('brand_profiles')
      .insert(insertData as never)
      .select()
      .single()

    if (error) {
      console.error('Error creating brand profile:', error)

      // Handle unique constraint violation
      if (error.code === '23505') {
        return NextResponse.json(
          { success: false, error: 'A brand profile with this name already exists' },
          { status: 409 }
        )
      }

      return NextResponse.json(
        { success: false, error: 'Failed to create brand profile' },
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
    console.error('Brand profiles POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
