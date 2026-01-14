import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ContentGenerator from '../../components/ContentGenerator'
import * as api from '../../lib/api'

// Mock the api module
vi.mock('../../lib/api', () => ({
  API_ENDPOINTS: {
    generateBlog: 'http://localhost:8000/generate-blog',
  },
  getDefaultHeaders: vi.fn(() => ({ 'Content-Type': 'application/json' })),
  checkServerConnection: vi.fn(),
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
      const contentArg = mockSetContent.mock.calls[0][0]
      expect(contentArg.success).toBe(true)
      expect(contentArg.type).toBe('blog')

      vi.useRealTimers()
    })

    it('should make API call when server is connected', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
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
        }),
      } as unknown as Response)

      render(<ContentGenerator {...defaultProps} />)

      fireEvent.change(
        screen.getByLabelText(/what would you like to write about/i),
        { target: { value: 'Test Topic' } }
      )
      fireEvent.submit(screen.getByRole('button', { name: /generate blog post/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/generate-blog',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test Topic'),
          })
        )
      })
    })

    it('should send correct request body', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: true,
          type: 'blog',
          content: { title: 'Test', sections: [], description: '', date: '', image: '', tags: [] },
        }),
      } as unknown as Response)

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
        const fetchCall = vi.mocked(global.fetch).mock.calls[0]
        const body = JSON.parse(fetchCall[1]?.body as string)

        expect(body.topic).toBe('My Topic')
        expect(body.keywords).toEqual(['key1', 'key2'])
        expect(body.tone).toBe('professional')
        expect(body.conversation_id).toBe('test-conversation-123')
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error on API failure', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValueOnce({ detail: 'Content generation failed' }),
      } as unknown as Response)

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
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

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
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Test error'))

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
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: false,
          detail: 'Validation failed',
        }),
      } as unknown as Response)

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
  })

  describe('Loading State', () => {
    it('should call setLoading(false) after successful response', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: true,
          type: 'blog',
          content: { title: 'Test', sections: [], description: '', date: '', image: '', tags: [] },
        }),
      } as unknown as Response)

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
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Failed'))

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
})
