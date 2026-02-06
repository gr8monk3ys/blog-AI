import { notFound } from 'next/navigation'
import Link from 'next/link'
import { loadBlogPost } from '../../../lib/blog-index'

interface BlogPostPageProps {
  params: { slug: string }
}

export async function generateMetadata({ params }: BlogPostPageProps) {
  const post = await loadBlogPost(params.slug)
  if (!post) return {}

  return {
    title: `${post.title} | Blog AI`,
    description: post.excerpt,
  }
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const post = await loadBlogPost(params.slug)

  if (!post) {
    notFound()
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-neutral-50 via-white to-neutral-100">
      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href="/blog" className="text-xs text-neutral-500 hover:text-indigo-700">
            Back to blog
          </Link>
          <h1 className="mt-3 text-3xl sm:text-4xl font-semibold text-neutral-900 font-serif">
            {post.title}
          </h1>
          <div className="mt-2 text-xs text-neutral-500">
            {formatDisplayDate(post.date)}
          </div>
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="space-y-6 text-neutral-700">
          {renderMarkdownBlocks(post.body)}
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
    </main>
  )
}

function renderMarkdownBlocks(body: string) {
  const blocks = body.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean)

  return blocks.map((block, index) => {
    if (block.startsWith('# ')) {
      return (
        <h2 key={index} className="text-2xl font-semibold text-neutral-900 font-serif">
          {block.replace(/^# /, '').trim()}
        </h2>
      )
    }
    if (block.startsWith('## ')) {
      return (
        <h3 key={index} className="text-xl font-semibold text-neutral-900 font-serif">
          {block.replace(/^## /, '').trim()}
        </h3>
      )
    }
    if (block.startsWith('### ')) {
      return (
        <h4 key={index} className="text-lg font-semibold text-neutral-900 font-serif">
          {block.replace(/^### /, '').trim()}
        </h4>
      )
    }

    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean)
    const isList = lines.length > 1 && lines.every((line) => line.startsWith('- '))
    if (isList) {
      return (
        <ul key={index} className="list-disc list-inside space-y-1 text-sm text-neutral-600">
          {lines.map((line, listIndex) => (
            <li key={listIndex}>{line.replace(/^- /, '')}</li>
          ))}
        </ul>
      )
    }

    return (
      <p key={index} className="text-sm text-neutral-600">
        {block.replace(/\n+/g, ' ')}
      </p>
    )
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
