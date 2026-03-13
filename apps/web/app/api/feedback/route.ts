import { NextRequest, NextResponse } from 'next/server'

import { getClerkUserIdOrNull } from '../../../lib/clerk-auth'
import { getSqlOrNull } from '../../../lib/db'
import { FEEDBACK_TAGS, type FeedbackTag, type FeedbackTagStat } from '../../../types/feedback'

const MAX_FEEDBACK_TEXT_LENGTH = 1000
const MAX_CONTENT_ID_LENGTH = 256
const MIN_RATING = 1
const MAX_RATING = 5

const allowedTagSet = new Set<string>(FEEDBACK_TAGS)

function isValidTag(tag: string): tag is FeedbackTag {
  return allowedTagSet.has(tag)
}

// ---------------------------------------------------------------------------
// In-memory fallback store (used when DATABASE_URL is not configured)
// ---------------------------------------------------------------------------

interface InMemoryFeedback {
  id: string
  user_id: string | null
  content_id: string
  rating: number
  tags: FeedbackTag[]
  feedback_text: string | null
  created_at: string
}

const memoryStore: InMemoryFeedback[] = []

// ---------------------------------------------------------------------------
// POST /api/feedback  --  Submit feedback for generated content
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid JSON' },
      { status: 400 }
    )
  }

  // --- Validate required fields ---

  const { content_id, rating, tags, feedback_text } = body as {
    content_id?: unknown
    rating?: unknown
    tags?: unknown
    feedback_text?: unknown
  }

  if (typeof content_id !== 'string' || content_id.trim().length === 0) {
    return NextResponse.json(
      { success: false, error: 'content_id is required and must be a non-empty string' },
      { status: 400 }
    )
  }

  if (content_id.length > MAX_CONTENT_ID_LENGTH) {
    return NextResponse.json(
      { success: false, error: `content_id must be at most ${MAX_CONTENT_ID_LENGTH} characters` },
      { status: 400 }
    )
  }

  if (typeof rating !== 'number' || !Number.isInteger(rating) || rating < MIN_RATING || rating > MAX_RATING) {
    return NextResponse.json(
      { success: false, error: `rating must be an integer between ${MIN_RATING} and ${MAX_RATING}` },
      { status: 400 }
    )
  }

  if (!Array.isArray(tags) || !tags.every((t): t is string => typeof t === 'string' && isValidTag(t))) {
    return NextResponse.json(
      { success: false, error: `tags must be an array of allowed values: ${FEEDBACK_TAGS.join(', ')}` },
      { status: 400 }
    )
  }

  if (feedback_text !== undefined && feedback_text !== null) {
    if (typeof feedback_text !== 'string') {
      return NextResponse.json(
        { success: false, error: 'feedback_text must be a string' },
        { status: 400 }
      )
    }
    if (feedback_text.length > MAX_FEEDBACK_TEXT_LENGTH) {
      return NextResponse.json(
        { success: false, error: `feedback_text must be at most ${MAX_FEEDBACK_TEXT_LENGTH} characters` },
        { status: 400 }
      )
    }
  }

  const validatedTags = tags as FeedbackTag[]
  const validatedText = typeof feedback_text === 'string' && feedback_text.trim().length > 0
    ? feedback_text.trim()
    : null

  try {
    // Allow anonymous feedback -- userId may be null for unauthenticated users.
    let userId: string | null = null
    try {
      userId = await getClerkUserIdOrNull()
    } catch {
      // Auth not configured or unavailable -- proceed without user_id.
    }

    const sql = getSqlOrNull()

    if (!sql) {
      // Fallback: store in memory
      const entry: InMemoryFeedback = {
        id: `fb-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        user_id: userId,
        content_id: content_id as string,
        rating: rating as number,
        tags: validatedTags,
        feedback_text: validatedText,
        created_at: new Date().toISOString(),
      }
      memoryStore.push(entry)

      return NextResponse.json({
        success: true,
        data: { id: entry.id, created_at: entry.created_at },
      })
    }

    const rows = await sql.query(
      `
        INSERT INTO content_feedback (
          user_id,
          content_id,
          rating,
          tags,
          feedback_text
        ) VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at
      `,
      [userId, content_id, rating, validatedTags, validatedText]
    )

    const row = rows?.[0] as { id: string; created_at: string } | undefined
    if (!row) {
      return NextResponse.json(
        { success: false, error: 'Failed to store feedback' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      data: { id: row.id, created_at: row.created_at },
    })
  } catch (error) {
    console.error('Feedback POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// ---------------------------------------------------------------------------
// GET /api/feedback?content_id=...  --  Retrieve feedback stats
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = new URL(request.url)
  const contentId = searchParams.get('content_id')

  if (!contentId) {
    return NextResponse.json(
      { success: false, error: 'content_id query parameter is required' },
      { status: 400 }
    )
  }

  if (contentId.length > MAX_CONTENT_ID_LENGTH) {
    return NextResponse.json(
      { success: false, error: `content_id must be at most ${MAX_CONTENT_ID_LENGTH} characters` },
      { status: 400 }
    )
  }

  try {
    const sql = getSqlOrNull()

    if (!sql) {
      // In-memory fallback
      const entries = memoryStore.filter((e) => e.content_id === contentId)

      if (entries.length === 0) {
        return NextResponse.json({
          success: true,
          data: {
            content_id: contentId,
            average_rating: 0,
            total_ratings: 0,
            rating_distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
            common_tags: [],
          },
        })
      }

      const totalRatings = entries.length
      const sumRatings = entries.reduce((acc, e) => acc + e.rating, 0)
      const averageRating = Math.round((sumRatings / totalRatings) * 10) / 10

      const distribution: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
      entries.forEach((e) => {
        distribution[e.rating] = (distribution[e.rating] ?? 0) + 1
      })

      const tagCounts = new Map<FeedbackTag, number>()
      entries.forEach((e) => {
        e.tags.forEach((tag) => {
          tagCounts.set(tag, (tagCounts.get(tag) ?? 0) + 1)
        })
      })

      const commonTags: FeedbackTagStat[] = Array.from(tagCounts.entries())
        .map(([tag, count]) => ({ tag, count }))
        .sort((a, b) => b.count - a.count)

      return NextResponse.json({
        success: true,
        data: {
          content_id: contentId,
          average_rating: averageRating,
          total_ratings: totalRatings,
          rating_distribution: distribution,
          common_tags: commonTags,
        },
      })
    }

    // Database path
    const [statsRows, tagRows] = await Promise.all([
      sql.query(
        `
          SELECT
            COUNT(*)::int AS total_ratings,
            ROUND(AVG(rating)::numeric, 1)::float AS average_rating,
            COUNT(*) FILTER (WHERE rating = 1)::int AS r1,
            COUNT(*) FILTER (WHERE rating = 2)::int AS r2,
            COUNT(*) FILTER (WHERE rating = 3)::int AS r3,
            COUNT(*) FILTER (WHERE rating = 4)::int AS r4,
            COUNT(*) FILTER (WHERE rating = 5)::int AS r5
          FROM content_feedback
          WHERE content_id = $1
        `,
        [contentId]
      ),
      sql.query(
        `
          SELECT tag, COUNT(*)::int AS count
          FROM content_feedback, UNNEST(tags) AS tag
          WHERE content_id = $1
          GROUP BY tag
          ORDER BY count DESC
        `,
        [contentId]
      ),
    ])

    const stats = statsRows?.[0] as {
      total_ratings: number
      average_rating: number
      r1: number
      r2: number
      r3: number
      r4: number
      r5: number
    } | undefined

    const commonTags: FeedbackTagStat[] = ((tagRows as Array<{ tag: string; count: number }>) ?? [])
      .filter((r) => isValidTag(r.tag))
      .map((r) => ({ tag: r.tag as FeedbackTag, count: r.count }))

    return NextResponse.json({
      success: true,
      data: {
        content_id: contentId,
        average_rating: stats?.average_rating ?? 0,
        total_ratings: stats?.total_ratings ?? 0,
        rating_distribution: {
          1: stats?.r1 ?? 0,
          2: stats?.r2 ?? 0,
          3: stats?.r3 ?? 0,
          4: stats?.r4 ?? 0,
          5: stats?.r5 ?? 0,
        },
        common_tags: commonTags,
      },
    })
  } catch (error) {
    console.error('Feedback GET error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
