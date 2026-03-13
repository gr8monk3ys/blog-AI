import { NextResponse } from 'next/server'
import { loadBlogPosts } from '../../../lib/blog-index'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const limitParam = searchParams.get('limit')
  const limit = limitParam ? Number(limitParam) : 3

  const posts = await loadBlogPosts()
  const trimmedPosts = Number.isFinite(limit) && limit > 0 ? posts.slice(0, limit) : posts

  return NextResponse.json({ data: trimmedPosts })
}
