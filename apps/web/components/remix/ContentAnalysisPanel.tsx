'use client'

import React from 'react'
import { motion } from 'framer-motion'
import type { ContentAnalysis } from '@/types/remix'

interface ContentAnalysisPanelProps {
  analysis: ContentAnalysis
}

function ContentAnalysisPanelComponent({ analysis }: ContentAnalysisPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6"
    >
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Content Analysis</h2>

      <div className="space-y-4 text-gray-900 dark:text-gray-100">
        <div>
          <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Summary</h4>
          <p className="mt-1">{analysis.summary}</p>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Key Points</h4>
          <ul className="mt-1 space-y-1">
            {analysis.key_points.map((point: string, i: number) => (
              <li key={i} className="flex items-start">
                <span className="text-amber-500 mr-2">-</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Tone</h4>
            <p className="mt-1 capitalize">{analysis.tone}</p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Audience</h4>
            <p className="mt-1">{analysis.target_audience}</p>
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Keywords</h4>
          <div className="flex flex-wrap gap-2 mt-1">
            {analysis.keywords.map((keyword: string, i: number) => (
              <span key={i} className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export const ContentAnalysisPanel = React.memo(ContentAnalysisPanelComponent)
