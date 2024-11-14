// Static option lists for the bulk generation page.
// Extracted from BulkGenerationPageClient.tsx to keep that component focused.

import type { ProviderStrategy, ExportFormat } from '../../types/bulk'
import type { LlmProviderType } from '../../types/llm'

export const TONE_OPTIONS = [
  { value: 'informative', label: 'Informative' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'technical', label: 'Technical' },
]

export const PROVIDER_META: Record<LlmProviderType, { label: string; cost: string }> = {
  openai: { label: 'OpenAI', cost: '$$$' },
  anthropic: { label: 'Anthropic', cost: '$$' },
  gemini: { label: 'Gemini', cost: '$' },
}

export const STRATEGY_OPTIONS: { value: ProviderStrategy; label: string; description: string }[] = [
  { value: 'single', label: 'Single Provider', description: 'Use one provider for all items' },
  { value: 'round_robin', label: 'Round Robin', description: 'Rotate through all providers' },
  { value: 'cost_optimized', label: 'Cost Optimized', description: 'Use cheapest provider available' },
  { value: 'quality_optimized', label: 'Quality Optimized', description: 'Use highest quality provider' },
]

export const EXPORT_OPTIONS: { value: ExportFormat; label: string; icon: string }[] = [
  { value: 'json', label: 'JSON', icon: '{ }' },
  { value: 'csv', label: 'CSV', icon: '📊' },
  { value: 'markdown', label: 'Markdown', icon: '📝' },
  { value: 'zip', label: 'ZIP (all files)', icon: '📦' },
]
