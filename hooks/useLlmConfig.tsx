'use client'

import { useEffect, useMemo, useState } from 'react'

import { API_ENDPOINTS, apiFetch } from '../lib/api'
import type { LlmConfig, LlmProviderType } from '../types/llm'

const FALLBACK_PROVIDERS: LlmProviderType[] = ['openai', 'anthropic', 'gemini']

export function useLlmConfig(): {
  loading: boolean
  error: string | null
  config: LlmConfig | null
  availableProviders: LlmProviderType[]
  defaultProvider: LlmProviderType
} {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<LlmConfig | null>(null)

  useEffect(() => {
    let mounted = true

    ;(async () => {
      try {
        const cfg = await apiFetch<LlmConfig>(API_ENDPOINTS.config.llm)
        if (!mounted) return
        setConfig(cfg)
        setError(null)
      } catch (err) {
        if (!mounted) return
        setError(err instanceof Error ? err.message : 'Failed to load model providers')
      } finally {
        if (mounted) setLoading(false)
      }
    })()

    return () => {
      mounted = false
    }
  }, [])

  const availableProviders = useMemo(() => {
    const list = config?.available_providers
    return list && Array.isArray(list) && list.length > 0 ? list : FALLBACK_PROVIDERS
  }, [config])

  const defaultProvider = useMemo(() => {
    const v = config?.default_provider
    if (v && availableProviders.includes(v)) return v
    return availableProviders[0] || 'openai'
  }, [availableProviders, config])

  return { loading, error, config, availableProviders, defaultProvider }
}

