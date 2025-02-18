import getBaseUrl from '../../lib/site-url'
import { loadBlogPosts } from '../../lib/blog-index'

const escapeXml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')

export async function GET() {
  const baseUrl = getBaseUrl()
  const posts = await loadBlogPosts()

  const items = posts
    .map((post) => {
      const url = `${baseUrl}/blog/${post.slug}`
      return `
        <item>
          <title>${escapeXml(post.title)}</title>
          <link>${url}</link>
          <guid>${url}</guid>
          <pubDate>${new Date(post.date).toUTCString()}</pubDate>
          <description>${escapeXml(post.excerpt)}</description>
        </item>
      `.trim()
    })
    .join('\n')

  const rss = `
    <?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Blog AI</title>
        <link>${baseUrl}/blog</link>
        <description>AI content strategy, SEO workflows, and scaling content with tools.</description>
        <language>en-us</language>
        ${items}
      </channel>
    </rss>
  `.trim()

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
    },
  })
}
