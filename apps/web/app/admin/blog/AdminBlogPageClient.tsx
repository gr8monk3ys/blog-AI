'use client'

import RequireAuth from '../../../components/RequireAuth'
import BlogPostEditor from '../../../components/admin/BlogPostEditor'

export default function AdminBlogPageClient() {
  return (
    <RequireAuth>
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
        <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Admin</p>
            <h1 className="text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
              Blog CMS
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-2xl">
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
