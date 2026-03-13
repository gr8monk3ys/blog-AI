/**
 * Shared types for Tool Page components
 */

import type { BrandProfile } from '../../../types/brand'
import type { ContentScoreResult } from '../ContentScore'
import type { ContentVariation } from '../VariationCompare'
import type { Tool, ToolCategoryInfo } from '../../../types/tools'

export type { Tool, ToolCategoryInfo }
export type { ContentScoreResult, ContentVariation }
export type { BrandProfile }

export interface ToastState {
  show: boolean
  message: string
  type: 'success' | 'error'
}

export interface FormState {
  inputText: string
  tone: string
  useResearch: boolean
  keywords: string
  generateVariations: boolean
  variationCount: number
  brandVoiceEnabled: boolean
  selectedBrandProfile: BrandProfile | null
}

export interface OutputState {
  output: string | null
  variations: ContentVariation[]
  selectedVariation: ContentVariation | null
  contentScore: ContentScoreResult | null
  scoringLoading: boolean
  savedContentId: string | null
  isFavorite: boolean
  copied: boolean
}

export interface ToolPageState extends FormState, OutputState {
  loading: boolean
}

export type ToneOption = 'professional' | 'conversational' | 'friendly' | 'persuasive' | 'informative'

export const TONE_OPTIONS: { value: ToneOption; label: string }[] = [
  { value: 'professional', label: 'Professional' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'persuasive', label: 'Persuasive' },
  { value: 'informative', label: 'Informative' },
]
