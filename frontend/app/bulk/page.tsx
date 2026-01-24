'use client'

import { useState, useRef, useCallback } from 'react'
import Link from 'next/link'
import { v4 as uuidv4 } from 'uuid'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeftIcon,
  ArrowUpTrayIcon,
  DocumentTextIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  PlusIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import {
  BulkGenerationItem,
  BulkGenerationItemResult,
  BulkGenerationStatus,
  BulkJobStartResponse,
  CSVRow,
  ParsedCSVData,
} from '../../types/bulk'
import UsageIndicator, { useUsageCheck } from '../../components/UsageIndicator'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'

const TONE_OPTIONS = [
  { value: 'informative', label: 'Informative' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'technical', label: 'Technical' },
]

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

export default function BulkGenerationPage() {
  const [conversationId] = useState(uuidv4())
  const [items, setItems] = useState<BulkGenerationItem[]>([])
  const [sharedTone, setSharedTone] = useState('informative')
  const [useResearch, setUseResearch] = useState(false)
  const [proofread, setProofread] = useState(true)
  const [humanize, setHumanize] = useState(true)
  const [parallelLimit, setParallelLimit] = useState(3)

  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<BulkGenerationStatus | null>(null)
  const [results, setResults] = useState<BulkGenerationItemResult[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const { canGenerate, checkUsage } = useUsageCheck()

  // Add a single item manually
  const addItem = () => {
    setItems([
      ...items,
      { topic: '', keywords: [], tone: sharedTone },
    ])
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
        const newItems: BulkGenerationItem[] = rows.map((row) => ({
          topic: row.topic,
          keywords: row.keywords ? row.keywords.split(';').map((k) => k.trim()) : [],
          tone: row.tone || sharedTone,
        }))
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
      const response = await fetch(API_ENDPOINTS.bulk.generate, {
        method: 'POST',
        headers: getDefaultHeaders(),
        body: JSON.stringify({
          items: items.map((item) => ({
            ...item,
            tone: item.tone || sharedTone,
          })),
          tool_id: 'blog-post',
          research: useResearch,
          proofread,
          humanize,
          parallel_limit: parallelLimit,
          conversation_id: conversationId,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error || errorData.detail || 'Failed to start bulk generation')
      }

      const data: BulkJobStartResponse = await response.json()
      setJobId(data.job_id)

      // Start polling for status
      startPolling(data.job_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start bulk generation')
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
        const response = await fetch(API_ENDPOINTS.bulk.status(id), {
          headers: getDefaultHeaders(),
        })

        if (!response.ok) {
          throw new Error('Failed to fetch status')
        }

        const statusData: BulkGenerationStatus = await response.json()
        setStatus(statusData)

        if (['completed', 'failed', 'cancelled'].includes(statusData.status)) {
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
      const response = await fetch(API_ENDPOINTS.bulk.results(id), {
        headers: getDefaultHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }

      const data = await response.json()
      setResults(data.results)
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
      await fetch(API_ENDPOINTS.bulk.cancel(jobId), {
        method: 'POST',
        headers: getDefaultHeaders(),
      })
      stopPolling()
      setIsProcessing(false)
    } catch (err) {
      console.error('Error cancelling job:', err)
    }
  }

  // Download results as JSON
  const downloadResults = () => {
    const data = results.map((r) => ({
      topic: r.topic,
      success: r.success,
      content: r.content,
      error: r.error,
    }))

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bulk-generation-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
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
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>Back to Generator</span>
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <UsageIndicator compact />
              <div className="flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-indigo-600" />
                <span className="font-semibold text-gray-900">Blog AI</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">
              Bulk Content Generation
            </h1>
            <p className="text-indigo-100">
              Generate multiple blog posts at once. Upload a CSV or add topics manually.
            </p>
          </motion.div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Items */}
          <div className="lg:col-span-2 space-y-6">
            {/* CSV Upload */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Upload CSV
              </h2>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
                <ArrowUpTrayIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 mb-2">
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
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  Select CSV File
                </label>
                <button
                  onClick={downloadTemplate}
                  className="ml-2 text-sm text-indigo-600 hover:text-indigo-700"
                >
                  Download template
                </button>
              </div>
            </motion.div>

            {/* Items List */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Topics ({items.length})
                </h2>
                <button
                  onClick={addItem}
                  disabled={isProcessing}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
                >
                  <PlusIcon className="w-4 h-4" />
                  Add Topic
                </button>
              </div>

              {items.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No topics added yet.</p>
                  <p className="text-sm">Upload a CSV or add topics manually.</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  <AnimatePresence>
                    {items.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="border border-gray-200 rounded-lg p-4"
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
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                            />
                            <div className="flex gap-3">
                              <input
                                type="text"
                                value={item.keywords.join(', ')}
                                onChange={(e) => updateItem(index, 'keywords', e.target.value)}
                                placeholder="Keywords (comma separated)"
                                disabled={isProcessing}
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                              />
                              <select
                                value={item.tone}
                                onChange={(e) => updateItem(index, 'tone', e.target.value)}
                                disabled={isProcessing}
                                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
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
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          </div>

          {/* Right Column - Settings and Actions */}
          <div className="space-y-6">
            {/* Settings */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Settings
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Tone
                  </label>
                  <select
                    value={sharedTone}
                    onChange={(e) => setSharedTone(e.target.value)}
                    disabled={isProcessing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                  >
                    {TONE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Parallel Generations
                  </label>
                  <select
                    value={parallelLimit}
                    onChange={(e) => setParallelLimit(Number(e.target.value))}
                    disabled={isProcessing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
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
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Use web research</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={proofread}
                      onChange={(e) => setProofread(e.target.checked)}
                      disabled={isProcessing}
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Proofread content</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={humanize}
                      onChange={(e) => setHumanize(e.target.checked)}
                      disabled={isProcessing}
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Humanize content</span>
                  </label>
                </div>
              </div>
            </motion.div>

            {/* Progress */}
            {status && isProcessing && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-xl border border-gray-200 p-6"
              >
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Progress
                </h2>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Status</span>
                    <span className="font-medium capitalize text-gray-900">
                      {status.status}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${status.progress_percentage}%` }}
                      className="bg-indigo-500 h-3 rounded-full"
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>
                      {status.completed_items} / {status.total_items} completed
                    </span>
                    {status.failed_items > 0 && (
                      <span className="text-red-600">
                        {status.failed_items} failed
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <div className="space-y-3">
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
                    disabled={items.length === 0}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlayIcon className="w-5 h-5" />
                    Generate {items.length} Post{items.length !== 1 ? 's' : ''}
                  </button>
                )}

                {results.length > 0 && (
                  <button
                    onClick={downloadResults}
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <ArrowDownTrayIcon className="w-5 h-5" />
                    Download Results
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
            </motion.div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-red-50 border border-red-200 rounded-xl p-4"
              >
                <p className="text-sm text-red-700">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-xs text-red-600 hover:text-red-800"
                >
                  Dismiss
                </button>
              </motion.div>
            )}

            {/* Usage indicator */}
            <UsageIndicator />
          </div>
        </div>
      </div>
    </main>
  )
}
