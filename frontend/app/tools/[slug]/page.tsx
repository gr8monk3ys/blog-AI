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
import SaveTemplateModal from '../../../components/templates/SaveTemplateModal'

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
    const keywordList = parseKeywords(keywords)

    if (generateVariations) {
      await handleVariationGeneration(keywordList)
    } else {
      await handleSingleGeneration(keywordList, startTime)
    }
  }

  // Generate multiple variations
  const handleVariationGeneration = async (keywordList: string[]) => {
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
  }

  // Generate single output
  const handleSingleGeneration = async (keywordList: string[], startTime: number) => {
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
