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
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <BeakerIcon className="w-5 h-5" />
        Voice Training
      </h2>

      <div className="space-y-4">
        {/* Training Status */}
        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          {trainingStatus === 'trained' ? (
            <CheckCircleIcon className="w-6 h-6 text-green-500" />
          ) : (
            <div className="w-6 h-6 rounded-full bg-gray-300" />
          )}
          <div>
            <p className="font-medium capitalize">{trainingStatus}</p>
            <p className="text-sm text-gray-500">
              {sampleCount} sample{sampleCount !== 1 ? 's' : ''} available
            </p>
          </div>
        </div>

        <button
          onClick={onTrain}
          disabled={isTraining || sampleCount === 0}
          className="w-full py-3 bg-gradient-to-r from-amber-600 to-amber-600 text-white rounded-lg hover:from-amber-700 hover:to-amber-700 disabled:from-gray-400 disabled:to-gray-400 font-medium"
        >
          {isTraining ? 'Training...' : 'Train Voice'}
        </button>

        {fingerprint && (
          <div className="mt-4 p-4 bg-amber-50 rounded-lg">
            <h4 className="font-medium text-amber-900 mb-2">Voice Summary</h4>
            <p className="text-sm text-amber-800">{fingerprint.voice_summary}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Quality:</span>{' '}
                <span className="font-medium">
                  {Math.round(fingerprint.training_quality * 100)}%
                </span>
              </div>
              <div>
                <span className="text-gray-500">Samples:</span>{' '}
                <span className="font-medium">{fingerprint.sample_count}</span>
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
