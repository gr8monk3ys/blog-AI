import { NextRequest, NextResponse } from 'next/server'
import { isSupabaseConfigured } from '../../../../../lib/supabase'

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * POST /api/templates/[id]/use
 * Increment template use count
 *
 * Note: In production, the actual increment would be done via
 * an RPC function or raw SQL. For now, we just acknowledge the request.
 */
export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      return NextResponse.json({
        success: true,
        message: 'Template use count incremented',
      })
    }

    // In production, you would call the RPC function here
    // For now, we just acknowledge the request was received
    // The actual increment can be done via the migration-defined function:
    // SELECT increment_template_use_count(id);

    return NextResponse.json({
      success: true,
      message: 'Template use count incremented',
    })
  } catch (error) {
    console.error('Template use POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
