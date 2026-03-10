'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import Link from 'next/link'
import { v4 as uuidv4 } from 'uuid'
import { m, AnimatePresence } from 'framer-motion'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  PlusIcon,
  ArrowPathIcon,
  CurrencyDollarIcon,
  ServerStackIcon,
} from '@heroicons/react/24/outline'
import {
  BulkGenerationItem,
  BulkJobStartResponse,
  CSVRow,
  ParsedCSVData,
  ProviderStrategy,
  CostEstimate,
  ExportFormat,
  EnhancedBatchStatus,
  EnhancedBatchItemResult,
} from '../../types/bulk'
import UsageIndicator, { useUsageCheck } from '../../components/UsageIndicator'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { useLlmConfig } from '../../hooks/useLlmConfig'
import type { LlmProviderType } from '../../types/llm'

const TONE_OPTIONS = [
  { value: 'informative', label: 'Informative' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'technical', label: 'Technical' },
]

const PROVIDER_META: Record<LlmProviderType, { label: string; cost: string }> = {
  openai: { label: 'OpenAI', cost: '$$$' },
  anthropic: { label: 'Anthropic', cost: '$$' },
  gemini: { label: 'Gemini', cost: '$' },
}

const STRATEGY_OPTIONS: { value: ProviderStrategy; label: string; description: string }[] = [
  { value: 'single', label: 'Single Provider', description: 'Use one provider for all items' },
  { value: 'round_robin', label: 'Round Robin', description: 'Rotate through all providers' },
  { value: 'cost_optimized', label: 'Cost Optimized', description: 'Use cheapest provider available' },
  { value: 'quality_optimized', label: 'Quality Optimized', description: 'Use highest quality provider' },
]

const EXPORT_OPTIONS: { value: ExportFormat; label: string; icon: string }[] = [
  { value: 'json', label: 'JSON', icon: '{ }' },
  { value: 'csv', label: 'CSV', icon: '📊' },
  { value: 'markdown', label: 'Markdown', icon: '📝' },
  { value: 'zip', label: 'ZIP (all files)', icon: '📦' },
]

interface BulkDraftItem extends BulkGenerationItem {
  localId: string
}

function createDraftItem(
  topic = '',
  keywords: string[] = [],
  tone = 'informative'
): BulkDraftItem {
  return {
    localId: uuidv4(),
    topic,
    keywords,
    tone,
  }
}

function parseCSV(csvText: string): ParsedCSVData {
  const lines = csvText.trim().split('\n')
  const errors: string[] = []
  const rows: CSVRow[] = []

  if (lines.length === 0) {
    return { rows: [], errors: ['Empty CSV file'], headers: [] }
  }

  // Parse header
  const headerLine = lines[0]
  if (!headerLine) {
    return { rows: [], errors: ['Empty CSV file'], headers: [] }
  }
  const headers = headerLine.split(',').map((h) => h.trim().toLowerCase())

  const topicIndex = headers.indexOf('topic')
  const keywordsIndex = headers.indexOf('keywords')
  const toneIndex = headers.indexOf('tone')

  if (topicIndex === -1) {
    errors.push('CSV must have a "topic" column')
    return { rows: [], errors, headers }
  }

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]
    if (!line || !line.trim()) continue

    // Simple CSV parsing (doesn't handle quoted commas)
    const values = line.split(',').map((v) => v.trim())

    const topic = values[topicIndex]
    if (!topic) {
      errors.push(`Row ${i + 1}: Missing topic`)
      continue
    }

    rows.push({
      topic,
      keywords: keywordsIndex !== -1 ? values[keywordsIndex] : undefined,
      tone: toneIndex !== -1 ? values[toneIndex] : undefined,
    })
  }

  return { rows, errors, headers }
}

function useBulkGenerationPageView() {
  const [conversationId] = useState(() => uuidv4())
  const [items, setItems] = useState<BulkDraftItem[]>([])
  const [sharedTone, setSharedTone] = useState('informative')
  const [useResearch, setUseResearch] = useState(false)
  const [proofread, setProofread] = useState(true)
  const [humanize, setHumanize] = useState(true)
  const [parallelLimit, setParallelLimit] = useState(3)

  // Tier 1 features: Provider and cost tracking
  const [providerStrategy, setProviderStrategy] = useState<ProviderStrategy>('single')
  const { config: llmConfig, availableProviders, defaultProvider } = useLlmConfig()
  const [preferredProvider, setPreferredProvider] = useState<LlmProviderType>('openai')
  const [providerTouched, setProviderTouched] = useState(false)
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null)
  const [providersUsed, setProvidersUsed] = useState<Record<string, number>>({})
  const [actualCost, setActualCost] = useState(0)
  const [showExportMenu, setShowExportMenu] = useState(false)

  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<EnhancedBatchStatus | null>(null)
  const [results, setResults] = useState<EnhancedBatchItemResult[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activationHint, setActivationHint] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const { canGenerate, checkUsage } = useUsageCheck()

  useEffect(() => {
    if (!providerTouched) setPreferredProvider(defaultProvider)
  }, [defaultProvider, providerTouched])

  useEffect(() => {
    if (!availableProviders.includes(preferredProvider)) setPreferredProvider(defaultProvider)
  }, [availableProviders, defaultProvider, preferredProvider])

  useEffect(() => {
    if (typeof window === 'undefined' || items.length > 0) return

    const params = new URLSearchParams(window.location.search)
    if (params.get('source') !== 'onboarding') return

    const topic = params.get('topic')?.trim() || ''
    const tone = params.get('tone')?.trim() || sharedTone
    const contentType = params.get('contentType')?.trim()

    if (topic) {
      setItems([createDraftItem(topic, [], tone)])
    }

    if (tone) {
      setSharedTone(tone)
    }

    if (contentType === 'marketing-copy') {
      setUseResearch(true)
      setHumanize(true)
    }

    setActivationHint(
      'Your first batch was prefilled from onboarding. Add a few more topics or run this one now to complete the activation loop.'
    )
  }, [items.length, sharedTone])

  // Add a single item manually
  const addItem = () => {
    setItems((prev) => [...prev, createDraftItem('', [], sharedTone)])
  }

  // Remove an item
  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index))
  }

  // Update an item
  const updateItem = (index: number, field: keyof BulkGenerationItem, value: string | string[]) => {
    const newItems = [...items]
    const currentItem = newItems[index]
    if (!currentItem) return

    if (field === 'keywords' && typeof value === 'string') {
      newItems[index] = {
        ...currentItem,
        keywords: value.split(',').map((k) => k.trim()).filter(Boolean),
      }
    } else if (field === 'topic' && typeof value === 'string') {
      newItems[index] = { ...currentItem, topic: value }
    } else if (field === 'tone' && typeof value === 'string') {
      newItems[index] = { ...currentItem, tone: value }
    }
    setItems(newItems)
  }

  // Estimate cost when items change
  const estimateCost = useCallback(async () => {
    if (items.length === 0) {
      setCostEstimate(null)
      return
    }

    try {
      const response = await fetch(
	        `${API_ENDPOINTS.batch.estimate}?provider_strategy=${providerStrategy}&preferred_provider=${preferredProvider}&research_enabled=${useResearch}`,
	        {
	          method: 'POST',
	          headers: await getDefaultHeaders(),
	          body: JSON.stringify(items.map(item => ({
	            topic: item.topic,
	            keywords: item.keywords,
	            tone: item.tone || sharedTone,
            content_type: 'blog',
          }))),
        }
      )

      if (response.ok) {
        const estimate: CostEstimate = await response.json()
        setCostEstimate(estimate)
      }
    } catch (err) {
      console.error('Failed to estimate cost:', err)
    }
  }, [items, providerStrategy, preferredProvider, useResearch, sharedTone])

  // Re-estimate cost when inputs change (debounced)
  useEffect(() => {
    if (isProcessing) return
    const timeout = setTimeout(() => {
      void estimateCost()
    }, 400)
    return () => clearTimeout(timeout)
  }, [estimateCost, isProcessing])

  // Retry failed items
  const retryFailed = async () => {
    if (!jobId || !status?.can_retry_failed) return

    const failedIndices = results
      .filter(r => !r.success)
      .map(r => r.index)

    if (failedIndices.length === 0) {
      setError('No failed items to retry')
      return
    }

	    try {
	      const response = await fetch(API_ENDPOINTS.batch.retry(jobId), {
	        method: 'POST',
	        headers: await getDefaultHeaders(),
	        body: JSON.stringify({
	          item_indices: failedIndices,
	          change_provider: preferredProvider,
	        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start retry')
      }

      const data = await response.json()
      setJobId(data.retry_job_id)
      setStatus(null)
      setResults([])
      setProvidersUsed({})
      setActualCost(0)
      setIsProcessing(true)
      startPolling(data.retry_job_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry failed items')
    }
  }

  // Export results in different formats
  const exportResults = async (format: ExportFormat) => {
    if (!jobId) return

	    try {
	      const response = await fetch(API_ENDPOINTS.batch.export(jobId, format), {
	        headers: await getDefaultHeaders(),
	      })

      if (!response.ok) {
        throw new Error('Failed to export results')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `batch-${jobId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`
      a.click()
      URL.revokeObjectURL(url)
      setShowExportMenu(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export results')
    }
  }

  // Handle CSV file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const { rows, errors } = parseCSV(text)

      if (errors.length > 0) {
        setError(`CSV parsing errors:\n${errors.join('\n')}`)
      } else {
        setError(null)
      }

      if (rows.length > 0) {
        const newItems: BulkDraftItem[] = rows.map((row) =>
          createDraftItem(
            row.topic,
            row.keywords ? row.keywords.split(';').map((k) => k.trim()) : [],
            row.tone || sharedTone
          )
        )
        setItems((prev) => [...prev, ...newItems])
      }
    }
    reader.readAsText(file)

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Start bulk generation
  const startGeneration = async () => {
    if (items.length === 0) {
      setError('Add at least one item to generate')
      return
    }

    // Check usage before starting
    const hasUsage = await checkUsage()
    if (!hasUsage) {
      setError('You have reached your usage limit. Upgrade to continue.')
      return
    }

    setIsProcessing(true)
    setError(null)
    setResults([])

	    try {
	      const fallbackProviders = availableProviders.filter((p) => p !== preferredProvider)

	      const response = await fetch(API_ENDPOINTS.batch.create, {
	        method: 'POST',
	        headers: await getDefaultHeaders(),
	        body: JSON.stringify({
	          items: items.map((item) => ({
	            topic: item.topic,
	            keywords: item.keywords,
	            tone: item.tone || sharedTone,
	            content_type: 'blog',
	          })),
	          provider_strategy: providerStrategy,
	          preferred_provider: preferredProvider,
	          fallback_providers: fallbackProviders,
	          parallel_limit: parallelLimit,
	          research_enabled: useResearch,
	          proofread_enabled: proofread,
	          humanize_enabled: humanize,
	          conversation_id: conversationId,
	          name: `Bulk Generation (${items.length})`,
	        }),
	      })

	      if (!response.ok) {
	        const errorData = await response.json()
	        throw new Error(
	          errorData.detail?.error || errorData.detail || 'Failed to start batch generation'
	        )
	      }

	      const data: BulkJobStartResponse = await response.json()
	      setJobId(data.job_id)
	      setStatus(null)
	      setProvidersUsed({})
	      setActualCost(0)

	      // Start polling for status
	      startPolling(data.job_id)
	    } catch (err) {
	      setError(err instanceof Error ? err.message : 'Failed to start batch generation')
	      setIsProcessing(false)
	    }
	  }

  // Poll for job status
  const startPolling = (id: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

	    const poll = async () => {
	      try {
	        const response = await fetch(API_ENDPOINTS.batch.status(id), {
	          headers: await getDefaultHeaders(),
	        })

        if (!response.ok) {
          throw new Error('Failed to fetch status')
        }

	        const statusData: EnhancedBatchStatus = await response.json()
	        setStatus(statusData)
	        setProvidersUsed(statusData.providers_used || {})
	        setActualCost(statusData.actual_cost_usd || 0)

	        if (['completed', 'failed', 'cancelled', 'partial'].includes(statusData.status)) {
	          // Job finished, fetch results
	          stopPolling()
	          fetchResults(id)
	        }
	      } catch (err) {
	        console.error('Error polling status:', err)
      }
    }

    poll() // Initial poll
    pollIntervalRef.current = setInterval(poll, 2000)
  }

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  // Fetch final results
	  const fetchResults = async (id: string) => {
	    try {
	      const response = await fetch(API_ENDPOINTS.batch.results(id), {
	        headers: await getDefaultHeaders(),
	      })

      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }

	      const data = await response.json()
	      setResults(data.results || [])
	      setProvidersUsed(data.providers_used || {})
	      setActualCost(data.total_cost_usd || 0)
	    } catch (err) {
	      setError(err instanceof Error ? err.message : 'Failed to fetch results')
	    } finally {
	      setIsProcessing(false)
	    }
	  }

  // Cancel job
	  const cancelJob = async () => {
	    if (!jobId) return

	    try {
	      await fetch(API_ENDPOINTS.batch.cancel(jobId), {
	        method: 'POST',
	        headers: await getDefaultHeaders(),
	      })
	      stopPolling()
	      setIsProcessing(false)
	    } catch (err) {
	      console.error('Error cancelling job:', err)
	    }
	  }

  // Download CSV template
  const downloadTemplate = () => {
    const template = 'topic,keywords,tone\n"Example blog topic","keyword1;keyword2;keyword3","informative"\n"Another topic","seo;marketing","professional"'
    const blob = new Blob([template], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bulk-generation-template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      <SiteHeader />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">
              Bulk SEO Content Workflow
            </h1>
            <p className="text-amber-100">
              Queue multiple topics, compare provider cost, and generate campaign-ready drafts
              faster than prompt-by-prompt writing.
            </p>
            <div className="mt-4 flex flex-wrap gap-3 text-sm">
              <span className="rounded-full bg-white/15 px-3 py-1">Best for publishing calendars</span>
              <span className="rounded-full bg-white/15 px-3 py-1">Pairs with Brand Voice</span>
              <span className="rounded-full bg-white/15 px-3 py-1">Strongest Pro workflow today</span>
            </div>
          </m.div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activationHint && (
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6 rounded-2xl border border-green-200 bg-green-50/80 p-5 text-sm text-green-900 dark:border-green-900/40 dark:bg-green-950/30 dark:text-green-100"
          >
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <p>{activationHint}</p>
              <button
                type="button"
                onClick={() => setActivationHint(null)}
                className="rounded-lg border border-green-300 px-3 py-2 font-medium text-green-800 transition-colors hover:bg-green-100 dark:border-green-800 dark:text-green-200 dark:hover:bg-green-900/30"
              >
                Dismiss
              </button>
            </div>
          </m.div>
        )}

        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
          className="mb-6 rounded-2xl border border-amber-200 bg-amber-50/80 p-5 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-100"
        >
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="font-semibold">Recommended workflow</p>
              <p className="mt-1 text-amber-800 dark:text-amber-200">
                Create a brand profile first, then use bulk generation for repeatable SEO content
                batches. That is the clearest upgrade path from free usage to a paid workflow.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/brand"
                className="inline-flex items-center justify-center rounded-lg bg-amber-600 px-4 py-2 font-medium text-white transition-colors hover:bg-amber-700"
              >
                Open Brand Voice
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center justify-center rounded-lg border border-amber-300 px-4 py-2 font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-800 dark:text-amber-200 dark:hover:bg-amber-900/30"
              >
                Compare Plans
              </Link>
            </div>
          </div>
        </m.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Items */}
          <div className="lg:col-span-2 space-y-6">
            {/* CSV Upload */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Upload CSV
              </h2>
              <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                Use one row per topic to turn a content plan into a production run. Start with
                the template if you want the fastest path.
              </p>
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center hover:border-amber-400 dark:hover:border-amber-500 transition-colors">
                <ArrowUpTrayIcon className="w-8 h-8 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Drop a CSV file here, or click to browse
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="csv-upload"
                />
                <label
                  htmlFor="csv-upload"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                >
                  Select CSV File
                </label>
                <button
                  onClick={downloadTemplate}
                  className="ml-2 text-sm text-amber-600 hover:text-amber-700"
                >
                  Download template
                </button>
              </div>
            </m.div>

            {/* Items List */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Topics ({items.length})
                </h2>
                <button
                  onClick={addItem}
                  disabled={isProcessing}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-amber-600 hover:text-amber-700 disabled:opacity-50"
                >
                  <PlusIcon className="w-4 h-4" />
                  Add Topic
                </button>
              </div>

              {items.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                  <p>No topics added yet.</p>
                  <p className="text-sm">Upload a CSV or add topics manually to build a batch.</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  <AnimatePresence>
                    {items.map((item, index) => (
                      <m.div
                        key={item.localId}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                      >
                        <div className="flex items-start gap-4">
                          <span className="text-sm font-medium text-gray-500 pt-2">
                            {index + 1}.
                          </span>
                          <div className="flex-1 space-y-3">
                            <input
                              type="text"
                              value={item.topic}
                              onChange={(e) => updateItem(index, 'topic', e.target.value)}
                              placeholder="Enter topic..."
                              disabled={isProcessing}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                            />
                            <div className="flex gap-3">
                              <input
                                type="text"
                                value={item.keywords.join(', ')}
                                onChange={(e) => updateItem(index, 'keywords', e.target.value)}
                                placeholder="Keywords (comma separated)"
                                disabled={isProcessing}
                                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                              />
                              <select
                                value={item.tone}
                                onChange={(e) => updateItem(index, 'tone', e.target.value)}
                                disabled={isProcessing}
                                className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                              >
                                {TONE_OPTIONS.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </div>
                          <button
                            onClick={() => removeItem(index)}
                            disabled={isProcessing}
                            className="p-2 text-gray-400 hover:text-red-500 disabled:opacity-50"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
                        </div>

                        {/* Show result if available */}
                        {results[index] && (
                          <div className={`mt-3 p-3 rounded-lg ${
                            results[index].success
                              ? 'bg-green-50 border border-green-200'
                              : 'bg-red-50 border border-red-200'
                          }`}>
                            <div className="flex items-center gap-2">
                              {results[index].success ? (
                                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                              ) : (
                                <XCircleIcon className="w-5 h-5 text-red-500" />
                              )}
                              <span className={`text-sm font-medium ${
                                results[index].success ? 'text-green-700' : 'text-red-700'
                              }`}>
                                {results[index].success
                                  ? `Generated: ${results[index].content?.title}`
                                  : `Error: ${results[index].error}`}
                              </span>
                            </div>
                          </div>
                        )}
                      </m.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </m.div>
          </div>

          {/* Right Column - Settings and Actions */}
          <div className="space-y-6">
            {/* Settings */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Settings
              </h2>
              <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                These controls define the economics of the batch: cost, speed, research depth,
                and editorial cleanup.
              </p>

              <div className="space-y-4">
                {/* Provider Strategy */}
                <div>
                  <label htmlFor="provider-strategy" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    <ServerStackIcon className="w-4 h-4 inline mr-1" />
                    Provider Strategy
                  </label>
                  <select
                    id="provider-strategy"
                    value={providerStrategy}
                    onChange={(e) => {
                      setProviderStrategy(e.target.value as ProviderStrategy)
                      setCostEstimate(null)
                    }}
                    disabled={isProcessing}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                  >
                    {STRATEGY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    {STRATEGY_OPTIONS.find(s => s.value === providerStrategy)?.description}
                  </p>
                </div>

                {/* Preferred Provider */}
                {providerStrategy === 'single' && (
                  <div>
                    <label htmlFor="preferred-provider" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Provider
                    </label>
                    <select
                      id="preferred-provider"
                      value={preferredProvider}
                      onChange={(e) => {
                        setProviderTouched(true)
                        setPreferredProvider(e.target.value as LlmProviderType)
                        setCostEstimate(null)
                      }}
                      disabled={isProcessing}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                    >
                      {availableProviders.map((p) => {
                        const meta = PROVIDER_META[p]
                        const model = llmConfig?.models?.[p]
                        const label = `${meta?.label || p}${model ? ` (${model})` : ''} (${meta?.cost || ''})`
                        return (
                          <option key={p} value={p}>
                            {label.trim()}
                          </option>
                        )
                      })}
                    </select>
                  </div>
                )}

                <div>
                  <label htmlFor="default-tone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Default Tone
                  </label>
                  <select
                    id="default-tone"
                    value={sharedTone}
                    onChange={(e) => setSharedTone(e.target.value)}
                    disabled={isProcessing}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                  >
                    {TONE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="parallel-limit" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Parallel Generations
                  </label>
                  <select
                    id="parallel-limit"
                    value={parallelLimit}
                    onChange={(e) => setParallelLimit(Number(e.target.value))}
                    disabled={isProcessing}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
                  >
                    {[1, 2, 3, 5, 10].map((n) => (
                      <option key={n} value={n}>
                        {n} at a time
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-3 pt-2">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={useResearch}
                      onChange={(e) => setUseResearch(e.target.checked)}
                      disabled={isProcessing}
                      className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Use web research</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={proofread}
                      onChange={(e) => setProofread(e.target.checked)}
                      disabled={isProcessing}
                      className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Proofread content</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={humanize}
                      onChange={(e) => setHumanize(e.target.checked)}
                      disabled={isProcessing}
                      className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Humanize content</span>
                  </label>
                </div>
              </div>
            </m.div>

            {/* Cost Estimate */}
            {costEstimate && items.length > 0 && !isProcessing && (
              <m.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl border border-green-200 dark:border-green-800 p-6"
              >
                <div className="flex items-center gap-2 mb-3">
                  <CurrencyDollarIcon className="w-5 h-5 text-green-600" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Cost Estimate
                  </h2>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Estimated Cost</span>
                    <span className="text-lg font-bold text-green-700">
                      ${costEstimate.estimated_cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>~{costEstimate.estimated_output_tokens.toLocaleString()} tokens</span>
                    <span>{Math.round(costEstimate.confidence * 100)}% confidence</span>
                  </div>
                  {costEstimate.provider_recommendations.length > 1 && (
                    <div className="mt-3 pt-3 border-t border-green-200 dark:border-green-800">
                      <p className="text-xs text-gray-500 mb-2">Provider comparison:</p>
                      <div className="space-y-1">
                        {costEstimate.provider_recommendations.slice(0, 3).map((rec) => (
                          <div key={rec.provider} className="flex items-center justify-between text-xs">
                            <span className="text-gray-600 dark:text-gray-400">{rec.display_name}</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">${rec.estimated_cost.toFixed(4)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </m.div>
            )}

            {/* Progress */}
            {status && isProcessing && (
              <m.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Progress
                </h2>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Status</span>
                    <span className="font-medium capitalize text-gray-900 dark:text-gray-100">
                      {status.status}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <m.div
                      initial={{ width: 0 }}
                      animate={{ width: `${status.progress_percentage}%` }}
                      className="bg-amber-500 h-3 rounded-full"
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                    <span>
                      {status.completed_items} / {status.total_items} completed
                    </span>
                    {status.failed_items > 0 && (
                      <span className="text-red-600">
                        {status.failed_items} failed
                      </span>
                    )}
                  </div>
                  {/* Provider usage */}
                  {Object.keys(providersUsed).length > 0 && (
                    <div className="pt-3 border-t border-gray-100 dark:border-gray-800">
                      <p className="text-xs text-gray-500 mb-2">Providers used:</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(providersUsed).map(([provider, count]) => (
                          <span
                            key={provider}
                            className="inline-flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-700 dark:text-gray-300"
                          >
                            {provider}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {actualCost > 0 && (
                    <div className="flex items-center justify-between text-sm pt-2">
                      <span className="text-gray-600 dark:text-gray-400">Cost so far</span>
                      <span className="font-medium text-green-600">
                        ${actualCost.toFixed(4)}
                      </span>
                    </div>
                  )}
                </div>
              </m.div>
            )}

            {/* Actions */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <div className="space-y-3">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-800/60 dark:text-gray-300">
                  <p className="font-medium text-gray-900 dark:text-gray-100">Who should upgrade to Pro?</p>
                  <p className="mt-1">
                    Teams running recurring batches with brand voice, higher monthly volume, and
                    fewer manual prompt edits.
                  </p>
                </div>
                {!canGenerate && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    Usage limit reached.{' '}
                    <Link href="/pricing" className="font-medium underline">
                      Upgrade your plan
                    </Link>{' '}
                    to continue.
                  </div>
                )}
                {isProcessing ? (
                  <button
                    onClick={cancelJob}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
                  >
                    <StopIcon className="w-5 h-5" />
                    Cancel Generation
                  </button>
                ) : (
                  <button
                    onClick={startGeneration}
                    disabled={items.length === 0 || !canGenerate}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlayIcon className="w-5 h-5" />
                    Generate {items.length} Post{items.length !== 1 ? 's' : ''}
                  </button>
                )}

                {results.length > 0 && (
                  <div className="relative">
                    <button
                      onClick={() => setShowExportMenu(!showExportMenu)}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <ArrowDownTrayIcon className="w-5 h-5" />
                      Export Results
                    </button>
                    {showExportMenu && (
                      <m.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-10"
                      >
                        {EXPORT_OPTIONS.map((option) => (
                          <button
                            key={option.value}
                            onClick={() => exportResults(option.value)}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-800 dark:text-gray-300 transition-colors"
                          >
                            <span className="text-lg">{option.icon}</span>
                            <span>{option.label}</span>
                          </button>
                        ))}
                      </m.div>
                    )}
                  </div>
                )}

                {/* Retry failed button */}
                {results.length > 0 && results.some(r => !r.success) && !isProcessing && (
                  <button
                    onClick={retryFailed}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-orange-300 bg-orange-50 text-orange-700 font-medium rounded-lg hover:bg-orange-100 transition-colors"
                  >
                    <ArrowPathIcon className="w-5 h-5" />
                    Retry {results.filter(r => !r.success).length} Failed
                  </button>
                )}

                {items.length > 0 && !isProcessing && (
                  <button
                    onClick={() => {
                      setItems([])
                      setResults([])
                      setStatus(null)
                    }}
                    className="w-full flex items-center justify-center gap-2 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                    Clear All
                  </button>
                )}
              </div>
            </m.div>

            {/* Error */}
            {error && (
              <m.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4"
              >
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-xs text-red-600 hover:text-red-800"
                >
                  Dismiss
                </button>
              </m.div>
            )}

            {/* Usage indicator */}
            <UsageIndicator />

            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Suggested operating flow
              </h2>
              <ol className="mt-4 space-y-3 text-sm text-gray-600 dark:text-gray-400">
                <li>1. Save one brand profile that reflects your real positioning.</li>
                <li>2. Import a week or month of topics with keywords via CSV.</li>
                <li>3. Run the batch, review the highest-value drafts, and publish faster.</li>
              </ol>
            </m.div>
          </div>
        </div>
      </div>

      <SiteFooter />
    </main>
  )
}

export default function BulkGenerationPageClient() {
  return useBulkGenerationPageView()
}
