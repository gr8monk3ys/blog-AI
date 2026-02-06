import type { MetadataRoute } from 'next'
import getBaseUrl from '../lib/site-url'
import { loadBlogPosts } from '../lib/blog-index'
import { toolsApi, toFrontendTools } from '../lib/tools-api'
import { SAMPLE_TOOLS, TOOL_CATEGORIES, type Tool, type ToolCategory } from '../types/tools'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = getBaseUrl()
  const [blogPosts, tools] = await Promise.all([loadBlogPosts(), loadTools()])

  const corePages: MetadataRoute.Sitemap = [
    { url: `${baseUrl}/`, lastModified: new Date() },
    { url: `${baseUrl}/tools`, lastModified: new Date() },
    { url: `${baseUrl}/tool-directory`, lastModified: new Date() },
    { url: `${baseUrl}/templates`, lastModified: new Date() },
    { url: `${baseUrl}/pricing`, lastModified: new Date() },
    { url: `${baseUrl}/blog`, lastModified: new Date() },
  ]

  const blogPages: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: new Date(post.date),
  }))

  const toolPages: MetadataRoute.Sitemap = tools.map((tool) => ({
    url: `${baseUrl}/tools/${tool.slug}`,
    lastModified: new Date(),
  }))

  const categoryPages: MetadataRoute.Sitemap = (Object.keys(TOOL_CATEGORIES) as ToolCategory[]).map(
    (category) => ({
      url: `${baseUrl}/tools/category/${category}`,
      lastModified: new Date(),
    })
  )

  return [...corePages, ...blogPages, ...toolPages, ...categoryPages]
}

async function loadTools(): Promise<Tool[]> {
  try {
    const response = await toolsApi.listTools({
      limit: 1000,
      include_premium: true,
      include_beta: true,
    })
    const tools = toFrontendTools(response.tools || [])
    return tools.length > 0 ? tools : SAMPLE_TOOLS
  } catch {
    return SAMPLE_TOOLS
  }
}
