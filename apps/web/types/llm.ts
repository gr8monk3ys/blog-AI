/**
 * Types for LLM provider selection in the UI.
 */

export type LlmProviderType = 'openai' | 'anthropic' | 'gemini'

export interface LlmConfig {
  default_provider: LlmProviderType | null
  available_providers: LlmProviderType[]
  models?: Partial<Record<LlmProviderType, string>>
}

