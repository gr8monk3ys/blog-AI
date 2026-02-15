import fs from 'fs'
import path from 'path'
import { getSqlOrNull } from './db'

export interface BlogPostMeta {
  title: string
  date: string
  excerpt: string
  slug: string
  tags: string[]
}

export interface BlogPost extends BlogPostMeta {
  body: string
}

const BLOG_DIR = path.join(process.cwd(), 'content', 'blog')

const FRONTMATTER_BOUNDARY = '---'

const parseFrontmatter = (raw: string): { data: Record<string, string>; body: string } => {
  if (!raw.startsWith(FRONTMATTER_BOUNDARY)) {
    return { data: {}, body: raw }
  }

  const endIndex = raw.indexOf(`${FRONTMATTER_BOUNDARY}\n`, FRONTMATTER_BOUNDARY.length)
  if (endIndex === -1) {
    return { data: {}, body: raw }
  }

  const frontmatterBlock = raw.slice(FRONTMATTER_BOUNDARY.length, endIndex).trim()
  const body = raw.slice(endIndex + FRONTMATTER_BOUNDARY.length + 1).trim()
  const data: Record<string, string> = {}

  frontmatterBlock.split('\n').forEach((line) => {
    const [key, ...rest] = line.split(':')
    if (!key || rest.length === 0) return
    data[key.trim()] = rest.join(':').trim()
  })

  return { data, body }
}

const parseTags = (value: string | undefined): string[] => {
  if (!value) return []
  const trimmed = value.trim()
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    return trimmed
      .slice(1, -1)
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
  }
  return trimmed
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

const buildExcerpt = (body: string, fallbackLength = 160): string => {
  const text = body
    .replace(/[#>*_`]/g, '')
    .replace(/\n+/g, ' ')
    .trim()

  if (text.length <= fallbackLength) return text
  return `${text.slice(0, fallbackLength).trim()}…`
}

export const loadBlogPosts = async (): Promise<BlogPostMeta[]> => {
  const cmsPosts = await loadBlogPostsFromDb()
  if (cmsPosts.length > 0) {
    return cmsPosts
  }

  try {
    const files = await fs.promises.readdir(BLOG_DIR)
    const markdownFiles = files.filter((file) => file.endsWith('.md') || file.endsWith('.mdx'))

    const posts = await Promise.all(
      markdownFiles.map(async (file) => {
        const fullPath = path.join(BLOG_DIR, file)
        const raw = await fs.promises.readFile(fullPath, 'utf8')
        const { data, body } = parseFrontmatter(raw)
        const slug = data.slug || file.replace(/\.(md|mdx)$/, '')

        return {
          title: data.title || slug.replace(/-/g, ' '),
          date: data.date || new Date().toISOString(),
          excerpt: data.excerpt || buildExcerpt(body),
          slug,
          tags: parseTags(data.tags),
        }
      })
    )

    return posts.sort((a, b) => (a.date < b.date ? 1 : -1))
  } catch {
    return []
  }
}

export const loadBlogPost = async (slug: string): Promise<BlogPost | null> => {
  const cmsPost = await loadBlogPostFromDb(slug)
  if (cmsPost) {
    return cmsPost
  }

  try {
    const candidates = [`${slug}.md`, `${slug}.mdx`]
    const target = candidates.find((file) =>
      fs.existsSync(path.join(BLOG_DIR, file))
    )
    if (!target) return null

    const raw = await fs.promises.readFile(path.join(BLOG_DIR, target), 'utf8')
    const { data, body } = parseFrontmatter(raw)

    return {
      title: data.title || slug.replace(/-/g, ' '),
      date: data.date || new Date().toISOString(),
      excerpt: data.excerpt || buildExcerpt(body),
      slug: data.slug || slug,
      tags: parseTags(data.tags),
      body,
    }
  } catch {
    return null
  }
}

const loadBlogPostsFromDb = async (): Promise<BlogPostMeta[]> => {
  const sql = getSqlOrNull()
  if (!sql) return []

  try {
    const rows = await sql.query(
      `
        SELECT
          title,
          slug,
          excerpt,
          body,
          tags,
          published_at,
          updated_at,
          created_at
        FROM blog_posts
        WHERE status = 'published'
        ORDER BY published_at DESC NULLS LAST
      `
    )

    if (!rows || rows.length === 0) return []

    return (rows as any[]).map((post) => ({
      title: post.title,
      date: post.published_at || post.updated_at || post.created_at,
      excerpt: post.excerpt || '',
      slug: post.slug,
      tags: post.tags || [],
    }))
  } catch {
    return []
  }
}

const loadBlogPostFromDb = async (slug: string): Promise<BlogPost | null> => {
  const sql = getSqlOrNull()
  if (!sql) return null

  try {
    const rows = await sql.query(
      `
        SELECT
          title,
          slug,
          excerpt,
          body,
          tags,
          published_at,
          updated_at,
          created_at
        FROM blog_posts
        WHERE slug = $1 AND status = 'published'
        LIMIT 1
      `,
      [slug]
    )

    if (!rows || rows.length === 0) return null

    const data = rows[0] as any
    return {
      title: data.title,
      date: data.published_at || data.updated_at || data.created_at,
      excerpt: data.excerpt || '',
      slug: data.slug,
      tags: data.tags || [],
      body: data.body,
    }
  } catch {
    return null
  }
}
