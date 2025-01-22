'use client'

import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { motion, AnimatePresence } from 'framer-motion'

interface ToolSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  placeholder?: string
  resultCount?: number
}

export default function ToolSearch({
  searchQuery,
  onSearchChange,
  placeholder = 'Search tools...',
  resultCount,
}: ToolSearchProps) {
  const handleClear = () => {
    onSearchChange('')
  }

  return (
    <div className="relative">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <MagnifyingGlassIcon
            className="h-5 w-5 text-gray-400"
            aria-hidden="true"
          />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="block w-full pl-11 pr-10 py-3 border border-gray-200 rounded-xl bg-white shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm transition-all"
          placeholder={placeholder}
          aria-label="Search tools"
        />
        <AnimatePresence>
          {searchQuery && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              type="button"
              onClick={handleClear}
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-5 w-5" aria-hidden="true" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Result count indicator - with aria-live for screen reader announcements */}
      <AnimatePresence>
        {searchQuery && resultCount !== undefined && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-2 text-sm text-gray-500"
            aria-live="polite"
            aria-atomic="true"
          >
            {resultCount === 0 ? (
              <span>No tools found matching &ldquo;{searchQuery}&rdquo;</span>
            ) : (
              <span>
                Found {resultCount} {resultCount === 1 ? 'tool' : 'tools'} matching
                &ldquo;{searchQuery}&rdquo;
              </span>
            )}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
