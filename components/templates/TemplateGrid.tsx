'use client'

import { useState, useMemo, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import TemplateCard from './TemplateCard'
import TemplateCategoryFilter from './TemplateCategoryFilter'
import {
  MagnifyingGlassIcon,
  Squares2X2Icon,
} from '@heroicons/react/24/outline'
import { Template, TemplateCategory, SAMPLE_TEMPLATES } from '../../types/templates'

interface TemplateGridProps {
  showFilters?: boolean
  showSearch?: boolean
  initialCategory?: TemplateCategory | 'all'
  toolId?: string
}

export default function TemplateGrid({
  showFilters = true,
  showSearch = true,
  initialCategory = 'all',
  toolId,
}: TemplateGridProps) {
  const router = useRouter()
  const [templates, setTemplates] = useState<Template[]>(SAMPLE_TEMPLATES)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>(
    initialCategory
  )
  const [loading, setLoading] = useState(false)

  // Fetch templates from API
  useEffect(() => {
    const fetchTemplates = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (selectedCategory !== 'all') {
          params.set('category', selectedCategory)
        }
        if (toolId) {
          params.set('toolId', toolId)
        }
        if (searchQuery) {
          params.set('search', searchQuery)
        }

        const response = await fetch(`/api/templates?${params.toString()}`)
        const data = await response.json()

        if (data.success) {
          setTemplates(data.data)
        }
      } catch (error) {
        console.error('Error fetching templates:', error)
        // Fall back to sample data
        setTemplates(SAMPLE_TEMPLATES)
      } finally {
        setLoading(false)
      }
    }

    // Debounce search
    const timeoutId = setTimeout(fetchTemplates, searchQuery ? 300 : 0)
    return () => clearTimeout(timeoutId)
  }, [selectedCategory, toolId, searchQuery])

  // Filter templates locally for immediate feedback
  const filteredTemplates = useMemo(() => {
    let result = templates

    // Filter by category
    if (selectedCategory !== 'all') {
      result = result.filter((t) => t.category === selectedCategory)
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          t.description?.toLowerCase().includes(query) ||
          t.tags.some((tag) => tag.toLowerCase().includes(query))
      )
    }

    // Filter by tool ID
    if (toolId) {
      result = result.filter((t) => t.toolId === toolId)
    }

    return result
  }, [templates, selectedCategory, searchQuery, toolId])

  // Calculate template counts per category
  const templateCounts = useMemo(() => {
    const counts: Record<TemplateCategory | 'all', number> = {
      all: templates.length,
      marketing: 0,
      saas: 0,
      ecommerce: 0,
      content: 0,
      social: 0,
      email: 0,
      video: 0,
      business: 0,
      other: 0,
    }

    templates.forEach((t) => {
      if (counts[t.category] !== undefined) {
        counts[t.category]++
      }
    })

    return counts
  }, [templates])

  // Sort templates: popular first
  const sortedTemplates = useMemo(() => {
    return [...filteredTemplates].sort((a, b) => b.useCount - a.useCount)
  }, [filteredTemplates])

  // Handle template use
  const handleUseTemplate = async (template: Template) => {
    // Increment use count
    try {
      await fetch(`/api/templates/${template.id}/use`, { method: 'POST' })
    } catch (error) {
      console.error('Error incrementing template use count:', error)
    }

    // Navigate to tool with preset inputs
    const presetParams = new URLSearchParams()
    presetParams.set('template', template.id)
    presetParams.set('presets', JSON.stringify(template.presetInputs))

    router.push(`/tools/${template.toolId}?${presetParams.toString()}`)
  }

  return (
    <div className="space-y-6">
      {/* Search and filter controls */}
      {(showSearch || showFilters) && (
        <div className="space-y-4">
          {showSearch && (
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates (e.g., landing page, email, social...)"
                className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm"
              />
              {searchQuery && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <span className="text-xs text-gray-400">
                    {filteredTemplates.length} results
                  </span>
                </div>
              )}
            </div>
          )}

          {showFilters && (
            <TemplateCategoryFilter
              selectedCategory={selectedCategory}
              onCategoryChange={setSelectedCategory}
              templateCounts={templateCounts}
            />
          )}
        </div>
      )}

      {/* Results summary */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <Squares2X2Icon className="w-4 h-4" aria-hidden="true" />
          <span>
            Showing {sortedTemplates.length} of {templates.length} templates
          </span>
        </div>
      </div>

      {/* Templates grid */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="h-64 bg-gray-100 rounded-xl animate-pulse"
              />
            ))}
          </motion.div>
        ) : sortedTemplates.length > 0 ? (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
            {sortedTemplates.map((template, index) => (
              <TemplateCard
                key={template.id}
                template={template}
                index={index}
                onUse={handleUseTemplate}
              />
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
              No templates found
            </h3>
            <p className="text-sm text-gray-500 max-w-sm mx-auto">
              Try adjusting your search or filter criteria to find what you are
              looking for.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery('')
                setSelectedCategory('all')
              }}
              className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors"
            >
              Clear all filters
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
