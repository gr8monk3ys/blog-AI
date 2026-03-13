import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { loadBlogPosts } from '../../lib/blog-index'

export const metadata = {
  title: 'Blog | Blog AI',
  description: 'AI content strategy, SEO workflows, and scaling content with tools.',
}

export default async function BlogIndexPage() {
  const posts = await loadBlogPosts()

  return (
    <main className="min-h-screen bg-gradient-to-b from-neutral-50 via-white to-neutral-100">
      <SiteHeader />

      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-xs uppercase tracking-wide text-neutral-500">Blog</p>
          <h1 className="text-3xl sm:text-4xl font-semibold text-neutral-900 font-serif">
            Content strategy and AI tooling
          </h1>
          <p className="mt-2 text-sm text-neutral-600 max-w-2xl">
            Learn how to scale content with templates, calculators, and AI workflows.
          </p>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {posts.length === 0 ? (
          <div className="bg-white border border-neutral-200 rounded-xl p-6 text-sm text-neutral-600">
            No posts yet. Add markdown files to `content/blog` to publish.
          </div>
        ) : (
          <div className="space-y-6">
            {posts.map((post) => (
              <article
                key={post.slug}
                className="bg-white border border-neutral-200 rounded-2xl p-6"
              >
                <div className="text-xs text-neutral-500">{formatDisplayDate(post.date)}</div>
                <h2 className="mt-2 text-xl font-semibold text-neutral-900">
                  <Link href={`/blog/${post.slug}`} className="hover:text-amber-700">
                    {post.title}
                  </Link>
                </h2>
                <p className="mt-2 text-sm text-neutral-600">{post.excerpt}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {post.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-2 py-1 rounded-full bg-neutral-100 text-neutral-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <SiteFooter />
    </main>
  )
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
