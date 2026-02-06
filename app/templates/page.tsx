'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import TemplateGrid from '../../components/templates/TemplateGrid'
import {
  SparklesIcon,
  ArrowLeftIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline'

export default function TemplatesPage() {
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
                href="/tools"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Tools
              </Link>
              <Link
                href="/brand"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Brand Voice
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
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 mb-6">
              <BookmarkIcon className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Templates Library
            </h1>
            <p className="text-lg sm:text-xl text-indigo-100 max-w-2xl mx-auto">
              Start faster with pre-configured templates. Browse our collection of
              ready-to-use content templates or save your own presets.
            </p>

            {/* Quick stats */}
            <div className="mt-8 flex flex-wrap justify-center gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold">50+</div>
                <div className="text-sm text-indigo-200">Templates</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">9</div>
                <div className="text-sm text-indigo-200">Categories</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">1-Click</div>
                <div className="text-sm text-indigo-200">Setup</div>
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
          <TemplateGrid />
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
              Create Your Own Templates
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto mb-6">
              Use any AI tool to create content, then save your settings as a
              reusable template for future use.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/tools"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Browse Tools
              </Link>
              <Link
                href="/brand"
                className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Set Up Brand Voice
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by AI - Blog AI Content Generator
          </p>
        </div>
      </footer>
    </main>
  )
}
