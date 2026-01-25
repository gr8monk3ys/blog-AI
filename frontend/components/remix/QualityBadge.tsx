'use client'

import React from 'react'
import type { QualityScore } from '@/types/remix'

interface QualityBadgeProps {
  score: QualityScore
}

function QualityBadgeComponent({ score }: QualityBadgeProps) {
  const grade =
    score.overall >= 0.9
      ? 'A+'
      : score.overall >= 0.8
        ? 'A'
        : score.overall >= 0.7
          ? 'B'
          : score.overall >= 0.6
            ? 'C'
            : 'D'

  const color =
    score.overall >= 0.8
      ? 'bg-green-100 text-green-800'
      : score.overall >= 0.6
        ? 'bg-yellow-100 text-yellow-800'
        : 'bg-red-100 text-red-800'

  return (
    <span className={`px-2 py-1 rounded text-sm font-medium ${color}`}>
      {grade} ({Math.round(score.overall * 100)}%)
    </span>
  )
}

export const QualityBadge = React.memo(QualityBadgeComponent)
