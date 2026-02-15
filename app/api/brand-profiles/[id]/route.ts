import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../../lib/db'
import { requireClerkUserId } from '../../../../lib/clerk-auth'
import { SAMPLE_BRAND_PROFILES } from '../../../../types/brand'

type BrandProfileRow = {
  id: string
  name: string
  slug: string
  tone_keywords: string[] | null
  writing_style: string
  example_content: string | null
  industry: string | null
  target_audience: string | null
  preferred_words: string[] | null
  avoid_words: string[] | null
  brand_values: string[] | null
  content_themes: string[] | null
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

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

    const sql = getSqlOrNull()

    // If DB is not configured, return sample data
    if (!sql) {
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

    let userId: string
    try {
      userId = await requireClerkUserId()
    } catch {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Check if it's a UUID
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

    const rows = await sql.query(
      `
        SELECT
          id,
          name,
          slug,
          tone_keywords,
          writing_style,
          example_content,
          industry,
          target_audience,
          preferred_words,
          avoid_words,
          brand_values,
          content_themes,
          is_active,
          is_default,
          created_at,
          updated_at
        FROM brand_profiles
        WHERE user_id = $1 AND ${isUuid ? 'id' : 'slug'} = $2
        LIMIT 1
      `,
      [userId, id]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Brand profile not found' },
        { status: 404 }
      )
    }

    const row = rows[0] as BrandProfileRow
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

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
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
    if (body.toneKeywords !== undefined) {
      sets.push(`tone_keywords = $${i++}`)
      params.push(Array.isArray(body.toneKeywords) ? body.toneKeywords : [])
    }
    if (body.writingStyle !== undefined) {
      sets.push(`writing_style = $${i++}`)
      params.push(body.writingStyle)
    }
    if (body.exampleContent !== undefined) {
      sets.push(`example_content = $${i++}`)
      params.push(body.exampleContent ?? null)
    }
    if (body.industry !== undefined) {
      sets.push(`industry = $${i++}`)
      params.push(body.industry ?? null)
    }
    if (body.targetAudience !== undefined) {
      sets.push(`target_audience = $${i++}`)
      params.push(body.targetAudience ?? null)
    }
    if (body.preferredWords !== undefined) {
      sets.push(`preferred_words = $${i++}`)
      params.push(Array.isArray(body.preferredWords) ? body.preferredWords : [])
    }
    if (body.avoidWords !== undefined) {
      sets.push(`avoid_words = $${i++}`)
      params.push(Array.isArray(body.avoidWords) ? body.avoidWords : [])
    }
    if (body.brandValues !== undefined) {
      sets.push(`brand_values = $${i++}`)
      params.push(Array.isArray(body.brandValues) ? body.brandValues : [])
    }
    if (body.contentThemes !== undefined) {
      sets.push(`content_themes = $${i++}`)
      params.push(Array.isArray(body.contentThemes) ? body.contentThemes : [])
    }
    if (body.isActive !== undefined) {
      sets.push(`is_active = $${i++}`)
      params.push(!!body.isActive)
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
        UPDATE brand_profiles
        SET ${sets.join(', ')}
        WHERE id = $${i++} AND user_id = $${i++}
        RETURNING
          id,
          name,
          slug,
          tone_keywords,
          writing_style,
          example_content,
          industry,
          target_audience,
          preferred_words,
          avoid_words,
          brand_values,
          content_themes,
          is_active,
          is_default,
          created_at,
          updated_at
      `,
      [...params, id, userId]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Brand profile not found' },
        { status: 404 }
      )
    }

    const row = rows[0] as BrandProfileRow
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

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
      return NextResponse.json({
        success: true,
        message: 'Brand profile deleted',
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

    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

    const rows = await sql.query(
      `DELETE FROM brand_profiles WHERE ${isUuid ? 'id' : 'slug'} = $1 AND user_id = $2 RETURNING id`,
      [id, userId]
    )

    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Brand profile not found' },
        { status: 404 }
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
