'use client'

import React, { memo } from 'react'
import { BeakerIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import type { VoiceFingerprint, TrainingStatus } from '@/types/brand'

interface TrainingPanelProps {
  trainingStatus: TrainingStatus
  sampleCount: number
  fingerprint: VoiceFingerprint | null
  isTraining: boolean
  onTrain: () => void
}

function TrainingPanelComponent({
  trainingStatus,
  sampleCount,
  fingerprint,
  isTraining,
  onTrain,
}: TrainingPanelProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
        <BeakerIcon className="w-5 h-5" />
        Voice Training
      </h2>

      <div className="space-y-4">
        {/* Training Status */}
        <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          {trainingStatus === 'trained' ? (
            <CheckCircleIcon className="w-6 h-6 text-emerald-500" />
          ) : (
            <div className="w-6 h-6 rounded-full bg-gray-300 dark:bg-gray-600" />
          )}
          <div>
            <p className="font-medium capitalize text-gray-900 dark:text-gray-100">{trainingStatus}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {sampleCount} sample{sampleCount !== 1 ? 's' : ''} available
            </p>
          </div>
        </div>

        <button
          onClick={onTrain}
          disabled={isTraining || sampleCount === 0}
          className="w-full py-3 bg-gradient-to-r from-amber-600 to-amber-700 text-white rounded-lg hover:from-amber-700 hover:to-amber-800 disabled:from-gray-400 disabled:to-gray-400 dark:disabled:from-gray-700 dark:disabled:to-gray-700 font-medium"
        >
          {isTraining ? 'Training...' : 'Train Voice'}
        </button>

        {fingerprint && (
          <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/30 rounded-lg">
            <h4 className="font-medium text-amber-900 dark:text-amber-300 mb-2">Voice Summary</h4>
            <p className="text-sm text-amber-800 dark:text-amber-200">{fingerprint.voice_summary}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Quality:</span>{' '}
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {Math.round(fingerprint.training_quality * 100)}%
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Samples:</span>{' '}
                <span className="font-medium text-gray-900 dark:text-gray-100">{fingerprint.sample_count}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export const TrainingPanel = memo(TrainingPanelComponent)
export default TrainingPanel
