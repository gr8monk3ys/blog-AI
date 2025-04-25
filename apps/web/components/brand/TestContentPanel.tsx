'use client'

import React, { memo } from 'react'
import { AnimatePresence } from 'framer-motion'
import type { VoiceScore } from '@/types/brand'
import ScoreResult from './ScoreResult'

interface TestContentPanelProps {
  testContent: string
  onContentChange: (value: string) => void
  onScore: () => void
  isScoring: boolean
  canScore: boolean
  scoreResult: VoiceScore | null
}

function TestContentPanelComponent({
  testContent,
  onContentChange,
  onScore,
  isScoring,
  canScore,
  scoreResult,
}: TestContentPanelProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">Test Content</h2>

      <textarea
        value={testContent}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder="Paste content to score against your brand voice..."
        rows={5}
        className="w-full px-4 py-2 border border-gray-200 rounded-lg resize-none mb-4"
      />

      <button
        onClick={onScore}
        disabled={isScoring || !canScore || !testContent.trim()}
        className="w-full py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300"
      >
        {isScoring ? 'Scoring...' : 'Score Content'}
      </button>

      {/* Score Results */}
      <AnimatePresence>
        {scoreResult && <ScoreResult score={scoreResult} />}
      </AnimatePresence>
    </div>
  )
}

export const TestContentPanel = memo(TestContentPanelComponent)
export default TestContentPanel
