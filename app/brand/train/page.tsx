'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { AnimatePresence, motion } from 'framer-motion'
import { API_ENDPOINTS, apiFetch } from '@/lib/api'
import { useConfirmModal } from '@/hooks/useConfirmModal'
import ErrorBoundary from '@/components/ErrorBoundary'
import {
  ProfileSelector,
  SampleForm,
  SamplesList,
  TrainingPanel,
  TestContentPanel,
} from '@/components/brand'
import type {
  VoiceFingerprint,
  VoiceScore,
  TrainingStatus,
} from '@/types/brand'
import { ArrowLeftIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'

interface SampleListItem {
  id: string
  title?: string
  word_count: number
  content_type: string
  is_analyzed: boolean
  quality_score: number
  is_primary_example: boolean
}

function VoiceTrainingPageContent() {
  // Confirm modal hook
  const { confirm, ConfirmModalComponent } = useConfirmModal()

  // State
  const [profileId, setProfileId] = useState<string>('')
  const [samples, setSamples] = useState<SampleListItem[]>([])
  const [fingerprint, setFingerprint] = useState<VoiceFingerprint | null>(null)
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus>('untrained')
  const [isLoading, setIsLoading] = useState(false)
  const [isTraining, setIsTraining] = useState(false)
  const [isScoring, setIsScoring] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [newSampleContent, setNewSampleContent] = useState('')
  const [newSampleTitle, setNewSampleTitle] = useState('')
  const [newSampleType, setNewSampleType] = useState<string>('text')

  // Test content state
  const [testContent, setTestContent] = useState('')
  const [scoreResult, setScoreResult] = useState<VoiceScore | null>(null)

  // Load samples for a profile
  const loadSamples = useCallback(async (id: string) => {
    if (!id) return
    setIsLoading(true)
    setError(null)

    try {
      const response = await apiFetch<{
        profile_id: string
        sample_count: number
        samples: SampleListItem[]
      }>(API_ENDPOINTS.brandVoice.samplesByProfile(id))
      setSamples(response.samples)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load samples')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load training status
  const loadStatus = useCallback(async (id: string) => {
    if (!id) return
    try {
      const response = await apiFetch<{
        status: TrainingStatus
        has_fingerprint: boolean
        voice_summary?: string
      }>(API_ENDPOINTS.brandVoice.status(id))
      setTrainingStatus(response.status)

      if (response.has_fingerprint) {
        const fpResponse = await apiFetch<{ fingerprint: VoiceFingerprint }>(
          API_ENDPOINTS.brandVoice.fingerprint(id)
        )
        setFingerprint(fpResponse.fingerprint)
      }
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }, [])

  // Handle profile ID change
  const handleProfileIdSubmit = useCallback(() => {
    if (profileId.trim()) {
      loadSamples(profileId)
      loadStatus(profileId)
    }
  }, [profileId, loadSamples, loadStatus])

  // Add a new sample
  const addSample = useCallback(async () => {
    if (!profileId || !newSampleContent.trim()) {
      setError('Please enter content for the sample')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await apiFetch(API_ENDPOINTS.brandVoice.samples, {
        method: 'POST',
        body: JSON.stringify({
          profile_id: profileId,
          content: newSampleContent,
          content_type: newSampleType,
          title: newSampleTitle || undefined,
        }),
      })

      setNewSampleContent('')
      setNewSampleTitle('')
      await loadSamples(profileId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add sample')
    } finally {
      setIsLoading(false)
    }
  }, [profileId, newSampleContent, newSampleType, newSampleTitle, loadSamples])

  // Delete a sample
  const deleteSample = useCallback(async (sampleId: string) => {
    const confirmed = await confirm({
      title: 'Delete Sample',
      message: 'Are you sure you want to delete this sample? This action cannot be undone.',
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'danger',
    })

    if (!confirmed) return

    try {
      await apiFetch(API_ENDPOINTS.brandVoice.deleteSample(profileId, sampleId), {
        method: 'DELETE',
      })
      await loadSamples(profileId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete sample')
    }
  }, [confirm, profileId, loadSamples])

  // Train the voice
  const trainVoice = useCallback(async () => {
    if (!profileId || samples.length === 0) {
      setError('Add at least one sample before training')
      return
    }

    setIsTraining(true)
    setTrainingStatus('training')
    setError(null)

    try {
      const response = await apiFetch<{
        success: boolean
        fingerprint: VoiceFingerprint
        training_quality: number
        voice_summary: string
      }>(API_ENDPOINTS.brandVoice.train, {
        method: 'POST',
        body: JSON.stringify({ profile_id: profileId }),
      })

      if (response.success) {
        setFingerprint(response.fingerprint)
        setTrainingStatus('trained')
      }
    } catch (err) {
      setTrainingStatus('failed')
      setError(err instanceof Error ? err.message : 'Training failed')
    } finally {
      setIsTraining(false)
    }
  }, [profileId, samples.length])

  // Score test content
  const scoreContent = useCallback(async () => {
    if (!profileId || !testContent.trim() || !fingerprint) {
      setError('Enter content to test and ensure voice is trained')
      return
    }

    setIsScoring(true)
    setError(null)

    try {
      const response = await apiFetch<{
        success: boolean
        score: VoiceScore
        grade: string
        passed: boolean
      }>(API_ENDPOINTS.brandVoice.score, {
        method: 'POST',
        body: JSON.stringify({
          profile_id: profileId,
          content: testContent,
          content_type: 'text',
        }),
      })

      if (response.success) {
        setScoreResult(response.score)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scoring failed')
    } finally {
      setIsScoring(false)
    }
  }, [profileId, testContent, fingerprint])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Confirm Modal */}
      <ConfirmModalComponent />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/brand"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Profiles
          </Link>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Voice Training Studio</h1>
          <p className="mt-2 text-gray-600">
            Train your brand voice with content samples for consistent AI-generated content
          </p>
        </div>

        {/* Error Alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2"
            >
              <ExclamationCircleIcon className="w-5 h-5" />
              {error}
              <button onClick={() => setError(null)} className="ml-auto text-red-500">
                &times;
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Profile Selection */}
        <ProfileSelector
          profileId={profileId}
          onProfileIdChange={setProfileId}
          onLoad={handleProfileIdSubmit}
          isLoading={isLoading}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Samples */}
          <div className="space-y-6">
            <SampleForm
              title={newSampleTitle}
              content={newSampleContent}
              contentType={newSampleType}
              isLoading={isLoading}
              onTitleChange={setNewSampleTitle}
              onContentChange={setNewSampleContent}
              onContentTypeChange={setNewSampleType}
              onSubmit={addSample}
            />

            <SamplesList samples={samples} onDelete={deleteSample} />
          </div>

          {/* Right Column - Training & Testing */}
          <div className="space-y-6">
            <TrainingPanel
              trainingStatus={trainingStatus}
              sampleCount={samples.length}
              fingerprint={fingerprint}
              isTraining={isTraining}
              onTrain={trainVoice}
            />

            <TestContentPanel
              testContent={testContent}
              onContentChange={setTestContent}
              onScore={scoreContent}
              isScoring={isScoring}
              canScore={!!fingerprint}
              scoreResult={scoreResult}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default function VoiceTrainingPage() {
  return (
    <ErrorBoundary>
      <VoiceTrainingPageContent />
    </ErrorBoundary>
  )
}
