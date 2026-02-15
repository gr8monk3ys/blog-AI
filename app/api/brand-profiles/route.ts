import { NextRequest, NextResponse } from 'next/server'
import { getSqlOrNull } from '../../../lib/db'
import { requireClerkUserId } from '../../../lib/clerk-auth'
import { SAMPLE_BRAND_PROFILES } from '../../../types/brand'

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

    const sql = getSqlOrNull()

    // If DB is not configured, return sample data
    if (!sql) {
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

    let userId: string
    try {
      userId = await requireClerkUserId()
    } catch {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const where: string[] = ['user_id = $1']
    const params: unknown[] = [userId]
    let i = 2

    if (activeOnly) {
      where.push('is_active = true')
    }

    const whereSql = `WHERE ${where.join(' AND ')}`

    const countRows = await sql.query(
      `SELECT COUNT(*)::int AS count FROM brand_profiles ${whereSql}`,
      params
    )
    const total = Number((countRows?.[0] as { count?: unknown } | undefined)?.count ?? 0)

    const dataRows = await sql.query(
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
        ${whereSql}
        ORDER BY is_default DESC, created_at DESC
        LIMIT $${i++}
        OFFSET $${i++}
      `,
      [...params, limit, offset]
    )

    if (!dataRows) {
      return NextResponse.json(
        { success: false, error: 'Failed to fetch brand profiles' },
        { status: 500 }
      )
    }

    // Transform database rows to API format
    const profiles = (dataRows as BrandProfileRow[]).map((row) => ({
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
      total,
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

    const sql = getSqlOrNull()

    // If DB is not configured, return mock response
    if (!sql) {
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

    let userId: string
    try {
      userId = await requireClerkUserId()
    } catch {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      )
    }

    let row: BrandProfileRow
    try {
      const rows = await sql.query(
        `
          INSERT INTO brand_profiles (
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
            user_id
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
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
        [
          body.name,
          slug,
          Array.isArray(body.toneKeywords) ? body.toneKeywords : [],
          body.writingStyle || 'balanced',
          body.exampleContent ?? null,
          body.industry ?? null,
          body.targetAudience ?? null,
          Array.isArray(body.preferredWords) ? body.preferredWords : [],
          Array.isArray(body.avoidWords) ? body.avoidWords : [],
          Array.isArray(body.brandValues) ? body.brandValues : [],
          Array.isArray(body.contentThemes) ? body.contentThemes : [],
          userId,
        ]
      )

      if (!rows || rows.length === 0) {
        return NextResponse.json(
          { success: false, error: 'Failed to create brand profile' },
          { status: 500 }
        )
      }

      row = rows[0] as BrandProfileRow
    } catch (e: any) {
      // Unique constraint violation (e.g., slug)
      if (e?.code === '23505') {
        return NextResponse.json(
          { success: false, error: 'A brand profile with this name already exists' },
          { status: 409 }
        )
      }

      console.error('Error creating brand profile:', e)
      return NextResponse.json(
        { success: false, error: 'Failed to create brand profile' },
        { status: 500 }
      )
    }

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
