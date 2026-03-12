'use client'

import React, { memo } from 'react'
import { LazyMotion, domAnimation, m } from 'framer-motion'
import type { VoiceScore } from '@/types/brand'

interface ScoreResultProps {
  score: VoiceScore
}

function toKeyedStrings(values: string[], prefix: string) {
  const counts = new Map<string, number>()

  return values.map((value) => {
    const normalized = value.trim() || 'item'
    const baseKey = `${prefix}-${normalized}`
    const seen = counts.get(baseKey) ?? 0
    counts.set(baseKey, seen + 1)

    return {
      key: seen === 0 ? baseKey : `${baseKey}-${seen + 1}`,
      value,
    }
  })
}

function getQualityColor(score: number) {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

function ScoreResultComponent({ score }: ScoreResultProps) {
  const keyedSuggestions = toKeyedStrings(score.suggestions, 'voice-suggestion')

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4 p-4 bg-gray-50 rounded-lg"
      >
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium">Voice Match Score</h4>
          <span
            className={`text-2xl font-bold ${getQualityColor(score.overall_score)}`}
          >
            {Math.round(score.overall_score * 100)}%
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="text-center p-2 bg-white rounded">
            <div className="font-medium">
              {Math.round(score.tone_match * 100)}%
            </div>
            <div className="text-gray-500">Tone</div>
          </div>
          <div className="text-center p-2 bg-white rounded">
            <div className="font-medium">
              {Math.round(score.vocabulary_match * 100)}%
            </div>
            <div className="text-gray-500">Vocabulary</div>
          </div>
          <div className="text-center p-2 bg-white rounded">
            <div className="font-medium">
              {Math.round(score.style_match * 100)}%
            </div>
            <div className="text-gray-500">Style</div>
          </div>
        </div>

        {keyedSuggestions.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm font-medium mb-2">Suggestions</h5>
            <ul className="text-sm text-gray-600 space-y-1">
              {keyedSuggestions.map((suggestion) => (
                <li key={suggestion.key} className="flex items-start gap-2">
                  <span className="text-amber-500">&bull;</span>
                  {suggestion.value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </m.div>
    </LazyMotion>
  )
}

export const ScoreResult = memo(ScoreResultComponent)
export default ScoreResult
