import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { loadBlogPosts } from '../../lib/blog-index'

export const metadata = {
  title: 'Blog',
  description: 'AI content strategy, SEO workflows, and scaling content with tools.',
}

// The blog index on the notebook: one reading column (42rem), an index header
// with a wall label, posts as hairline-divided rows — mono date, Fraunces
// title, muted excerpt, tags as wall labels (DESIGN.md → Cards / Rows).
export default async function BlogIndexPage() {
  const posts = await loadBlogPosts()

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <header className="mx-auto max-w-2xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <p className="label-mono">Blog</p>
          <h1 className="text-page-title mt-3">Content Strategy and AI Tooling</h1>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground text-pretty">
            Learn how to scale content with templates, calculators, and AI workflows.
          </p>
        </header>

        <section className="mx-auto max-w-2xl px-4 pb-16 sm:px-6 md:pb-24 lg:px-8">
          {posts.length === 0 ? (
            // An honest empty state in the house voice: a wall label and one serif line.
            <div className="border-y border-border py-10">
              <p className="label-mono">No posts yet</p>
              <h2 className="text-card-title mt-3">Nothing has been published here yet.</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Add markdown files to <code className="font-mono">content/blog</code> to publish.
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-border border-y border-border">
              {posts.map((post) => (
                <li key={post.slug}>
                  <article className="py-8">
                    <p className="label-mono">
                      <time dateTime={post.date}>{formatDisplayDate(post.date)}</time>
                    </p>
                    <h2 className="text-card-title mt-2">
                      <Link
                        href={`/blog/${post.slug}`}
                        className="transition-colors hover:text-primary"
                      >
                        {post.title}
                      </Link>
                    </h2>
                    <p className="mt-2 leading-relaxed text-muted-foreground">{post.excerpt}</p>
                    {post.tags.length > 0 && (
                      <ul className="label-mono mt-4 flex flex-wrap gap-x-4 gap-y-1" aria-label="Tags">
                        {post.tags.map((tag) => (
                          <li key={tag}>{tag}</li>
                        ))}
                      </ul>
                    )}
                  </article>
                </li>
              ))}
            </ul>
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
    month: 'short',
    day: 'numeric',
  })
}
