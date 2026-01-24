'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ToolCard from './ToolCard'
import ToolSearch from './ToolSearch'
import CategoryFilter from './CategoryFilter'
import { Tool, ToolCategory, SAMPLE_TOOLS } from '../../types/tools'
import {
  FunnelIcon,
  Squares2X2Icon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'

interface ToolGridProps {
  tools?: Tool[]
  showFilters?: boolean
  showSearch?: boolean
  initialCategory?: ToolCategory | 'all'
}

export default function ToolGrid({
  tools = SAMPLE_TOOLS,
  showFilters = true,
  showSearch = true,
  initialCategory = 'all',
}: ToolGridProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ToolCategory | 'all'>(
    initialCategory
  )
  const [showFreeOnly, setShowFreeOnly] = useState(false)

  // Filter tools based on search, category, and free filter
  const filteredTools = useMemo(() => {
    let result = tools

    // Filter by category
    if (selectedCategory !== 'all') {
      result = result.filter((tool) => tool.category === selectedCategory)
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      result = result.filter(
        (tool) =>
          tool.name.toLowerCase().includes(query) ||
          tool.description.toLowerCase().includes(query) ||
          tool.category.toLowerCase().includes(query)
      )
    }

    // Filter by free only
    if (showFreeOnly) {
      result = result.filter((tool) => tool.isFree)
    }

    return result
  }, [tools, selectedCategory, searchQuery, showFreeOnly])

  // Calculate tool counts per category
  const toolCounts = useMemo(() => {
    const counts: Record<ToolCategory | 'all', number> = {
      all: tools.length,
      blog: 0,
      email: 0,
      'social-media': 0,
      business: 0,
      naming: 0,
      video: 0,
      seo: 0,
      rewriting: 0,
    }

    tools.forEach((tool) => {
      counts[tool.category]++
    })

    return counts
  }, [tools])

  // Sort tools: popular first, then new, then alphabetically
  const sortedTools = useMemo(() => {
    return [...filteredTools].sort((a, b) => {
      if (a.isPopular && !b.isPopular) return -1
      if (!a.isPopular && b.isPopular) return 1
      if (a.isNew && !b.isNew) return -1
      if (!a.isNew && b.isNew) return 1
      return a.name.localeCompare(b.name)
    })
  }, [filteredTools])

  return (
    <div className="space-y-6">
      {/* Search and filter controls */}
      {(showSearch || showFilters) && (
        <div className="space-y-4">
          {showSearch && (
            <ToolSearch
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              placeholder="Search for tools (e.g., blog, email, SEO...)"
              resultCount={searchQuery ? filteredTools.length : undefined}
            />
          )}

          {showFilters && (
            <div className="flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
              <CategoryFilter
                selectedCategory={selectedCategory}
                onCategoryChange={setSelectedCategory}
                toolCounts={toolCounts}
              />

              {/* Additional filter toggle */}
              <button
                type="button"
                onClick={() => setShowFreeOnly(!showFreeOnly)}
                className={`flex-shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                  showFreeOnly
                    ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
                aria-pressed={showFreeOnly}
              >
                <FunnelIcon className="w-4 h-4" aria-hidden="true" />
                Free Only
              </button>
            </div>
          )}
        </div>
      )}

      {/* Results summary */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <Squares2X2Icon className="w-4 h-4" aria-hidden="true" />
          <span>
            Showing {sortedTools.length} of {tools.length} tools
          </span>
        </div>
      </div>

      {/* Tools grid */}
      <AnimatePresence mode="wait">
        {sortedTools.length > 0 ? (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
            {sortedTools.map((tool, index) => (
              <ToolCard key={tool.id} tool={tool} index={index} />
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <MagnifyingGlassIcon className="w-8 h-8 text-gray-400" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No tools found
            </h3>
            <p className="text-sm text-gray-500 max-w-sm mx-auto">
              Try adjusting your search or filter criteria to find what you&apos;re
              looking for.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery('')
                setSelectedCategory('all')
                setShowFreeOnly(false)
              }}
              className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
            >
              Clear all filters
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
