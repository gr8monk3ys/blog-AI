'use client'

import { useState, useMemo, useEffect } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { TOOL_CATEGORIES, SAMPLE_TOOLS } from '../../../types/tools'
import type { TemplateCategory } from '../../../types/templates'
import type { ExportFormat } from '../../../components/ExportMenu'
import type { ContentVariation } from '../../../components/tools/VariationCompare'
import type { BrandProfile } from '../../../types/brand'
import { historyApi } from '../../../lib/history-api'
import { toolsApi } from '../../../lib/tools-api'
import { API_ENDPOINTS, apiFetch, getDefaultHeaders } from '../../../lib/api'
import SaveTemplateModal from '../../../components/templates/SaveTemplateModal'
import type { PlagiarismCheckResponse, PlagiarismCheckResult } from '../../../types/plagiarism'

// Import extracted components
import {
  ToastNotification,
  ToolNotFound,
  ToolPageHeader,
  ToolHeaderSection,
  ToolInputForm,
  ToolOutput,
  ToolSidebar,
  generateMockScore,
  generateMockOutput,
  parseKeywords,
  copyToClipboard,
} from '../../../components/tools/tool-page'

import type { ToastState } from '../../../components/tools/tool-page'

/**
 * Tool Page Component
 *
 * Displays individual tool interface for content generation.
 * Supports various content types (blog, email, social media, etc.)
 * with features like A/B testing, content scoring, and brand voice.
 */
export default function ToolPage() {
  const params = useParams()
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
  const [keywords, setKeywords] = useState('')
  const [generateVariations, setGenerateVariations] = useState(false)
  const [variationCount, setVariationCount] = useState(2)
  const [brandVoiceEnabled, setBrandVoiceEnabled] = useState(false)
  const [selectedBrandProfile, setSelectedBrandProfile] = useState<BrandProfile | null>(null)

  // Output state
  const [loading, setLoading] = useState(false)
  const [output, setOutput] = useState<string | null>(null)
  const [variations, setVariations] = useState<ContentVariation[]>([])
  const [selectedVariation, setSelectedVariation] = useState<ContentVariation | null>(null)
  const [contentScore, setContentScore] = useState<import('../../../components/tools/ContentScore').ContentScoreResult | null>(null)
  const [scoringLoading, setScoringLoading] = useState(false)
  const [plagiarismResult, setPlagiarismResult] = useState<PlagiarismCheckResult | null>(null)
  const [plagiarismLoading, setPlagiarismLoading] = useState(false)
  const [plagiarismError, setPlagiarismError] = useState<string | null>(null)

  // UI state
  const [copied, setCopied] = useState(false)
  const [savedContentId, setSavedContentId] = useState<string | null>(null)
  const [isFavorite, setIsFavorite] = useState(false)
  const [showSaveTemplateModal, setShowSaveTemplateModal] = useState(false)
  const [exportToast, setExportToast] = useState<ToastState>({
    show: false,
    message: '',
    type: 'success',
  })

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


  const buildExecutionInputs = (keywordList: string[]) => ({
    topic: inputText,
    input: inputText,
    tone,
    keywords: keywordList.join(', '),
    use_research: useResearch,
    brand_voice_enabled: brandVoiceEnabled,
  })

  const executeTool = async (keywordList: string[]) => {
    if (!tool) return null

    try {
      const result = await toolsApi.executeTool(tool.slug, {
        inputs: buildExecutionInputs(keywordList),
        brand_profile_id: brandVoiceEnabled ? (selectedBrandProfile?.id || undefined) : undefined,
      })

      if (result.success && result.output) {
        return result.output
      }

      // Treat structured "success: false" responses as real errors so we don't
      // silently fall back to mock output in production.
      throw new Error(result.error || 'Tool execution failed')
    } catch (err) {
      const status = (err as any)?.status
      // In production, don't silently fall back to mock output for auth/quota issues.
      if (process.env.NODE_ENV === 'production' || status === 401 || status === 403 || status === 429) {
        throw err
      }
      console.warn('Tool API execution failed, falling back to local preview.', err)
    }

    return null
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setOutput(null)
    setVariations([])
    setSelectedVariation(null)
    setContentScore(null)
    setPlagiarismResult(null)
    setPlagiarismError(null)
    setSavedContentId(null)
    setIsFavorite(false)

    const startTime = Date.now()
    const keywordList = parseKeywords(keywords)

    if (!inputText.trim()) {
      setLoading(false)
      setExportToast({
        show: true,
        message: 'Please enter a topic before generating content.',
        type: 'error',
      })
      return
    }

    if (brandVoiceEnabled && !selectedBrandProfile) {
      setLoading(false)
      setExportToast({
        show: true,
        message: 'Select a brand profile (or disable Brand Voice) to continue.',
        type: 'error',
      })
      return
    }

    try {
      if (generateVariations) {
        await handleVariationGeneration(keywordList)
      } else {
        await handleSingleGeneration(keywordList, startTime)
      }
    } catch (err: any) {
      const status = err?.status
      if (status === 401 || status === 403) {
        setExportToast({
          show: true,
          message: 'Sign in required to use the tool.',
          type: 'error',
        })
      } else if (status === 429) {
        setExportToast({
          show: true,
          message: 'Usage limit reached. Upgrade your plan to continue.',
          type: 'error',
        })
      } else {
        setExportToast({
          show: true,
          message: err instanceof Error ? err.message : 'Generation failed. Please try again.',
          type: 'error',
        })
      }
      setLoading(false)
    }
  }

  // Generate multiple variations
  const handleVariationGeneration = async (keywordList: string[]) => {
    if (!tool) return

    // Prefer backend variations endpoint (single call, scored on server).
    try {
      const response = await toolsApi.generateVariations(tool.slug, {
        inputs: buildExecutionInputs(keywordList),
        variation_count: variationCount,
        provider_type: 'openai',
        include_scores: true,
        keywords: keywordList,
        ...(brandVoiceEnabled && selectedBrandProfile?.id
          ? { brand_profile_id: selectedBrandProfile.id }
          : {}),
      })

      if (!response.success) {
        throw new Error(response.error || 'Failed to generate variations')
      }

      setVariations(response.variations || [])
      setLoading(false)
      return
    } catch (err) {
      // In production, surface the failure (no mock fallback).
      if (process.env.NODE_ENV === 'production') throw err
    }

    // Dev fallback: client-side loop with mock scoring/output.
    const generated: ContentVariation[] = []
    const labels = ['A', 'B', 'C']
    const styles = ['standard', 'creative', 'concise']
    const temps = [0.7, 0.9, 0.5]
    let usedFallback = false

    for (let i = 0; i < variationCount; i++) {
      let backendOutput: string | null = null
      try {
        backendOutput = await executeTool(keywordList)
      } catch {
        backendOutput = null
      }

      const content = backendOutput || generateMockOutput(tool, inputText, styles[i])
      if (!backendOutput) usedFallback = true
      const scores = generateMockScore(content, keywordList)

      generated.push({
        id: `var-${i}-${Date.now()}`,
        content,
        label: labels[i] || `V${i + 1}`,
        temperature: temps[i] || 0.7,
        prompt_style: styles[i] || 'standard',
        scores,
      })
    }

    if (usedFallback) {
      setExportToast({
        show: true,
        message: 'Backend unavailable. Showing local preview output for one or more variations.',
        type: 'error',
      })
    }

    setVariations(generated)
    setLoading(false)
  }

  // Generate single output
  const handleSingleGeneration = async (keywordList: string[], startTime: number) => {
    const backendOutput = await executeTool(keywordList)

    if (!backendOutput && process.env.NODE_ENV === 'production') {
      throw new Error('Backend unavailable. Please try again.')
    }

    const finalOutput = backendOutput || generateMockOutput(tool, inputText)

    if (!backendOutput) {
      setExportToast({
        show: true,
        message: 'Backend unavailable. Showing local preview output.',
        type: 'error',
      })
    }

    setOutput(finalOutput)
    setLoading(false)

    // Auto-score the content
    setScoringLoading(true)
    try {
      if (tool) {
        const scores = await toolsApi.scoreToolContent(tool.slug, {
          text: finalOutput,
          keywords: keywordList.length > 0 ? keywordList : undefined,
        })
        setContentScore(scores)
      }
    } catch {
      if (process.env.NODE_ENV !== 'production') {
        const scores = generateMockScore(finalOutput, keywordList)
        setContentScore(scores)
      } else {
        setContentScore(null)
      }
    }
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
            brand_profile_id: brandVoiceEnabled ? selectedBrandProfile?.id : null,
          },
          output: finalOutput,
          provider: backendOutput ? 'openai' : 'mock',
          execution_time_ms: executionTime,
        })
        setSavedContentId(saved.id)
        setIsFavorite(saved.is_favorite)
      } catch (err) {
        console.error('Failed to save to history:', err)
      }
    }
  }

  const runPlagiarismCheck = async (opts?: { skipCache?: boolean }) => {
    if (!output?.trim()) return
    if (output.trim().length < 50) {
      setPlagiarismError('Add more content before running a plagiarism check (min 50 characters).')
      return
    }

    setPlagiarismLoading(true)
    setPlagiarismError(null)

    try {
      const payload = await apiFetch<PlagiarismCheckResponse>(
        API_ENDPOINTS.content.checkPlagiarism,
        {
          method: 'POST',
          body: JSON.stringify({
            content: output,
            title: tool?.name,
            exclude_urls: [],
            skip_cache: opts?.skipCache === true,
          }),
        }
      )

      if (!payload.success) {
        throw new Error(payload.error || 'Plagiarism check failed')
      }

      setPlagiarismResult(payload.data || null)
    } catch (err: any) {
      const status = err?.status
      if (status === 401 || status === 403) {
        setPlagiarismError('Sign in required to run checks.')
      } else if (status === 429) {
        setPlagiarismError('Usage limit reached. Upgrade your plan to run checks.')
      } else {
        setPlagiarismError(err instanceof Error ? err.message : 'Plagiarism check failed')
      }
    } finally {
      setPlagiarismLoading(false)
    }
  }

  // Handle variation selection
  const handleVariationSelect = (variation: ContentVariation) => {
    setSelectedVariation(variation)
    setOutput(variation.content)
    setContentScore(variation.scores || null)
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
      keywords: parseKeywords(keywords),
    }

    const response = await fetch('/api/templates', {
      method: 'POST',
      headers: await getDefaultHeaders(),
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

  // Copy to clipboard handler
  const handleCopy = async () => {
    if (!output) return

    const success = await copyToClipboard(output)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  // Handle tool not found
  if (!tool) {
    return <ToolNotFound />
  }

  const categoryInfo = TOOL_CATEGORIES[tool.category]

  // Get related tools (same category, excluding current)
  const relatedTools = SAMPLE_TOOLS.filter(
    (t) => t.category === tool.category && t.id !== tool.id
  ).slice(0, 3)

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Toast notification for export */}
      <ToastNotification toast={exportToast} />

      {/* Header */}
      <ToolPageHeader />

      {/* Tool Header */}
      <ToolHeaderSection tool={tool} categoryInfo={categoryInfo} />

      {/* Main Content */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Form with Output */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="lg:col-span-2"
          >
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <ToolInputForm
                tool={tool}
                inputText={inputText}
                onInputTextChange={setInputText}
                tone={tone}
                onToneChange={setTone}
                useResearch={useResearch}
                onUseResearchChange={setUseResearch}
                generateVariations={generateVariations}
                onGenerateVariationsChange={setGenerateVariations}
                variationCount={variationCount}
                onVariationCountChange={setVariationCount}
                keywords={keywords}
                onKeywordsChange={setKeywords}
                brandVoiceEnabled={brandVoiceEnabled}
                onBrandVoiceEnabledChange={setBrandVoiceEnabled}
                selectedBrandProfile={selectedBrandProfile}
                onSelectedBrandProfileChange={setSelectedBrandProfile}
                loading={loading}
                onSubmit={handleSubmit}
              />

              {/* Output section */}
              <ToolOutput
                tool={tool}
                inputText={inputText}
                output={output}
                variations={variations}
                selectedVariation={selectedVariation}
                onVariationSelect={handleVariationSelect}
                contentScore={contentScore}
                scoringLoading={scoringLoading}
                plagiarismResult={plagiarismResult}
                plagiarismLoading={plagiarismLoading}
                plagiarismError={plagiarismError}
                onPlagiarismCheck={runPlagiarismCheck}
                savedContentId={savedContentId}
                isFavorite={isFavorite}
                onFavoriteToggle={setIsFavorite}
                copied={copied}
                onCopy={handleCopy}
                onExportComplete={handleExportComplete}
                onSaveTemplateClick={() => setShowSaveTemplateModal(true)}
                loading={loading}
              />
            </div>
          </motion.div>

          {/* Sidebar */}
          <ToolSidebar relatedTools={relatedTools} />
        </div>
      </section>

      {/* Save Template Modal */}
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
          keywords: parseKeywords(keywords),
        }}
      />
    </main>
  )
}
