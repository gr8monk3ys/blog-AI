'use client'

import { useState, useCallback } from 'react'
import { StarIcon } from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { historyApi } from '../../lib/history-api'
import { cn } from '../../lib/cn'

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

// A starred item takes the ink; an unstarred one is Ink Muted until hovered.
// The swap between the outline and the solid star is instant: a toggle is the
// interface responding, and a 150ms scale-in read as the page fidgeting.
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

  const Star = isFavorite ? StarIconSolid : StarIcon

  return (
    <div className={cn('inline-flex items-center', className)}>
      <button
        type="button"
        onClick={handleToggle}
        disabled={isLoading}
        aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        aria-pressed={isFavorite}
        className={cn(
          'inline-flex items-center justify-center rounded-lg transition-colors duration-150 hover:bg-primary/5 disabled:cursor-not-allowed',
          buttonSizeClasses[size],
          isFavorite ? 'text-primary' : 'text-muted-foreground hover:text-primary',
          isLoading && 'cursor-wait opacity-50'
        )}
      >
        <Star className={cn(sizeClasses[size], isLoading && 'animate-pulse')} aria-hidden="true" />
      </button>

      {showLabel && (
        <span className={cn('ml-1.5 text-sm', isFavorite ? 'text-primary' : 'text-muted-foreground')}>
          {isFavorite ? 'Favorited' : 'Favorite'}
        </span>
      )}

      {error && (
        <span className="ml-2 text-xs text-destructive" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
