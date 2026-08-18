import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { loadBlogPosts } from '../../lib/blog-index'

export const metadata = {
  title: 'Blog',
  description: 'AI content strategy, SEO workflows, and scaling content with tools.',
}

export default async function BlogIndexPage() {
  const posts = await loadBlogPosts()

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Blog</p>
          <h1 className="text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
            Content strategy and AI tooling
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-2xl">
            Learn how to scale content with templates, calculators, and AI workflows.
          </p>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {posts.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 text-sm text-gray-600 dark:text-gray-400">
            No posts yet. Add markdown files to `content/blog` to publish.
          </div>
        ) : (
          <div className="space-y-6">
            {posts.map((post) => (
              <article
                key={post.slug}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6"
              >
                <div className="text-xs text-gray-500 dark:text-gray-400">{formatDisplayDate(post.date)}</div>
                <h2 className="mt-2 text-xl font-semibold text-gray-900 dark:text-gray-100">
                  <Link href={`/blog/${post.slug}`} className="hover:text-amber-700 dark:hover:text-amber-300">
                    {post.title}
                  </Link>
                </h2>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{post.excerpt}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {post.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
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

      </main>
      <SiteFooter />
    </>
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
