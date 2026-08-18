import { notFound } from 'next/navigation'
import Link from 'next/link'
import SiteHeader from '../../../components/SiteHeader'
import SiteFooter from '../../../components/SiteFooter'
import { loadBlogPost } from '../../../lib/blog-index'

interface BlogPostPageProps {
  params: Promise<{ slug: string }>
}

export async function generateMetadata({ params }: BlogPostPageProps) {
  const { slug } = await params
  const post = await loadBlogPost(slug)
  if (!post) return {}

  return {
    title: `${post.title} | Blog AI`,
    description: post.excerpt,
  }
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params
  const post = await loadBlogPost(slug)

  if (!post) {
    notFound()
  }

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href="/blog" className="text-xs text-gray-500 dark:text-gray-400 hover:text-amber-700 dark:hover:text-amber-300">
            Back to blog
          </Link>
          <h1 className="mt-3 text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
            {post.title}
          </h1>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">{formatDisplayDate(post.date)}</div>
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="space-y-6 text-gray-700 dark:text-gray-300">{renderMarkdownBlocks(post.body)}</div>

        {post.tags.length > 0 && (
          <div className="mt-8 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </article>

      </main>
      <SiteFooter />
    </>
  )
}

function renderMarkdownBlocks(body: string) {
  const blocks = body.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean)

  return blocks.map((block, index) => {
    if (block.startsWith('# ')) {
      return (
        <h2 key={index} className="text-2xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
          {block.replace(/^# /, '').trim()}
        </h2>
      )
    }
    if (block.startsWith('## ')) {
      return (
        <h3 key={index} className="text-xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
          {block.replace(/^## /, '').trim()}
        </h3>
      )
    }
    if (block.startsWith('### ')) {
      return (
        <h4 key={index} className="text-lg font-semibold text-gray-900 dark:text-gray-100 font-serif">
          {block.replace(/^### /, '').trim()}
        </h4>
      )
    }

    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean)
    const isList = lines.length > 1 && lines.every((line) => line.startsWith('- '))
    if (isList) {
      return (
        <ul key={index} className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
          {lines.map((line, listIndex) => (
            <li key={listIndex}>{line.replace(/^- /, '')}</li>
          ))}
        </ul>
      )
    }

    return (
      <p key={index} className="text-sm text-gray-600 dark:text-gray-400">
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
