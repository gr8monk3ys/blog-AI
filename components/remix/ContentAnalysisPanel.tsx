'use client'

import React from 'react'
import { LazyMotion, domAnimation, m } from 'framer-motion'
import type { ContentAnalysis } from '@/types/remix'

interface ContentAnalysisPanelProps {
  analysis: ContentAnalysis
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

function ContentAnalysisPanelComponent({ analysis }: ContentAnalysisPanelProps) {
  const keyPoints = toKeyedStrings(analysis.key_points, 'key-point')
  const keywords = toKeyedStrings(analysis.keywords, 'keyword')

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <h2 className="text-lg font-semibold mb-4">Content Analysis</h2>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-500">Summary</h4>
            <p className="mt-1">{analysis.summary}</p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-500">Key Points</h4>
            <ul className="mt-1 space-y-1">
              {keyPoints.map((point) => (
                <li key={point.key} className="flex items-start">
                  <span className="text-blue-500 mr-2">-</span>
                  <span>{point.value}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500">Tone</h4>
                <p className="mt-1 capitalize">{analysis.tone}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500">Audience</h4>
                <p className="mt-1">{analysis.target_audience}</p>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-500">Keywords</h4>
            <div className="flex flex-wrap gap-2 mt-1">
              {keywords.map((keyword) => (
                <span key={keyword.key} className="px-2 py-1 bg-gray-100 rounded text-sm">
                  {keyword.value}
                </span>
              ))}
            </div>
          </div>
        </div>
      </m.div>
    </LazyMotion>
  )
}

export const ContentAnalysisPanel = React.memo(ContentAnalysisPanelComponent)
