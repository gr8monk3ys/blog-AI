'use client'

import Link from 'next/link'
import { Suspense, useMemo } from 'react'
import { m } from 'framer-motion'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import ToolGrid from '../../components/tools/ToolGrid'
import { TOOL_CATEGORIES, type ToolCategory } from '../../types/tools'

function ToolsPageContent() {
  const initialCategory = useMemo(() => {
    if (typeof window === 'undefined') return 'all'
    const categoryParam = new URLSearchParams(window.location.search).get('category')
    if (categoryParam && categoryParam in TOOL_CATEGORIES) {
      return categoryParam as ToolCategory
    }
    return 'all'
  }, [])

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-700 to-amber-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              AI Writing Tools
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto">
              Discover powerful AI tools to create content for blogs, emails, social
              media, and more. Start writing smarter today.
            </p>

            {/* Quick stats */}
            <div className="mt-8 flex flex-wrap justify-center gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold">29+</div>
                <div className="text-sm text-amber-200">AI Tools</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">8</div>
                <div className="text-sm text-amber-200">Categories</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">50+</div>
                <div className="text-sm text-amber-200">Content Formats</div>
              </div>
            </div>
          </m.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {/* The grid is the first content under the page <h1>, so its card titles
              are the h2 level of this page; the CTA below is the other h2. */}
          <ToolGrid initialCategory={initialCategory} headingLevel={2} />
        </m.div>
      </section>

      {/* CTA Section */}
      <section className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="text-center"
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Can’t find what you need?
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-xl mx-auto mb-6">
              Use our flexible Blog Post or Book generators for custom content creation
              with advanced options.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-gradient-to-r from-amber-700 to-amber-800 hover:from-amber-800 hover:to-amber-900 shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
              >
                Open Content Generator
              </Link>
              <a
                href="mailto:support@blog-ai.com?subject=Tool%20Request"
                className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
              >
                Request a Tool
              </a>
            </div>
          </m.div>
        </div>
      </section>

      </main>
      <SiteFooter />
    </>
  )
}

export default function ToolsPageClient() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
          Loading tools…
        </main>
      }
    >
      <ToolsPageContent />
    </Suspense>
  )
}
