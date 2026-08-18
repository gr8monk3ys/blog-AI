'use client'

import React, { memo } from 'react'
import { motion } from 'framer-motion'
import type { VoiceScore } from '@/types/brand'

interface ScoreResultProps {
  score: VoiceScore
}

function getQualityColor(score: number) {
  if (score >= 0.8) return 'text-emerald-600 dark:text-emerald-400'
  if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function ScoreResultComponent({ score }: ScoreResultProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-gray-900 dark:text-gray-100">Voice Match Score</h4>
        <span
          className={`text-2xl font-bold ${getQualityColor(score.overall_score)}`}
        >
          {Math.round(score.overall_score * 100)}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-sm">
        <div className="text-center p-2 bg-white dark:bg-gray-900 rounded">
          <div className="font-medium text-gray-900 dark:text-gray-100">
            {Math.round(score.tone_match * 100)}%
          </div>
          <div className="text-gray-500 dark:text-gray-400">Tone</div>
        </div>
        <div className="text-center p-2 bg-white dark:bg-gray-900 rounded">
          <div className="font-medium text-gray-900 dark:text-gray-100">
            {Math.round(score.vocabulary_match * 100)}%
          </div>
          <div className="text-gray-500 dark:text-gray-400">Vocabulary</div>
        </div>
        <div className="text-center p-2 bg-white dark:bg-gray-900 rounded">
          <div className="font-medium text-gray-900 dark:text-gray-100">
            {Math.round(score.style_match * 100)}%
          </div>
          <div className="text-gray-500 dark:text-gray-400">Style</div>
        </div>
      </div>

      {score.suggestions.length > 0 && (
        <div className="mt-4">
          <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Suggestions</h5>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            {score.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-amber-500">&bull;</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}

export const ScoreResult = memo(ScoreResultComponent)
export default ScoreResult
