import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../../../lib/supabase'

interface RouteContext {
  params: Promise<{ id: string }>
}

/**
 * POST /api/brand-profiles/[id]/default
 * Set a brand profile as the default
 */
export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { id } = await context.params
    const body = await request.json()
    const userHash = body.userHash

    // If Supabase is not configured, return mock response
    if (!isSupabaseConfigured()) {
      return NextResponse.json({
        success: true,
        message: 'Brand profile set as default',
      })
    }

    const supabase = getSupabase()

    // Manually update default status since RPC might not be available
    // First, unset all defaults for this user
    await supabase
      .from('brand_profiles')
      .update({ is_default: false } as never)
      .eq('user_hash', userHash || '')
      .neq('id', id)

    // Then set this profile as default
    const { error } = await supabase
      .from('brand_profiles')
      .update({ is_default: true } as never)
      .eq('id', id)

    if (error) {
      console.error('Error setting default brand profile:', error)
      return NextResponse.json(
        { success: false, error: 'Failed to set default profile' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Brand profile set as default',
    })
  } catch (error) {
    console.error('Brand profile default POST error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
