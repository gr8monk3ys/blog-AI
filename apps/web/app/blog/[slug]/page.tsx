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

// A post on the notebook: the reading column (42rem), a mono date above a
// Fraunces title, the body in `prose` pointed at the tokens
// (`prose-notebook` in globals.css), tags as wall labels at the end.
export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params
  const post = await loadBlogPost(slug)

  if (!post) {
    notFound()
  }

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <header className="mx-auto max-w-2xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <Link
            href="/blog"
            className="label-mono label-link ink-underline transition-colors hover:text-primary"
          >
            ← Back to Blog
          </Link>
          <p className="label-mono mt-8">
            <time dateTime={post.date}>{formatDisplayDate(post.date)}</time>
          </p>
          <h1 className="text-page-title mt-3">{post.title}</h1>
        </header>

        <article className="mx-auto max-w-2xl px-4 pb-16 sm:px-6 md:pb-24 lg:px-8">
          <hr className="gallery-rule" />
          <div className="prose prose-notebook mt-10 max-w-none">{renderMarkdownBlocks(post.body)}</div>

          {post.tags.length > 0 && (
            <ul
              className="label-mono mt-12 flex flex-wrap gap-x-4 gap-y-1 border-t border-border pt-6"
              aria-label="Tags"
            >
              {post.tags.map((tag) => (
                <li key={tag}>{tag}</li>
              ))}
            </ul>
          )}
        </article>
      </main>
      <SiteFooter />
    </>
  )
}

function renderMarkdownBlocks(body: string) {
  const blocks = body.split(/\n\s*\n/).flatMap((block) => block.trim() || [])

  return blocks.map((block, index) => {
    if (block.startsWith('# ')) {
      return <h2 key={index}>{block.replace(/^# /, '').trim()}</h2>
    }
    if (block.startsWith('## ')) {
      return <h3 key={index}>{block.replace(/^## /, '').trim()}</h3>
    }
    if (block.startsWith('### ')) {
      return <h4 key={index}>{block.replace(/^### /, '').trim()}</h4>
    }

    const lines = block.split('\n').flatMap((line) => line.trim() || [])
    const isList = lines.length > 1 && lines.every((line) => line.startsWith('- '))
    if (isList) {
      return (
        <ul key={index}>
          {lines.map((line, listIndex) => (
            <li key={listIndex}>{line.replace(/^- /, '')}</li>
          ))}
        </ul>
      )
    }

    return <p key={index}>{block.replace(/\n+/g, ' ')}</p>
  })
}

function formatDisplayDate(dateValue: string): string {
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return dateValue
  return parsed.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
