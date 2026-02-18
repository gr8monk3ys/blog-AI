'use client'

import { useCallback, useState } from 'react'
import { FEEDBACK_TAGS, type FeedbackTag } from '../types/feedback'

interface ContentRatingProps {
  contentId: string
}

const STAR_COUNT = 5

function StarIcon({
  filled,
  half,
}: {
  filled: boolean
  half?: boolean
}): React.ReactElement {
  if (half) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        className="h-6 w-6"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="half-star-grad">
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="50%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path
          fill="url(#half-star-grad)"
          stroke="#f59e0b"
          strokeWidth="1.5"
          d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
        />
      </svg>
    )
  }

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      className="h-6 w-6"
      aria-hidden="true"
    >
      <path
        fill={filled ? '#f59e0b' : 'none'}
        stroke={filled ? '#f59e0b' : '#d1d5db'}
        strokeWidth="1.5"
        d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
      />
    </svg>
  )
}

export default function ContentRating({ contentId }: ContentRatingProps): React.ReactElement | null {
  const [rating, setRating] = useState(0)
  const [hoveredStar, setHoveredStar] = useState(0)
  const [selectedTags, setSelectedTags] = useState<FeedbackTag[]>([])
  const [feedbackText, setFeedbackText] = useState('')
  const [showTextarea, setShowTextarea] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleTagToggle = useCallback((tag: FeedbackTag) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    )
  }, [])

  const handleSubmit = useCallback(async () => {
    if (rating === 0) return

    setSubmitting(true)
    setError(null)

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: contentId,
          rating,
          tags: selectedTags,
          feedback_text: feedbackText.trim() || undefined,
        }),
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to submit feedback')
      }

      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }, [contentId, rating, selectedTags, feedbackText])

  if (submitted) {
    return (
      <div
        className="mt-8 border-t border-gray-200 pt-6"
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center gap-2 text-sm text-emerald-700">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
              clipRule="evenodd"
            />
          </svg>
          <span className="font-medium">Thanks for your feedback!</span>
        </div>
      </div>
    )
  }

  const displayRating = hoveredStar || rating

  return (
    <div className="mt-8 border-t border-gray-200 pt-6">
      <div className="space-y-4">
        {/* Star rating */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            How would you rate this content?
          </p>
          <div
            className="flex items-center gap-1"
            role="radiogroup"
            aria-label="Content rating"
          >
            {Array.from({ length: STAR_COUNT }, (_, i) => {
              const starValue = i + 1
              const isFilled = starValue <= displayRating
              const isSelected = starValue === rating

              return (
                <button
                  key={starValue}
                  type="button"
                  onClick={() => setRating(starValue)}
                  onMouseEnter={() => setHoveredStar(starValue)}
                  onMouseLeave={() => setHoveredStar(0)}
                  onFocus={() => setHoveredStar(starValue)}
                  onBlur={() => setHoveredStar(0)}
                  className={`
                    rounded-sm p-0.5 transition-transform duration-150
                    hover:scale-110 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1
                    ${isSelected ? 'scale-110' : ''}
                  `}
                  role="radio"
                  aria-checked={isSelected}
                  aria-label={`${starValue} star${starValue !== 1 ? 's' : ''}`}
                >
                  <StarIcon filled={isFilled} />
                </button>
              )
            })}
            {rating > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                {rating}/{STAR_COUNT}
              </span>
            )}
          </div>
        </div>

        {/* Quick feedback tags -- only show after a rating is selected */}
        {rating > 0 && (
          <div>
            <p className="text-sm text-gray-600 mb-2">
              What stood out? <span className="text-gray-400">(optional)</span>
            </p>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Feedback tags">
              {FEEDBACK_TAGS.map((tag) => {
                const isActive = selectedTags.includes(tag)
                return (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => handleTagToggle(tag)}
                    aria-pressed={isActive}
                    className={`
                      text-xs font-medium px-3 py-1.5 rounded-full border transition-colors
                      focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1
                      ${
                        isActive
                          ? 'bg-amber-100 border-amber-300 text-amber-800'
                          : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    {tag}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Expandable text feedback */}
        {rating > 0 && (
          <div>
            {!showTextarea ? (
              <button
                type="button"
                onClick={() => setShowTextarea(true)}
                className="text-sm text-amber-700 hover:text-amber-800 underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1 rounded-sm"
              >
                Add a comment
              </button>
            ) : (
              <div>
                <label htmlFor="feedback-text" className="sr-only">
                  Additional feedback
                </label>
                <textarea
                  id="feedback-text"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us more about your experience..."
                  maxLength={MAX_TEXT_LENGTH}
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 placeholder:text-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 resize-y"
                />
                <p className="mt-1 text-xs text-gray-400 text-right">
                  {feedbackText.length}/{MAX_TEXT_LENGTH}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}

        {/* Submit button */}
        {rating > 0 && (
          <div>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className={`
                inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg
                transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2
                ${
                  submitting
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-amber-600 text-white hover:bg-amber-700'
                }
              `}
            >
              {submitting ? (
                <>
                  <svg
                    className="mr-2 h-4 w-4 animate-spin text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Submitting...
                </>
              ) : (
                'Submit Feedback'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const MAX_TEXT_LENGTH = 1000
