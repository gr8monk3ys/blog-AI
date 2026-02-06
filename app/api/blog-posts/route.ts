import { NextResponse } from 'next/server'
import { getSupabase, isSupabaseConfigured } from '../../../lib/supabase'

const getAdminKey = () => process.env.BLOG_ADMIN_KEY

const isAuthorized = (request: Request) => {
  const adminKey = getAdminKey()
  if (!adminKey) return false

  const headerKey =
    request.headers.get('x-admin-key') ||
    request.headers.get('authorization')?.replace('Bearer ', '')

  return headerKey === adminKey
}

export async function GET(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 503 })
  }

  const supabase = getSupabase() as any
  const { data, error } = await supabase
    .from('blog_posts')
    .select('id, title, slug, excerpt, tags, status, published_at, updated_at, created_at')
    .order('published_at', { ascending: false, nullsFirst: false })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ data })
}

export async function POST(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 503 })
  }

  const payload = await request.json()

  if (!payload?.title || !payload?.slug || !payload?.body) {
    return NextResponse.json(
      { error: 'Missing required fields: title, slug, body' },
      { status: 400 }
    )
  }

  const supabase = getSupabase() as any
  const { data, error } = await supabase
    .from('blog_posts')
    .upsert(
      {
        title: payload.title,
        slug: payload.slug,
        excerpt: payload.excerpt || null,
        body: payload.body,
        tags: Array.isArray(payload.tags) ? payload.tags : [],
        status: payload.status || 'draft',
        published_at: payload.published_at || null,
        cover_image: payload.cover_image || null,
        seo_title: payload.seo_title || null,
        seo_description: payload.seo_description || null,
      },
      { onConflict: 'slug' }
    )
    .select()
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ data })
}
