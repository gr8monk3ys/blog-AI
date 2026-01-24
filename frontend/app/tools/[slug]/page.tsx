'use client'

import { useState, useMemo, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Switch } from '@headlessui/react'
import {
  ArrowLeftIcon,
  SparklesIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  BriefcaseIcon,
  VideoCameraIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  LightBulbIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  ClockIcon,
  BeakerIcon,
  ChartBarIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline'
import { StarIcon, SparklesIcon as SparklesSolid } from '@heroicons/react/24/solid'
import ExportMenu, { ExportContent, ExportFormat } from '../../../components/ExportMenu'
import FavoriteButton from '../../../components/history/FavoriteButton'
import ContentScore from '../../../components/tools/ContentScore'
import VariationCompare from '../../../components/tools/VariationCompare'
import SaveTemplateModal from '../../../components/templates/SaveTemplateModal'
import BrandVoiceSelector from '../../../components/brand/BrandVoiceSelector'
import type { ContentScoreResult } from '../../../components/tools/ContentScore'
import type { ContentVariation } from '../../../components/tools/VariationCompare'
import type { BrandProfile } from '../../../types/brand'
import type { TemplateCategory } from '../../../types/templates'
import { Tool, TOOL_CATEGORIES, SAMPLE_TOOLS } from '../../../types/tools'
import { historyApi } from '../../../lib/history-api'

const categoryIcons: Record<string, React.ElementType> = {
  blog: DocumentTextIcon,
  email: EnvelopeIcon,
  'social-media': ChatBubbleLeftRightIcon,
  business: BriefcaseIcon,
  naming: SparklesIcon,
  video: VideoCameraIcon,
  seo: MagnifyingGlassIcon,
  rewriting: ArrowPathIcon,
}

export default function ToolPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const slug = params.slug as string
  const fromHistoryId = searchParams.get('from')

  // Find the tool by slug
  const tool = useMemo(() => {
    return SAMPLE_TOOLS.find((t) => t.slug === slug)
  }, [slug])

  // Form state
  const [inputText, setInputText] = useState('')
  const [tone, setTone] = useState<string>('professional')
  const [useResearch, setUseResearch] = useState(false)
  const [loading, setLoading] = useState(false)
  const [output, setOutput] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [savedContentId, setSavedContentId] = useState<string | null>(null)
  const [isFavorite, setIsFavorite] = useState(false)
  const [exportToast, setExportToast] = useState<{
    show: boolean
    message: string
    type: 'success' | 'error'
  }>({ show: false, message: '', type: 'success' })

  // A/B Testing and Scoring state
  const [generateVariations, setGenerateVariations] = useState(false)
  const [variationCount, setVariationCount] = useState(2)
  const [variations, setVariations] = useState<ContentVariation[]>([])
  const [selectedVariation, setSelectedVariation] = useState<ContentVariation | null>(null)
  const [contentScore, setContentScore] = useState<ContentScoreResult | null>(null)
  const [scoringLoading, setScoringLoading] = useState(false)
  const [keywords, setKeywords] = useState('')

  // Template and Brand Voice state
  const [showSaveTemplateModal, setShowSaveTemplateModal] = useState(false)
  const [brandVoiceEnabled, setBrandVoiceEnabled] = useState(false)
  const [selectedBrandProfile, setSelectedBrandProfile] = useState<BrandProfile | null>(null)

  // Load previous content if coming from history
  useEffect(() => {
    const loadFromHistory = async () => {
      if (!fromHistoryId) return

      try {
        const item = await historyApi.getById(fromHistoryId)
        if (item) {
          const inputs = item.inputs as Record<string, unknown>
          if (inputs.topic) setInputText(String(inputs.topic))
          else if (inputs.input) setInputText(String(inputs.input))
          if (inputs.tone) setTone(String(inputs.tone))
          setOutput(item.output)
          setSavedContentId(item.id)
          setIsFavorite(item.is_favorite)
        }
      } catch (err) {
        console.error('Failed to load from history:', err)
      }
    }

    loadFromHistory()
  }, [fromHistoryId])

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setOutput(null)
    setVariations([])
    setSelectedVariation(null)
    setContentScore(null)
    setSavedContentId(null)
    setIsFavorite(false)

    const startTime = Date.now()

    // Parse keywords for scoring
    const keywordList = keywords
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0)

    if (generateVariations) {
      // Generate multiple variations (mock for now)
      await new Promise((resolve) => setTimeout(resolve, 3000))

      const mockVariations: ContentVariation[] = []
      const labels = ['A', 'B', 'C']
      const styles = ['standard', 'creative', 'concise']
      const temps = [0.7, 0.9, 0.5]

      for (let i = 0; i < variationCount; i++) {
        const content = generateMockOutput(tool, inputText, styles[i])
        const scores = generateMockScore(content, keywordList)

        mockVariations.push({
          id: `var-${i}-${Date.now()}`,
          content,
          label: labels[i] || `V${i + 1}`,
          temperature: temps[i] || 0.7,
          prompt_style: styles[i] || 'standard',
          scores,
        })
      }

      setVariations(mockVariations)
      setLoading(false)
    } else {
      // Single generation
      await new Promise((resolve) => setTimeout(resolve, 2000))

      const mockOutput = generateMockOutput(tool, inputText)
      setOutput(mockOutput)
      setLoading(false)

      // Auto-score the content
      setScoringLoading(true)
      await new Promise((resolve) => setTimeout(resolve, 500))
      const scores = generateMockScore(mockOutput, keywordList)
      setContentScore(scores)
      setScoringLoading(false)

      const executionTime = Date.now() - startTime

      // Save to history if available
      if (historyApi.isAvailable() && tool) {
        try {
          const saved = await historyApi.saveGeneration({
            tool_id: tool.slug,
            tool_name: tool.name,
            title: inputText.substring(0, 100),
            inputs: {
              topic: inputText,
              tone,
              useResearch,
              keywords: keywordList,
            },
            output: mockOutput,
            provider: 'openai',
            execution_time_ms: executionTime,
          })
          setSavedContentId(saved.id)
          setIsFavorite(saved.is_favorite)
        } catch (err) {
          console.error('Failed to save to history:', err)
        }
      }
    }
  }

  // Handle variation selection
  const handleVariationSelect = (variation: ContentVariation) => {
    setSelectedVariation(variation)
    setOutput(variation.content)
    setContentScore(variation.scores || null)
  }

  // Build export content from tool output
  const getExportContent = (): ExportContent | null => {
    if (!output || !tool) return null
    return {
      title: `${tool.name} - ${inputText.substring(0, 50)}${inputText.length > 50 ? '...' : ''}`,
      content: output,
      type: 'tool',
      metadata: {
        date: new Date().toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        }),
        toolName: tool.name,
        description: tool.description,
      },
    }
  }

  // Handle export completion with toast notification
  const handleExportComplete = (format: ExportFormat, success: boolean) => {
    const formatNames: Record<ExportFormat, string> = {
      markdown: 'Markdown',
      html: 'HTML',
      text: 'Plain Text',
      pdf: 'PDF',
      clipboard: 'Clipboard',
      wordpress: 'WordPress',
      medium: 'Medium',
    }

    if (success) {
      const action = ['clipboard', 'wordpress', 'medium'].includes(format)
        ? 'copied'
        : 'downloaded'
      setExportToast({
        show: true,
        message: `${formatNames[format]} ${action} successfully`,
        type: 'success',
      })
    } else {
      setExportToast({
        show: true,
        message: `Failed to export as ${formatNames[format]}`,
        type: 'error',
      })
    }

    setTimeout(() => setExportToast({ show: false, message: '', type: 'success' }), 3000)
  }

  // Handle saving as template
  const handleSaveTemplate = async (data: {
    name: string
    description: string
    category: TemplateCategory
    tags: string[]
    isPublic: boolean
  }) => {
    if (!tool) return

    const presetInputs = {
      topic: inputText,
      tone,
      useResearch,
      keywords: keywords.split(',').map((k) => k.trim()).filter((k) => k.length > 0),
    }

    const response = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...data,
        toolId: tool.slug,
        presetInputs,
      }),
    })

    const result = await response.json()

    if (!result.success) {
      throw new Error(result.error || 'Failed to save template')
    }

    setExportToast({
      show: true,
      message: 'Template saved successfully',
      type: 'success',
    })
    setTimeout(() => setExportToast({ show: false, message: '', type: 'success' }), 3000)
  }

  // Copy to clipboard with fallback for older browsers
  const handleCopy = async () => {
    if (!output) return

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(output)
      } else {
        // Fallback for older browsers or non-HTTPS contexts
        const textArea = document.createElement('textarea')
        textArea.value = output
        textArea.style.position = 'fixed'
        textArea.style.left = '-9999px'
        textArea.style.top = '-9999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
      // Could add a toast notification here for user feedback
    }
  }

  // Handle tool not found
  if (!tool) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Tool Not Found</h1>
          <p className="text-gray-600 mb-6">
            The tool you&apos;re looking for doesn&apos;t exist or has been removed.
          </p>
          <Link
            href="/tools"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Tools
          </Link>
        </div>
      </main>
    )
  }

  const categoryInfo = TOOL_CATEGORIES[tool.category]
  const Icon = categoryIcons[tool.category] || DocumentTextIcon

  // Get related tools (same category, excluding current)
  const relatedTools = SAMPLE_TOOLS.filter(
    (t) => t.category === tool.category && t.id !== tool.id
  ).slice(0, 3)

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Toast notification for export */}
      {exportToast.show && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-4 right-4 z-50"
        >
          <div
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
              exportToast.type === 'success'
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            {exportToast.type === 'success' ? (
              <CheckIcon className="w-5 h-5 text-emerald-500" />
            ) : (
              <svg
                className="w-5 h-5 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            )}
            <span className="text-sm font-medium">{exportToast.message}</span>
          </div>
        </motion.div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/tools"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" aria-hidden="true" />
                <span>All Tools</span>
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-indigo-600" aria-hidden="true" />
              <span className="font-semibold text-gray-900">Blog AI</span>
            </div>
          </div>
        </div>
      </header>

      {/* Tool Header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="flex items-start gap-4">
              <div
                className={`flex-shrink-0 w-14 h-14 rounded-xl ${categoryInfo.bgColor} flex items-center justify-center`}
              >
                <Icon className={`w-7 h-7 ${categoryInfo.color}`} aria-hidden="true" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {tool.name}
                  </h1>
                  {tool.isFree && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 border border-emerald-200">
                      Free
                    </span>
                  )}
                  {tool.isNew && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                      New
                    </span>
                  )}
                </div>
                <p className="mt-2 text-gray-600">{tool.description}</p>
                <div className="mt-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${categoryInfo.bgColor} ${categoryInfo.color} border ${categoryInfo.borderColor}`}
                  >
                    {categoryInfo.name}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="lg:col-span-2"
          >
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Create Content
                </h2>

                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* Main input */}
                  <div>
                    <label
                      htmlFor="input"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      {getInputLabel(tool)}
                    </label>
                    <textarea
                      id="input"
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      rows={4}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                      placeholder={getInputPlaceholder(tool)}
                      required
                    />
                  </div>

                  {/* Tone selector */}
                  <div>
                    <label
                      htmlFor="tone"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Tone
                    </label>
                    <select
                      id="tone"
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                    >
                      <option value="professional">Professional</option>
                      <option value="conversational">Conversational</option>
                      <option value="friendly">Friendly</option>
                      <option value="persuasive">Persuasive</option>
                      <option value="informative">Informative</option>
                    </select>
                  </div>

                  {/* Advanced options */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center mb-3">
                      <LightBulbIcon
                        className="h-4 w-4 text-indigo-600 mr-2"
                        aria-hidden="true"
                      />
                      <h3 className="text-sm font-medium text-gray-700">
                        Advanced Options
                      </h3>
                    </div>

                    <div className="space-y-4">
                      {/* Web research toggle */}
                      <div className="flex items-center space-x-3">
                        <Switch
                          checked={useResearch}
                          onChange={setUseResearch}
                          aria-label="Use web research"
                          className={`${
                            useResearch ? 'bg-indigo-600' : 'bg-gray-200'
                          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
                        >
                          <span
                            aria-hidden="true"
                            className={`${
                              useResearch ? 'translate-x-6' : 'translate-x-1'
                            } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                          />
                        </Switch>
                        <span className="text-sm text-gray-700">
                          Use web research for better results
                        </span>
                      </div>

                      {/* A/B Testing toggle */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Switch
                            checked={generateVariations}
                            onChange={setGenerateVariations}
                            aria-label="Generate variations"
                            className={`${
                              generateVariations ? 'bg-indigo-600' : 'bg-gray-200'
                            } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
                          >
                            <span
                              aria-hidden="true"
                              className={`${
                                generateVariations ? 'translate-x-6' : 'translate-x-1'
                              } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
                            />
                          </Switch>
                          <div className="flex items-center gap-2">
                            <BeakerIcon className="w-4 h-4 text-indigo-600" />
                            <span className="text-sm text-gray-700">
                              Generate variations for A/B testing
                            </span>
                          </div>
                        </div>
                        {generateVariations && (
                          <select
                            value={variationCount}
                            onChange={(e) => setVariationCount(Number(e.target.value))}
                            className="text-sm rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                          >
                            <option value={2}>2 versions</option>
                            <option value={3}>3 versions</option>
                          </select>
                        )}
                      </div>

                      {/* Keywords input for SEO scoring */}
                      <div>
                        <label
                          htmlFor="keywords"
                          className="flex items-center gap-2 text-sm text-gray-700 mb-1"
                        >
                          <ChartBarIcon className="w-4 h-4 text-indigo-600" />
                          Keywords for SEO scoring (comma-separated)
                        </label>
                        <input
                          type="text"
                          id="keywords"
                          value={keywords}
                          onChange={(e) => setKeywords(e.target.value)}
                          placeholder="e.g., AI, machine learning, technology"
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Brand Voice Selector */}
                  <BrandVoiceSelector
                    enabled={brandVoiceEnabled}
                    onEnabledChange={setBrandVoiceEnabled}
                    selectedProfile={selectedBrandProfile}
                    onProfileChange={setSelectedBrandProfile}
                  />

                  {/* Submit button */}
                  <button
                    type="submit"
                    disabled={loading || !inputText.trim()}
                    className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <svg
                          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-4 h-4 mr-2" aria-hidden="true" />
                        Generate Content
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Variations comparison section */}
              {variations.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border-t border-gray-200 bg-gray-50"
                >
                  <div className="p-6">
                    <VariationCompare
                      variations={variations}
                      isLoading={loading}
                      onSelect={handleVariationSelect}
                      selectedId={selectedVariation?.id}
                    />
                  </div>
                </motion.div>
              )}

              {/* Output section */}
              {output && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="border-t border-gray-200 bg-gray-50"
                >
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          {selectedVariation ? `Selected Content (Version ${selectedVariation.label})` : 'Generated Content'}
                        </h3>
                        {savedContentId && (
                          <FavoriteButton
                            contentId={savedContentId}
                            isFavorite={isFavorite}
                            onToggle={(newStatus) => setIsFavorite(newStatus)}
                            size="sm"
                          />
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={handleCopy}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                        >
                          {copied ? (
                            <>
                              <CheckIcon className="w-3.5 h-3.5 text-emerald-500" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <ClipboardDocumentIcon className="w-3.5 h-3.5" />
                              Copy
                            </>
                          )}
                        </button>
                        {getExportContent() && (
                          <ExportMenu
                            content={getExportContent()!}
                            onExportComplete={handleExportComplete}
                          />
                        )}
                      </div>
                    </div>
                    <div className="bg-white rounded-lg border border-gray-200 p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {output}
                      </p>
                    </div>

                    {/* Content Score display */}
                    {(contentScore || scoringLoading) && (
                      <div className="mt-4">
                        <ContentScore
                          scores={contentScore!}
                          isLoading={scoringLoading}
                          showDetails={true}
                        />
                      </div>
                    )}

                    {/* Save as Template and History indicator */}
                    <div className="mt-4 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => setShowSaveTemplateModal(true)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 transition-colors"
                      >
                        <BookmarkIcon className="w-3.5 h-3.5" />
                        Save as Template
                      </button>

                      {savedContentId && (
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="inline-flex items-center gap-1">
                            <ClockIcon className="w-3.5 h-3.5" aria-hidden="true" />
                            Saved to history
                          </span>
                          <Link
                            href="/history"
                            className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-700 transition-colors"
                          >
                            View history
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </Link>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Sidebar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="space-y-6"
          >
            {/* Tips card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Tips for best results
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-indigo-600 mt-0.5">*</span>
                  Be specific about your topic or goal
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-indigo-600 mt-0.5">*</span>
                  Include relevant keywords for SEO
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-indigo-600 mt-0.5">*</span>
                  Choose a tone that matches your brand
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-indigo-600 mt-0.5">*</span>
                  Enable research for factual content
                </li>
              </ul>
            </div>

            {/* Related tools */}
            {relatedTools.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  Related Tools
                </h3>
                <ul className="space-y-3">
                  {relatedTools.map((relatedTool) => (
                    <li key={relatedTool.id}>
                      <Link
                        href={`/tools/${relatedTool.slug}`}
                        className="block group"
                      >
                        <div className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors">
                          {relatedTool.name}
                        </div>
                        <div className="text-xs text-gray-500 line-clamp-1">
                          {relatedTool.description}
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        </div>
      </section>

      {/* Save Template Modal */}
      {tool && (
        <SaveTemplateModal
          isOpen={showSaveTemplateModal}
          onClose={() => setShowSaveTemplateModal(false)}
          onSave={handleSaveTemplate}
          toolId={tool.slug}
          toolName={tool.name}
          presetInputs={{
            topic: inputText,
            tone,
            useResearch,
            keywords: keywords.split(',').map((k) => k.trim()).filter((k) => k.length > 0),
          }}
        />
      )}
    </main>
  )
}

// Helper functions
function getInputLabel(tool: Tool): string {
  const labels: Record<string, string> = {
    blog: 'What topic would you like to write about?',
    email: 'What is this email about?',
    'social-media': 'What would you like to post about?',
    business: 'Describe your business or product',
    naming: 'Describe what you need a name for',
    video: 'What is your video about?',
    seo: 'Enter your content or topic',
    rewriting: 'Enter the content to rewrite',
  }
  return labels[tool.category] || 'Enter your input'
}

function getInputPlaceholder(tool: Tool): string {
  const placeholders: Record<string, string> = {
    blog: 'e.g., The future of artificial intelligence in healthcare...',
    email: 'e.g., Following up on our meeting about the Q4 project...',
    'social-media': 'e.g., Launching our new product line for summer...',
    business: 'e.g., A SaaS platform that helps small businesses manage...',
    naming: 'e.g., A tech startup focused on sustainable energy solutions...',
    video: 'e.g., Tutorial on how to build a React application...',
    seo: 'e.g., Best practices for remote work in 2024...',
    rewriting: 'Paste the content you want to improve here...',
  }
  return placeholders[tool.category] || 'Enter your input here...'
}

// Generate mock content scores
function generateMockScore(content: string, keywords: string[]): ContentScoreResult {
  const wordCount = content.split(/\s+/).length
  const sentenceCount = content.split(/[.!?]+/).filter(s => s.trim()).length
  const headingCount = (content.match(/^#{1,6}\s/gm) || []).length
  const questionCount = (content.match(/\?/g) || []).length
  const listCount = (content.match(/^[\s]*[-*+]|\d+[.)]/gm) || []).length

  // Calculate keyword density
  const contentLower = content.toLowerCase()
  const primaryKeyword = keywords[0]?.toLowerCase() || ''
  const keywordOccurrences = primaryKeyword
    ? (contentLower.match(new RegExp(primaryKeyword, 'g')) || []).length
    : 0
  const keywordDensity = wordCount > 0 ? (keywordOccurrences / wordCount) * 100 : 0

  // Random variation for mock data
  const randomOffset = () => Math.floor(Math.random() * 15) - 7

  const readabilityScore = Math.min(100, Math.max(40, 70 + randomOffset()))
  const seoScore = Math.min(100, Math.max(40, wordCount > 300 ? 75 + randomOffset() : 50 + randomOffset()))
  const engagementScore = Math.min(100, Math.max(40, 65 + randomOffset()))

  const getLevel = (score: number): 'excellent' | 'good' | 'fair' | 'poor' => {
    if (score >= 80) return 'excellent'
    if (score >= 60) return 'good'
    if (score >= 40) return 'fair'
    return 'poor'
  }

  return {
    overall_score: Math.round((readabilityScore * 0.3 + seoScore * 0.4 + engagementScore * 0.3)),
    overall_level: getLevel(Math.round((readabilityScore * 0.3 + seoScore * 0.4 + engagementScore * 0.3))),
    readability: {
      score: readabilityScore,
      level: getLevel(readabilityScore),
      flesch_kincaid_grade: 8 + Math.random() * 4,
      flesch_reading_ease: readabilityScore,
      average_sentence_length: wordCount / Math.max(1, sentenceCount),
      average_word_length: 4.5 + Math.random(),
      complex_word_percentage: 10 + Math.random() * 10,
      suggestions: readabilityScore < 70
        ? ['Consider using shorter sentences', 'Use simpler vocabulary for broader audience']
        : ['Readability is good. Content is accessible to most readers.'],
    },
    seo: {
      score: seoScore,
      level: getLevel(seoScore),
      keyword_density: keywordDensity,
      keyword_placement: {
        in_title: headingCount > 0 && primaryKeyword ? contentLower.includes(primaryKeyword) : false,
        in_first_paragraph: primaryKeyword ? contentLower.substring(0, 500).includes(primaryKeyword) : false,
        in_headings: headingCount > 0,
      },
      word_count: wordCount,
      heading_count: headingCount,
      has_meta_elements: false,
      internal_link_potential: 2,
      suggestions: seoScore < 70
        ? ['Add more headings to improve structure', 'Consider expanding content length']
        : ['SEO structure looks good. Content is well-optimized.'],
    },
    engagement: {
      score: engagementScore,
      level: getLevel(engagementScore),
      hook_strength: 60 + Math.random() * 30,
      cta_count: listCount > 0 ? 1 : 0,
      emotional_word_count: Math.floor(wordCount * 0.02),
      question_count: questionCount,
      list_count: listCount,
      storytelling_elements: 1,
      suggestions: engagementScore < 70
        ? ['Add a stronger opening hook', 'Include a call-to-action']
        : ['Engagement is strong. Content has good hooks and CTAs.'],
    },
    summary: readabilityScore >= 70 && seoScore >= 70 && engagementScore >= 70
      ? 'Good content with solid fundamentals across all dimensions.'
      : 'Content has room for improvement. Focus on the suggestions below.',
    top_improvements: [
      '[SEO] Consider adding more relevant keywords naturally',
      '[Engagement] Add questions to engage readers',
      '[Readability] Break up long paragraphs for better scanning',
    ].slice(0, 3),
  }
}

function generateMockOutput(tool: Tool | undefined, input: string, style: string = 'standard'): string {
  if (!tool) return ''

  // Style modifiers for variation
  const stylePrefix: Record<string, string> = {
    standard: '',
    creative: 'Imagine a world where ',
    concise: '',
  }

  const styleSuffix: Record<string, string> = {
    standard: '',
    creative: '\n\nWhat possibilities does this open up for you?',
    concise: '',
  }

  const templates: Record<string, string> = {
    blog: `# ${input}

## Introduction
In today's rapidly evolving landscape, understanding ${input.toLowerCase()} has become more crucial than ever. This comprehensive guide will explore the key aspects and provide actionable insights for your journey.

## Key Points

### 1. Understanding the Fundamentals
The foundation of ${input.toLowerCase()} lies in grasping its core principles. When we examine this topic closely, we find several interconnected elements that work together to create meaningful outcomes.

### 2. Best Practices
To excel in this area, consider implementing these proven strategies:
- Focus on continuous learning and adaptation
- Embrace innovative approaches while respecting established methods
- Build strong networks and collaborative relationships

### 3. Future Outlook
As we look ahead, ${input.toLowerCase()} will continue to evolve. Staying informed and adaptable will be key to success in this dynamic field.

## Conclusion
By understanding and applying these principles, you'll be well-positioned to navigate the complexities of ${input.toLowerCase()} and achieve your goals.`,

    email: `Subject: ${input}

Hi [Name],

I hope this email finds you well. I wanted to reach out regarding ${input.toLowerCase()}.

After careful consideration, I believe we have an excellent opportunity to move forward with this initiative. Here are the key points I'd like to discuss:

1. The current situation and its implications
2. Our proposed approach and timeline
3. Expected outcomes and success metrics

Would you be available for a brief call this week to discuss these points in more detail? I'm confident that together we can achieve great results.

Looking forward to your response.

Best regards,
[Your Name]`,

    'social-media': `${input}

Here's what you need to know:

1/ First key insight that grabs attention
2/ Supporting evidence and examples
3/ Actionable takeaway for your audience

The future is bright for those who embrace change.

What are your thoughts on this? Drop a comment below and let's discuss.

#${input.split(' ')[0]} #Innovation #Growth`,

    business: `Product/Service Description:

${input}

Our solution addresses the critical challenges facing modern businesses by providing:

* Streamlined operations and improved efficiency
* Cost-effective implementation with measurable ROI
* Scalable architecture that grows with your needs

Key Benefits:
- Reduce operational costs by up to 40%
- Increase team productivity and collaboration
- Access real-time insights for informed decision-making

Ready to transform your business? Contact us today for a personalized demo.`,

    naming: `Based on your description of "${input}", here are some creative name suggestions:

1. **Nexacore** - Combining "next" and "core" for innovative foundations
2. **Vantiq** - A blend of "vantage" and "technique" suggesting expertise
3. **Luminary Labs** - Evoking leadership and innovation
4. **Elevate Pro** - Simple, memorable, and aspirational
5. **Zenith Solutions** - Representing peak performance

Each name is designed to be:
* Easy to pronounce and remember
* Available as a domain (recommended to verify)
* Scalable for future growth`,

    video: `VIDEO SCRIPT: ${input}

[INTRO - 0:00-0:30]
Hook: Open with a compelling question or statement that grabs attention immediately.

"Have you ever wondered about ${input.toLowerCase()}? Today, we're diving deep into this fascinating topic."

[MAIN CONTENT - 0:30-4:00]
Section 1: The Basics
- Explain foundational concepts
- Use visual examples

Section 2: Key Insights
- Share surprising facts
- Include expert perspectives

Section 3: Practical Application
- Step-by-step demonstration
- Real-world examples

[OUTRO - 4:00-4:30]
Summary and call-to-action:
"If you found this valuable, don't forget to like and subscribe for more content like this!"`,

    seo: `META DESCRIPTION:
Discover everything you need to know about ${input.toLowerCase()}. Our comprehensive guide covers key strategies, best practices, and expert tips for success. Read now!

---

OPTIMIZED TITLE OPTIONS:
1. "${input}: The Ultimate Guide for 2024"
2. "How to Master ${input} - Complete Strategy Guide"
3. "${input} Explained: Tips, Tricks & Best Practices"

---

KEYWORD SUGGESTIONS:
Primary: ${input.toLowerCase()}
Secondary: ${input.toLowerCase()} guide, ${input.toLowerCase()} tips, how to ${input.toLowerCase()}
Long-tail: best practices for ${input.toLowerCase()}, ${input.toLowerCase()} for beginners`,

    rewriting: `IMPROVED VERSION:

${input
  .split('. ')
  .map((sentence) => {
    // Simple transformation for demo
    return sentence.charAt(0).toUpperCase() + sentence.slice(1)
  })
  .join('. ')}

---

CHANGES MADE:
* Improved sentence structure and flow
* Enhanced clarity and readability
* Strengthened word choices
* Maintained original meaning and intent

The revised content is now more engaging and professional while preserving your original message.`,
  }

  const baseContent = templates[tool.category] || `Generated content for: ${input}`

  // Apply style modifications
  if (style === 'creative') {
    return stylePrefix.creative + baseContent + styleSuffix.creative
  } else if (style === 'concise') {
    // Return a shorter version
    const lines = baseContent.split('\n').filter(line => line.trim())
    return lines.slice(0, Math.ceil(lines.length * 0.7)).join('\n')
  }

  return baseContent
}
