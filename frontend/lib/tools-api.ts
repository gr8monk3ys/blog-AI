/**
 * Tools API client for Blog-AI
 *
 * Provides typed methods for interacting with the tools backend API.
 */

import { API_ENDPOINTS, apiFetch } from './api'
import type { Tool, ToolCategory } from '../types/tools'
import { TOOL_CATEGORIES } from '../types/tools'

/**
 * Valid tool categories from the frontend
 */
const VALID_CATEGORIES = Object.keys(TOOL_CATEGORIES) as ToolCategory[]

/**
 * Validate that a string is a valid ToolCategory
 */
function isValidCategory(category: string): category is ToolCategory {
  return VALID_CATEGORIES.includes(category as ToolCategory)
}

/**
 * Validate and sanitize tag values to prevent injection
 */
function validateTag(tag: string): boolean {
  return /^[a-zA-Z0-9_-]+$/.test(tag)
}

// Backend API response types
export interface ToolDefinition {
  id: string
  name: string
  description: string
  category: string
  icon?: string
  tags: string[]
  is_premium: boolean
  is_beta: boolean
  input_schema: {
    fields: InputField[]
  }
  output_schema: {
    format: string
    description?: string
  }
  prompt_template?: string
  examples?: ToolExample[]
}

export interface InputField {
  name: string
  type: 'text' | 'textarea' | 'select' | 'number' | 'boolean' | 'keywords'
  label: string
  placeholder?: string
  required: boolean
  default_value?: string | number | boolean
  options?: SelectOption[]
  min_length?: number
  max_length?: number
  min_value?: number
  max_value?: number
}

export interface SelectOption {
  value: string
  label: string
}

export interface ToolExample {
  inputs: Record<string, string | number | boolean>
  output: string
}

export interface ToolListResponse {
  tools: ToolDefinition[]
  total: number
  offset: number
  limit: number
}

export interface CategoryInfo {
  id: string
  name: string
  description: string
  icon?: string
  color: string
  tool_count: number
}

export interface ToolExecutionRequest {
  inputs: Record<string, string | number | boolean>
  provider_type?: 'openai' | 'anthropic' | 'gemini'
  options?: {
    temperature?: number
    max_tokens?: number
  }
}

export interface ToolExecutionResult {
  success: boolean
  output?: string
  execution_time_ms: number
  error?: string
  tool_id: string
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
}

/**
 * Tools API client
 */
export const toolsApi = {
  /**
   * List all available tools with optional filtering
   */
  async listTools(params?: {
    category?: string
    search?: string
    tags?: string[]
    include_premium?: boolean
    include_beta?: boolean
    limit?: number
    offset?: number
  }): Promise<ToolListResponse> {
    const searchParams = new URLSearchParams()

    if (params?.category) searchParams.set('category', params.category)
    if (params?.search) searchParams.set('search', params.search)
    // Validate tags to prevent injection
    if (params?.tags?.length) {
      const validTags = params.tags.filter(validateTag)
      if (validTags.length > 0) {
        searchParams.set('tags', validTags.join(','))
      }
    }
    if (params?.include_premium !== undefined)
      searchParams.set('include_premium', String(params.include_premium))
    if (params?.include_beta !== undefined)
      searchParams.set('include_beta', String(params.include_beta))
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.offset) searchParams.set('offset', String(params.offset))

    const url = searchParams.toString()
      ? `${API_ENDPOINTS.tools.list}?${searchParams}`
      : API_ENDPOINTS.tools.list

    return apiFetch<ToolListResponse>(url)
  },

  /**
   * Get all tool categories with counts
   */
  async listCategories(): Promise<CategoryInfo[]> {
    return apiFetch<CategoryInfo[]>(API_ENDPOINTS.tools.categories)
  },

  /**
   * Get tool registry statistics
   */
  async getStats(): Promise<{
    total_tools: number
    premium_tools: number
    beta_tools: number
    categories: Record<string, number>
  }> {
    return apiFetch(API_ENDPOINTS.tools.stats)
  },

  /**
   * Get a specific tool by ID
   */
  async getTool(toolId: string): Promise<ToolDefinition> {
    return apiFetch<ToolDefinition>(API_ENDPOINTS.tools.get(toolId))
  },

  /**
   * Execute a tool with the provided inputs
   */
  async executeTool(
    toolId: string,
    request: ToolExecutionRequest
  ): Promise<ToolExecutionResult> {
    return apiFetch<ToolExecutionResult>(API_ENDPOINTS.tools.execute(toolId), {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Validate inputs for a tool without executing
   */
  async validateInputs(
    toolId: string,
    inputs: Record<string, string | number | boolean>
  ): Promise<ValidationResult> {
    return apiFetch<ValidationResult>(API_ENDPOINTS.tools.validate(toolId), {
      method: 'POST',
      body: JSON.stringify(inputs),
    })
  },

  /**
   * Get all tools in a specific category
   */
  async getToolsByCategory(category: string): Promise<ToolDefinition[]> {
    return apiFetch<ToolDefinition[]>(API_ENDPOINTS.tools.byCategory(category))
  },
}

/**
 * Convert backend ToolDefinition to frontend Tool type with validation
 */
export function toFrontendTool(def: ToolDefinition): Tool {
  // Validate required fields
  if (!def.id || typeof def.id !== 'string') {
    throw new Error('Invalid tool definition: missing or invalid id')
  }
  if (!def.name || typeof def.name !== 'string') {
    throw new Error(`Invalid tool definition: missing or invalid name for tool ${def.id}`)
  }
  if (!def.description || typeof def.description !== 'string') {
    throw new Error(`Invalid tool definition: missing or invalid description for tool ${def.id}`)
  }

  // Validate and fallback category
  const category = isValidCategory(def.category) ? def.category : 'blog'

  return {
    id: def.id,
    slug: def.id,
    name: def.name,
    description: def.description,
    category,
    isFree: !def.is_premium,
    isNew: def.is_beta ?? false,
    isPopular: Array.isArray(def.tags) ? def.tags.includes('popular') : false,
  }
}

/**
 * Convert a list of backend tools to frontend format
 */
export function toFrontendTools(defs: ToolDefinition[]): Tool[] {
  return defs.map(toFrontendTool)
}

export default toolsApi
