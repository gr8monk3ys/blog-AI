import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import BulkGenerationPageClient from '@/app/bulk/BulkGenerationPageClient'

/**
 * Characterization net for the bulk generation page ahead of the planned
 * hook/JSX split (docs/REMEDIATION_PLAN.md Phase 3.1): pins the interactive
 * shell — empty state, adding/removing topic rows, and the provider/strategy
 * controls — so extractions can be verified against unchanged behavior.
 */

vi.mock('framer-motion', () => {
  const passthrough = (tag: string) =>
    function MockMotion({ children, ...props }: Record<string, unknown>) {
      const Tag = tag as keyof JSX.IntrinsicElements
      void props
      return <Tag>{children as React.ReactNode}</Tag>
    }
  return {
    m: new Proxy({}, { get: (_t, prop: string) => passthrough(prop) }),
    motion: new Proxy({}, { get: (_t, prop: string) => passthrough(prop) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }
})

vi.mock('../../../components/SiteHeader', () => ({
  default: () => <header data-testid="site-header" />,
}))
vi.mock('../../../components/SiteFooter', () => ({
  default: () => <footer data-testid="site-footer" />,
}))

vi.mock('../../../components/UsageIndicator', () => ({
  default: () => <div data-testid="usage-indicator" />,
  useUsageCheck: () => ({
    canGenerate: true,
    remaining: null,
    loading: false,
    checkUsage: vi.fn().mockResolvedValue(true),
  }),
}))

vi.mock('../../../hooks/useLlmConfig', () => ({
  useLlmConfig: () => ({
    config: null,
    availableProviders: ['openai', 'anthropic', 'gemini'],
    defaultProvider: 'openai',
  }),
}))

describe('BulkGenerationPageClient', () => {
  beforeEach(() => {
    vi.mocked(global.fetch).mockReset()
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response)
  })

  it('renders the empty state with CSV/manual guidance', () => {
    render(<BulkGenerationPageClient />)
    expect(
      screen.getByText(/upload a csv or add topics manually/i)
    ).toBeInTheDocument()
  })

  it('adds a topic row when Add Topic is clicked', () => {
    render(<BulkGenerationPageClient />)
    expect(screen.queryAllByPlaceholderText(/enter topic/i)).toHaveLength(0)

    fireEvent.click(screen.getByRole('button', { name: /add topic/i }))
    expect(screen.getAllByPlaceholderText(/enter topic/i)).toHaveLength(1)

    fireEvent.click(screen.getByRole('button', { name: /add topic/i }))
    expect(screen.getAllByPlaceholderText(/enter topic/i)).toHaveLength(2)
  })

  it('edits a topic value through the input', () => {
    render(<BulkGenerationPageClient />)
    fireEvent.click(screen.getByRole('button', { name: /add topic/i }))
    const input = screen.getByPlaceholderText(/enter topic/i)
    fireEvent.change(input, { target: { value: 'AI in Healthcare' } })
    expect(input).toHaveValue('AI in Healthcare')
  })

  it('shows the provider strategy options', () => {
    render(<BulkGenerationPageClient />)
    expect(screen.getByText(/single provider/i)).toBeInTheDocument()
    expect(screen.getByText(/round robin/i)).toBeInTheDocument()
  })

  it('renders header and footer stubs (page shell intact)', () => {
    render(<BulkGenerationPageClient />)
    expect(screen.getByTestId('site-header')).toBeInTheDocument()
    expect(screen.getByTestId('site-footer')).toBeInTheDocument()
  })
})
