import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import SiteHeader from '../../../components/SiteHeader'
import SiteFooter from '../../../components/SiteFooter'
import { loadBlogPost } from '../../../lib/blog-index'
import getBaseUrl from '../../../lib/site-url'

interface BlogPostPageProps {
  params: Promise<{ slug: string }>
}

type MarkdownBlock =
  | { type: 'heading-2' | 'heading-3' | 'heading-4' | 'paragraph'; key: string; text: string }
  | { type: 'list'; key: string; items: Array<{ key: string; text: string }> }

export async function generateMetadata({ params }: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params
  const post = await loadBlogPost(slug)
  if (!post) return {}

  const canonicalPath = `/blog/${post.slug}`
  const canonicalUrl = `${getBaseUrl()}${canonicalPath}`

  return {
    title: post.title,
    description: post.excerpt,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      type: 'article',
      url: canonicalUrl,
      title: post.title,
      description: post.excerpt,
    },
    twitter: {
      card: 'summary',
      title: post.title,
      description: post.excerpt,
    },
  }
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params
  const post = await loadBlogPost(slug)

  if (!post) {
    notFound()
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-neutral-50 via-white to-neutral-100">
      <SiteHeader />

      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href="/blog" className="text-xs text-neutral-500 hover:text-amber-700">
            Back to blog
          </Link>
          <h1 className="mt-3 text-3xl sm:text-4xl font-semibold text-neutral-900 font-serif">
            {post.title}
          </h1>
          <div className="mt-2 text-xs text-neutral-500">{formatDisplayDate(post.date)}</div>
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="space-y-6 text-neutral-700">
          <MarkdownBlocks body={post.body} />
        </div>

        {post.tags.length > 0 && (
          <div className="mt-8 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-1 rounded-full bg-neutral-100 text-neutral-600"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </article>

      <SiteFooter />
    </main>
  )
}

function MarkdownBlocks({ body }: { body: string }) {
  return parseMarkdownBlocks(body).map((block) => {
    if (block.type === 'heading-2') {
      return (
        <h2 key={block.key} className="text-2xl font-semibold text-neutral-900 font-serif">
          {block.text}
        </h2>
      )
    }

    if (block.type === 'heading-3') {
      return (
        <h3 key={block.key} className="text-xl font-semibold text-neutral-900 font-serif">
          {block.text}
        </h3>
      )
    }

    if (block.type === 'heading-4') {
      return (
        <h4 key={block.key} className="text-lg font-semibold text-neutral-900 font-serif">
          {block.text}
        </h4>
      )
    }

    if (block.type === 'list') {
      return (
        <ul key={block.key} className="list-disc list-inside space-y-1 text-sm text-neutral-600">
          {block.items.map((item) => (
            <li key={item.key}>{item.text}</li>
          ))}
        </ul>
      )
    }

    return (
      <p key={block.key} className="text-sm text-neutral-600">
        {block.text}
      </p>
    )
  })
}

function parseMarkdownBlocks(body: string): MarkdownBlock[] {
  const blocks = createStableEntries(
    body.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean),
    'block'
  )

  return blocks.map(({ key, value: block }) => {
    if (block.startsWith('# ')) {
      return { type: 'heading-2', key, text: block.replace(/^# /, '').trim() }
    }

    if (block.startsWith('## ')) {
      return { type: 'heading-3', key, text: block.replace(/^## /, '').trim() }
    }

    if (block.startsWith('### ')) {
      return { type: 'heading-4', key, text: block.replace(/^### /, '').trim() }
    }

    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean)
    const isList = lines.length > 1 && lines.every((line) => line.startsWith('- '))

    if (isList) {
      return {
        type: 'list',
        key,
        items: createStableEntries(lines.map((line) => line.replace(/^- /, '')), `${key}-item`).map(
          ({ key: itemKey, value }) => ({
            key: itemKey,
            text: value,
          })
        ),
      }
    }

    return {
      type: 'paragraph',
      key,
      text: block.replace(/\n+/g, ' '),
    }
  })
}

function createStableEntries(values: string[], prefix: string) {
  const counts = new Map<string, number>()

  return values.map((value) => {
    const normalized = value.trim().toLowerCase() || 'item'
    const occurrence = (counts.get(normalized) ?? 0) + 1
    counts.set(normalized, occurrence)

    return {
      key: `${prefix}-${normalized.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'item'}-${occurrence}`,
      value,
    }
  })
}

function formatDisplayDate(dateValue: string): string {
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return dateValue
  return parsed.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
