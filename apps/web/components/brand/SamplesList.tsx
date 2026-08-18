'use client'

import React, { memo } from 'react'
import { DocumentTextIcon, TrashIcon } from '@heroicons/react/24/outline'

interface SampleListItem {
  id: string
  title?: string
  word_count: number
  content_type: string
  is_analyzed: boolean
  quality_score: number
  is_primary_example: boolean
}

interface SamplesListProps {
  samples: SampleListItem[]
  onDelete: (sampleId: string) => void
}

function getQualityColor(score: number) {
  if (score >= 0.8) return 'text-emerald-600 dark:text-emerald-400'
  if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function SamplesListComponent({ samples, onDelete }: SamplesListProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
        <DocumentTextIcon className="w-5 h-5" />
        Voice Samples ({samples.length})
      </h2>

      {samples.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No samples yet. Add content samples above.
        </p>
      ) : (
        <div className="space-y-3">
          {samples.map((sample) => (
            <div
              key={sample.id}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
            >
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {sample.title || `Sample ${sample.id.slice(-4)}`}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {sample.word_count} words &bull; {sample.content_type}
                  {sample.is_analyzed && (
                    <span className={`ml-2 ${getQualityColor(sample.quality_score)}`}>
                      Quality: {Math.round(sample.quality_score * 100)}%
                    </span>
                  )}
                </p>
              </div>
              <button
                onClick={() => onDelete(sample.id)}
                className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded"
                aria-label="Delete sample"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export const SamplesList = memo(SamplesListComponent)
export default SamplesList
