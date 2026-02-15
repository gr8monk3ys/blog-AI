'use client'

import { useState, useEffect, useCallback } from 'react'
import { AnimatePresence } from 'framer-motion'
import { API_ENDPOINTS, apiFetch } from '@/lib/api'
import { useLlmConfig } from '@/hooks/useLlmConfig'
import ErrorBoundary from '@/components/ErrorBoundary'
import {
  SourceContentForm,
  ContentAnalysisPanel,
  FormatSelector,
  ResultsPanel,
} from '@/components/remix'
import type {
  ContentFormatId,
  ContentFormatInfo,
  RemixRequest,
  RemixResponse,
  RemixPreviewResponse,
  ContentAnalysis,
  RemixedContent,
} from '@/types/remix'
import type { LlmProviderType } from '@/types/llm'

function RemixPageContent() {
  // State
  const [formats, setFormats] = useState<ContentFormatInfo[]>([])
  const [selectedFormats, setSelectedFormats] = useState<ContentFormatId[]>([])
  const [sourceContent, setSourceContent] = useState<string>('')
  const [sourceTitle, setSourceTitle] = useState<string>('')
  const [analysis, setAnalysis] = useState<ContentAnalysis | null>(null)
  const [previews, setPreviews] = useState<Map<ContentFormatId, RemixPreviewResponse>>(new Map())
  const [results, setResults] = useState<RemixedContent[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isTransforming, setIsTransforming] = useState(false)
  const [selectedResult, setSelectedResult] = useState<RemixedContent | null>(null)
  const [error, setError] = useState<string | null>(null)

  const {
    config: llmConfig,
    availableProviders,
    defaultProvider,
    error: llmConfigError,
  } = useLlmConfig()
  const [provider, setProvider] = useState<LlmProviderType>('openai')
  const [providerTouched, setProviderTouched] = useState(false)

  useEffect(() => {
    if (!providerTouched) setProvider(defaultProvider)
  }, [defaultProvider, providerTouched])

  useEffect(() => {
    if (!availableProviders.includes(provider)) setProvider(defaultProvider)
  }, [availableProviders, defaultProvider, provider])

  // Fetch available formats on mount
  useEffect(() => {
    const fetchFormats = async () => {
      try {
        const data = await apiFetch<ContentFormatInfo[]>(API_ENDPOINTS.remix.formats)
        setFormats(data)
      } catch (err) {
        console.error('Failed to fetch formats:', err)
        setError('Failed to load formats')
      }
    }
    fetchFormats()
  }, [])

  // Analyze content
  const analyzeContent = useCallback(async () => {
    if (!sourceContent.trim()) {
      setError('Please enter some content to analyze')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await apiFetch<{ success: boolean; analysis: ContentAnalysis }>(
        API_ENDPOINTS.remix.analyze,
        {
          method: 'POST',
          body: JSON.stringify({
            source_content: {
              title: sourceTitle || 'Untitled',
              body: sourceContent,
            },
            provider,
          }),
        }
      )

      if (response.success) {
        setAnalysis(response.analysis)
        // Auto-select suggested formats
        setSelectedFormats(response.analysis.suggested_formats.slice(0, 3))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }, [sourceContent, sourceTitle, provider])

  // Preview a format
  const previewFormat = useCallback(async (formatId: ContentFormatId) => {
    try {
      const response = await apiFetch<RemixPreviewResponse>(
        API_ENDPOINTS.remix.preview,
        {
          method: 'POST',
          body: JSON.stringify({
            source_content: {
              title: sourceTitle || 'Untitled',
              body: sourceContent,
            },
            target_format: formatId,
            provider,
          }),
        }
      )
      setPreviews(prev => new Map(prev).set(formatId, response))
    } catch (err) {
      console.error(`Preview failed for ${formatId}:`, err)
    }
  }, [sourceContent, sourceTitle, provider])

  // Toggle format selection
  const toggleFormat = useCallback((formatId: ContentFormatId) => {
    setSelectedFormats(prev => {
      if (prev.includes(formatId)) {
        return prev.filter(f => f !== formatId)
      }
      if (prev.length >= 6) {
        setError('Maximum 6 formats per remix')
        return prev
      }
      // Preview when selecting
      if (!previews.has(formatId)) {
        previewFormat(formatId)
      }
      return [...prev, formatId]
    })
  }, [previews, previewFormat])

  // Transform content
  const transformContent = useCallback(async () => {
    if (selectedFormats.length === 0) {
      setError('Please select at least one target format')
      return
    }

    setIsTransforming(true)
    setError(null)

    try {
      const request: RemixRequest = {
        source_content: {
          title: sourceTitle || 'Untitled',
          body: sourceContent,
        },
        target_formats: selectedFormats,
        preserve_voice: true,
        conversation_id: crypto.randomUUID(),
        provider,
      }

      const response = await apiFetch<RemixResponse>(
        API_ENDPOINTS.remix.transform,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      )

      if (response.success) {
        setResults(response.remixed_content)
        setAnalysis(response.source_analysis)
        const firstResult = response.remixed_content[0]
        if (firstResult) {
          setSelectedResult(firstResult)
        }
      } else {
        setError(response.message || 'Transformation failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transformation failed')
    } finally {
      setIsTransforming(false)
    }
  }, [selectedFormats, sourceTitle, sourceContent, provider])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Content Remix Engine</h1>
          <p className="mt-2 text-gray-600">
            Transform your content into multiple formats with one click
          </p>
        </div>

        {/* Error Alert */}
        <AnimatePresence>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
              <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">
                x
              </button>
            </div>
          )}
        </AnimatePresence>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Input */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold mb-4">Model Provider</h2>
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-gray-700 w-20">Provider</label>
                <select
                  value={provider}
                  onChange={(e) => {
                    setProviderTouched(true)
                    setProvider(e.target.value as LlmProviderType)
                  }}
                  className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {availableProviders.map((p) => {
                    const model = llmConfig?.models?.[p]
                    const label = p === 'openai'
                      ? `OpenAI${model ? ` (${model})` : ''}`
                      : p === 'anthropic'
                        ? `Anthropic${model ? ` (${model})` : ''}`
                        : `Gemini${model ? ` (${model})` : ''}`
                    return (
                      <option key={p} value={p}>
                        {label}
                      </option>
                    )
                  })}
                </select>
              </div>
              {llmConfigError && (
                <p className="mt-2 text-xs text-amber-700">
                  {llmConfigError}. Showing default providers.
                </p>
              )}
            </div>

            <SourceContentForm
              sourceTitle={sourceTitle}
              sourceContent={sourceContent}
              isAnalyzing={isAnalyzing}
              onTitleChange={setSourceTitle}
              onContentChange={setSourceContent}
              onAnalyze={analyzeContent}
            />

            <AnimatePresence>
              {analysis && <ContentAnalysisPanel analysis={analysis} />}
            </AnimatePresence>

            <FormatSelector
              formats={formats}
              selectedFormats={selectedFormats}
              previews={previews}
              isTransforming={isTransforming}
              onToggleFormat={toggleFormat}
              onTransform={transformContent}
            />
          </div>

          {/* Right Panel - Results */}
          <div className="space-y-6">
            <ResultsPanel
              results={results}
              formats={formats}
              selectedResult={selectedResult}
              onSelectResult={setSelectedResult}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default function RemixPage() {
  return (
    <ErrorBoundary>
      <RemixPageContent />
    </ErrorBoundary>
  )
}
