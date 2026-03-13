import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ContentGenerator from '../../components/ContentGenerator'
import * as api from '../../lib/api'

const { mockCheckServerConnection, mockApiFetchWithRetry, mockCheckUsage } = vi.hoisted(() => ({
  mockCheckServerConnection: vi.fn(),
  mockApiFetchWithRetry: vi.fn(),
  mockCheckUsage: vi.fn(),
}))

const { mockUseLlmConfig } = vi.hoisted(() => ({
  mockUseLlmConfig: vi.fn(() => ({
    availableProviders: ['openai', 'anthropic', 'gemini'],
    defaultProvider: 'openai',
  })),
}))

// Mock the api module
vi.mock('../../lib/api', () => {
  class ApiError extends Error {
    status: number
    data: unknown

    constructor(message: string, status: number, data: unknown) {
      super(message)
      this.name = 'ApiError'
      this.status = status
      this.data = data
    }
  }

  return {
    API_ENDPOINTS: {
      generateBlog: 'http://localhost:8000/generate-blog',
    },
    ApiError,
    getDefaultHeaders: vi.fn(() => ({ 'Content-Type': 'application/json' })),
    checkServerConnection: mockCheckServerConnection,
    apiFetchWithRetry: mockApiFetchWithRetry,
  }
})

vi.mock('../../components/UsageIndicator', () => ({
  useUsageCheck: () => ({
    canGenerate: true,
    remaining: null,
    loading: false,
    checkUsage: mockCheckUsage,
  }),
}))

vi.mock('../../hooks/useLlmConfig', () => ({
  useLlmConfig: () => mockUseLlmConfig(),
}))

vi.mock('../../components/brand/BrandVoiceSelector', () => ({
  default: ({
    onEnabledChange,
    onProfileChange,
  }: {
    onEnabledChange: (enabled: boolean) => void
    onProfileChange: (profile: { id: string } | null) => void
  }) => (
    <div data-testid="brand-voice-selector">
      <button type="button" onClick={() => onEnabledChange(true)}>
        Enable Brand Voice
      </button>
      <button type="button" onClick={() => onEnabledChange(false)}>
        Disable Brand Voice
      </button>
      <button type="button" onClick={() => onProfileChange({ id: 'brand-1' })}>
        Pick Brand Profile
      </button>
      <button type="button" onClick={() => onProfileChange(null)}>
        Clear Brand Profile
      </button>
    </div>
  ),
}))

describe('ContentGenerator', () => {
  const mockSetContent = vi.fn()
  const mockSetLoading = vi.fn()
  const defaultProps = {
    conversationId: 'test-conversation-123',
    setContent: mockSetContent,
    setLoading: mockSetLoading,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseLlmConfig.mockReturnValue({
      availableProviders: ['openai', 'anthropic', 'gemini'],
      defaultProvider: 'openai',
    })
    mockCheckUsage.mockResolvedValue(true)
    mockCheckServerConnection.mockResolvedValue(true)
    mockApiFetchWithRetry.mockResolvedValue({
      success: true,
      type: 'blog',
      content: {
        title: 'Generated Blog',
        sections: [],
        description: '',
        date: '',
        image: '',
        tags: [],
      },
    })
    vi.mocked(global.fetch).mockReset()
  })

  describe('Rendering', () => {
    it('should render the form with all fields', () => {
      render(<ContentGenerator {...defaultProps} />)

      expect(screen.getByText('Blog Post Generator')).toBeInTheDocument()
      expect(screen.getByLabelText(/what would you like to write about/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/keywords/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/tone/i)).toBeInTheDocument()
    })

    it('should render advanced options switches', () => {
      render(<ContentGenerator {...defaultProps} />)

      expect(screen.getByText('Use web research')).toBeInTheDocument()
      expect(screen.getByText('Proofread content')).toBeInTheDocument()
      expect(screen.getByText('Humanize content')).toBeInTheDocument()
    })

    it('should render submit button', () => {
      render(<ContentGenerator {...defaultProps} />)

      expect(screen.getByRole('button', { name: /generate blog post/i })).toBeInTheDocument()
    })
  })

  describe('Form Inputs', () => {
    it('should update topic when typed', async () => {
      const user = userEvent.setup()
      render(<ContentGenerator {...defaultProps} />)

      const topicInput = screen.getByLabelText(/what would you like to write about/i)
      await user.type(topicInput, 'AI in Healthcare')

      expect(topicInput).toHaveValue('AI in Healthcare')
    })

    it('should update keywords when typed', async () => {
      const user = userEvent.setup()
      render(<ContentGenerator {...defaultProps} />)

      const keywordsInput = screen.getByLabelText(/keywords/i)
      await user.type(keywordsInput, 'AI, healthcare, technology')

      expect(keywordsInput).toHaveValue('AI, healthcare, technology')
    })

    it('should change tone selection', async () => {
      const user = userEvent.setup()
      render(<ContentGenerator {...defaultProps} />)

      const toneSelect = screen.getByLabelText(/tone/i)
      await user.selectOptions(toneSelect, 'conversational')

      expect(toneSelect).toHaveValue('conversational')
    })

    it('should have all tone options', () => {
      render(<ContentGenerator {...defaultProps} />)

      const toneSelect = screen.getByLabelText(/tone/i)
      const options = Array.from(toneSelect.querySelectorAll('option'))

      expect(options.map((o) => o.value)).toEqual([
        'informative',
        'conversational',
        'professional',
        'friendly',
        'authoritative',
        'technical',
      ])
    })

    it('should disable provider selector when only one provider is available', () => {
      mockUseLlmConfig.mockReturnValue({
        availableProviders: ['openai'],
        defaultProvider: 'openai',
      })

      render(<ContentGenerator {...defaultProps} />)

      expect(screen.getByLabelText(/model provider/i)).toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    it('should require topic field', () => {
      render(<ContentGenerator {...defaultProps} />)

      const topicInput = screen.getByLabelText(/what would you like to write about/i)
      expect(topicInput).toBeRequired()
    })

    it('should call setLoading(true) on submit', async () => {
      const user = userEvent.setup()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ContentGenerator {...defaultProps} />)

      await user.type(
        screen.getByLabelText(/what would you like to write about/i),
        'Test Topic'
      )
      await user.click(screen.getByRole('button', { name: /generate blog post/i }))

      expect(mockSetLoading).toHaveBeenCalledWith(true)
    })

    it('should use mock data when server is not connected', async () => {
      vi.useFakeTimers()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      // Advance timers to trigger mock data
      await vi.advanceTimersByTimeAsync(3500)

      expect(mockSetContent).toHaveBeenCalled()
      const contentArg = mockSetContent.mock.calls[0]?.[0]
      expect(contentArg).toBeDefined()
      expect(contentArg!.success).toBe(true)
      expect(contentArg!.type).toBe('blog')

      vi.useRealTimers()
    })

    it('should make API call when server is connected', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockResolvedValueOnce({
        success: true,
        type: 'blog',
        content: {
          title: 'Generated Blog',
          sections: [],
          description: '',
          date: '',
          image: '',
          tags: [],
        },
      })

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(api.apiFetchWithRetry).toHaveBeenCalledWith(
          'http://localhost:8000/generate-blog',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test Topic'),
          }),
        )
      })
    })

    it('should send correct request body', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockResolvedValueOnce({
        success: true,
        type: 'blog',
        content: {
          title: 'Test',
          sections: [],
          description: '',
          date: '',
          image: '',
          tags: [],
        },
      })

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'My Topic' } }
      )
      fireEvent.change(screen.getByLabelText(/keywords/i), {
        target: { value: 'key1, key2' },
      })
      fireEvent.change(screen.getByLabelText(/tone/i), {
        target: { value: 'professional' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        const apiCall = vi.mocked(api.apiFetchWithRetry).mock.calls[0]
        expect(apiCall).toBeDefined()
        const body = JSON.parse(apiCall![1]?.body as string)

        expect(body.topic).toBe('My Topic')
        expect(body.keywords).toEqual(['key1', 'key2'])
        expect(body.tone).toBe('professional')
        expect(body.conversation_id).toBe('test-conversation-123')
      })
    })

    it('should prevent submission when usage limit is reached', async () => {
      mockCheckUsage.mockResolvedValue(false)

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Limited Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Usage Limit Reached')).toBeInTheDocument()
      })
      expect(mockApiFetchWithRetry).not.toHaveBeenCalled()
    })

    it('should require a brand profile when brand voice is enabled', async () => {
      render(<ContentGenerator {...defaultProps} />)

      fireEvent.click(screen.getByRole('button', { name: /enable brand voice/i }))
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Brand Voice Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(
          screen.getByText(/select a brand profile/i)
        ).toBeInTheDocument()
      })
      expect(mockApiFetchWithRetry).not.toHaveBeenCalled()
    })

    it('should include brand_profile_id in request body when profile is selected', async () => {
      render(<ContentGenerator {...defaultProps} />)

      fireEvent.click(screen.getByRole('button', { name: /enable brand voice/i }))
      fireEvent.click(screen.getByRole('button', { name: /pick brand profile/i }))
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Branded Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        const apiCall = vi.mocked(api.apiFetchWithRetry).mock.calls[0]
        expect(apiCall).toBeDefined()
        const body = JSON.parse(apiCall![1]?.body as string)
        expect(body.brand_profile_id).toBe('brand-1')
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error on API failure', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new Error('Content generation failed')
      )

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Content generation failed')).toBeInTheDocument()
      })
    })

    it('should display error on network failure', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(new Error('Network error'))

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('should allow dismissing error', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(new Error('Test error'))

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Test error')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }))

      expect(screen.queryByText('Test error')).not.toBeInTheDocument()
    })

    it('should handle non-success response', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockResolvedValueOnce({
        success: false,
        detail: 'Validation failed',
      })

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Validation failed')).toBeInTheDocument()
      })
    })

    it('should show auth message for 401 errors', async () => {
      const ApiErrorClass = (api as unknown as { ApiError: typeof Error }).ApiError
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new (ApiErrorClass as unknown as new (
          message: string,
          status: number,
          data: unknown
        ) => Error)('Unauthorized', 401, {})
      )

      render(<ContentGenerator {...defaultProps} />)
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Auth Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Authentication Required')).toBeInTheDocument()
      })
      expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute(
        'href',
        '/sign-in'
      )
    })

    it('should show upgrade message for 403 errors', async () => {
      const ApiErrorClass = (api as unknown as { ApiError: typeof Error }).ApiError
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new (ApiErrorClass as unknown as new (
          message: string,
          status: number,
          data: unknown
        ) => Error)('Forbidden', 403, {})
      )

      render(<ContentGenerator {...defaultProps} />)
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Forbidden Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
      })
      expect(
        screen.getByRole('link', { name: /upgrade your plan/i })
      ).toHaveAttribute('href', '/pricing')
    })

    it('should show retry-after messaging for 429 errors', async () => {
      const ApiErrorClass = (api as unknown as { ApiError: typeof Error }).ApiError
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new (ApiErrorClass as unknown as new (
          message: string,
          status: number,
          data: unknown
        ) => Error)('Rate limited', 429, { retry_after: 7 })
      )

      render(<ContentGenerator {...defaultProps} />)
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Rate Limited Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Rate Limit')).toBeInTheDocument()
        expect(screen.getByText(/try again in 7s/i)).toBeInTheDocument()
      })
    })

    it('should show unavailable message for 503 errors', async () => {
      const ApiErrorClass = (api as unknown as { ApiError: typeof Error }).ApiError
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new (ApiErrorClass as unknown as new (
          message: string,
          status: number,
          data: unknown
        ) => Error)('Unavailable', 503, {})
      )

      render(<ContentGenerator {...defaultProps} />)
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Unavailable Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Service Unavailable')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('should show offline message for fetch TypeError', async () => {
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(
        new TypeError('fetch failed')
      )

      render(<ContentGenerator {...defaultProps} />)
      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Offline Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(screen.getByText('Connection Error')).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('should call setLoading(false) after successful response', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockResolvedValueOnce({
        success: true,
        type: 'blog',
        content: {
          title: 'Test',
          sections: [],
          description: '',
          date: '',
          image: '',
          tags: [],
        },
      })

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(mockSetLoading).toHaveBeenLastCalledWith(false)
      })
    })

    it('should call setLoading(false) after error', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(api.apiFetchWithRetry).mockRejectedValueOnce(new Error('Failed'))

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(mockSetLoading).toHaveBeenLastCalledWith(false)
      })
    })
  })

  describe('Option Toggles', () => {
    it('should toggle advanced option switches', async () => {
      const user = userEvent.setup()
      render(<ContentGenerator {...defaultProps} />)

      const researchToggle = screen.getByLabelText(/enable web research/i)
      const proofreadToggle = screen.getByLabelText(/enable proofreading/i)
      const humanizeToggle = screen.getByLabelText(/enable content humanization/i)

      expect(researchToggle).toHaveAttribute('aria-checked', 'false')
      expect(proofreadToggle).toHaveAttribute('aria-checked', 'true')
      expect(humanizeToggle).toHaveAttribute('aria-checked', 'true')

      await user.click(researchToggle)
      await user.click(proofreadToggle)
      await user.click(humanizeToggle)

      expect(researchToggle).toHaveAttribute('aria-checked', 'true')
      expect(proofreadToggle).toHaveAttribute('aria-checked', 'false')
      expect(humanizeToggle).toHaveAttribute('aria-checked', 'false')
    })
  })
})
