'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { StarIcon } from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { historyApi } from '../../lib/history-api'

interface FavoriteButtonProps {
  contentId: string
  isFavorite: boolean
  onToggle?: (newStatus: boolean) => void
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
}

const buttonSizeClasses = {
  sm: 'p-1',
  md: 'p-1.5',
  lg: 'p-2',
}

export default function FavoriteButton({
  contentId,
  isFavorite: initialFavorite,
  onToggle,
  size = 'md',
  showLabel = false,
  className = '',
}: FavoriteButtonProps) {
  const [isFavorite, setIsFavorite] = useState(initialFavorite)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleToggle = useCallback(async () => {
    if (isLoading) return

    setIsLoading(true)
    setError(null)

    // Optimistic update
    const previousState = isFavorite
    setIsFavorite(!isFavorite)

    try {
      const newStatus = await historyApi.toggleFavorite(contentId)
      setIsFavorite(newStatus)
      onToggle?.(newStatus)
    } catch (err) {
      // Revert on error
      setIsFavorite(previousState)
      setError('Failed to update favorite')
      console.error('Failed to toggle favorite:', err)
    } finally {
      setIsLoading(false)
    }
  }, [contentId, isFavorite, isLoading, onToggle])

  return (
    <div className={`inline-flex items-center ${className}`}>
      <button
        type="button"
        onClick={handleToggle}
        disabled={isLoading}
        aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        aria-pressed={isFavorite}
        className={`
          group relative inline-flex items-center justify-center
          ${buttonSizeClasses[size]}
          rounded-lg transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
          ${
            isFavorite
              ? 'text-amber-500 hover:text-amber-600'
              : 'text-gray-400 hover:text-amber-500'
          }
          ${isLoading ? 'opacity-50 cursor-wait' : 'hover:bg-gray-100'}
          disabled:cursor-not-allowed
        `}
      >
        <AnimatePresence mode="wait">
          {isFavorite ? (
            <motion.div
              key="filled"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <StarIconSolid
                className={`${sizeClasses[size]} ${isLoading ? 'animate-pulse' : ''}`}
                aria-hidden="true"
              />
            </motion.div>
          ) : (
            <motion.div
              key="outline"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <StarIcon
                className={`${sizeClasses[size]} ${isLoading ? 'animate-pulse' : ''}`}
                aria-hidden="true"
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Ripple effect on click */}
        <span
          className={`
            absolute inset-0 rounded-lg
            ${isFavorite ? 'bg-amber-500' : 'bg-gray-500'}
            opacity-0 group-active:opacity-10
            transition-opacity
          `}
          aria-hidden="true"
        />
      </button>

      {showLabel && (
        <span
          className={`ml-1.5 text-sm ${
            isFavorite ? 'text-amber-600' : 'text-gray-500'
          }`}
        >
          {isFavorite ? 'Favorited' : 'Favorite'}
        </span>
      )}

      {/* Error tooltip */}
      <AnimatePresence>
        {error && (
          <motion.span
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -5 }}
            className="ml-2 text-xs text-red-500"
            role="alert"
          >
            {error}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  )
}
