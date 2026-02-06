'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import ToolGrid from '../../components/tools/ToolGrid'
import { SparklesIcon, ArrowLeftIcon, ClockIcon } from '@heroicons/react/24/outline'
import { TOOL_CATEGORIES, type ToolCategory } from '../../types/tools'

export default function ToolsPage() {
  const searchParams = useSearchParams()

  const initialCategory = useMemo(() => {
    const categoryParam = searchParams.get('category')
    if (categoryParam && categoryParam in TOOL_CATEGORIES) {
      return categoryParam as ToolCategory
    }
    return 'all'
  }, [searchParams])

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" aria-hidden="true" />
                <span>Back to Generator</span>
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/tool-directory"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 transition-colors"
              >
                Directory
              </Link>
              <Link
                href="/blog"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 transition-colors"
              >
                Blog
              </Link>
              <Link
                href="/history"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-indigo-600 transition-colors"
              >
                <ClockIcon className="w-4 h-4" aria-hidden="true" />
                <span>History</span>
              </Link>
              <div className="flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-indigo-600" aria-hidden="true" />
                <span className="font-semibold text-gray-900">Blog AI</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              AI Writing Tools
            </h1>
            <p className="text-lg sm:text-xl text-indigo-100 max-w-2xl mx-auto">
              Discover powerful AI tools to create content for blogs, emails, social
              media, and more. Start writing smarter today.
            </p>

            {/* Quick stats */}
            <div className="mt-8 flex flex-wrap justify-center gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold">29+</div>
                <div className="text-sm text-indigo-200">AI Tools</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">8</div>
                <div className="text-sm text-indigo-200">Categories</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">20+</div>
                <div className="text-sm text-indigo-200">Free Tools</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ToolGrid initialCategory={initialCategory} />
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="text-center"
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              Can&apos;t find what you need?
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto mb-6">
              Use our flexible Blog Post or Book generators for custom content creation
              with advanced options.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Open Content Generator
              </Link>
              <a
                href="#"
                className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Request a Tool
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by AI &middot; Blog AI Content Generator
          </p>
        </div>
      </footer>
    </main>
  )
}
