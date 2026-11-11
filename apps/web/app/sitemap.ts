import type { MetadataRoute } from 'next'
import getBaseUrl from '../lib/site-url'
import { loadBlogPosts } from '../lib/blog-index'
import { TOOL_CATEGORIES, type ToolCategory } from '../types/tools'

// Only public pages belong here. /templates and /tools/<slug> require sign-in, so a
// crawler gets no page from them (production answered 404 for all 30 of them).
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = getBaseUrl()
  const blogPosts = await loadBlogPosts()

  const corePages: MetadataRoute.Sitemap = [
    { url: `${baseUrl}/`, lastModified: new Date() },
    { url: `${baseUrl}/tools`, lastModified: new Date() },
    { url: `${baseUrl}/tool-directory`, lastModified: new Date() },
    { url: `${baseUrl}/pricing`, lastModified: new Date() },
    { url: `${baseUrl}/blog`, lastModified: new Date() },
  ]

  const blogPages: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: new Date(post.date),
  }))

  const categoryPages: MetadataRoute.Sitemap = (Object.keys(TOOL_CATEGORIES) as ToolCategory[]).map(
    (category) => ({
      url: `${baseUrl}/tools/category/${category}`,
      lastModified: new Date(),
    })
  )

  return [...corePages, ...blogPages, ...categoryPages]
}
