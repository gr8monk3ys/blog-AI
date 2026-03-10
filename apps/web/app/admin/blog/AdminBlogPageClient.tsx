'use client'

import RequireAuth from '../../../components/RequireAuth'
import BlogPostEditor from '../../../components/admin/BlogPostEditor'

export default function AdminBlogPageClient() {
  return (
    <RequireAuth>
      <main className="min-h-screen bg-gradient-to-b from-neutral-50 via-white to-neutral-100 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
        <header className="border-b border-neutral-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400">Admin</p>
            <h1 className="text-3xl sm:text-4xl font-semibold text-neutral-900 dark:text-neutral-100 font-serif">
              Blog CMS
            </h1>
            <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400 max-w-2xl">
              Create, edit, and publish blog posts. Requires `BLOG_ADMIN_KEY`.
            </p>
          </div>
        </header>

        <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <BlogPostEditor />
        </section>
      </main>
    </RequireAuth>
  )
}
