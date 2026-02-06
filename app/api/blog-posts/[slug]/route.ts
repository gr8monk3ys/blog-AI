import { NextRequest, NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured, isNoRowsError } from '../../../../lib/supabase'

const getAdminKey = () => process.env.BLOG_ADMIN_KEY

const isAuthorized = (request: Request) => {
  const adminKey = getAdminKey()
  if (!adminKey) return false

  const headerKey =
    request.headers.get('x-admin-key') ||
    request.headers.get('authorization')?.replace('Bearer ', '')

  return headerKey === adminKey
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const resolvedParams = await params
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 503 })
  }

  const supabase = getSupabase()
  const { data, error } = await supabase
    .from('blog_posts')
    .select('*')
    .eq('slug', resolvedParams.slug)
    .single()

  if (error) {
    if (isNoRowsError(error)) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 })
    }
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ data })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const resolvedParams = await params
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 503 })
  }

  const supabase = getSupabase()
  const { error } = await supabase.from('blog_posts').delete().eq('slug', resolvedParams.slug)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ success: true })
}
