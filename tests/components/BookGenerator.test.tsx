import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import BookGenerator from '../../components/BookGenerator'
import * as api from '../../lib/api'

// Mock the api module
vi.mock('../../lib/api', () => ({
  API_ENDPOINTS: {
    generateBook: 'http://localhost:8000/generate-book',
  },
  getDefaultHeaders: vi.fn(() => ({ 'Content-Type': 'application/json' })),
  checkServerConnection: vi.fn(),
}))

describe('BookGenerator', () => {
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
      render(<BookGenerator {...defaultProps} />)

      expect(screen.getByText('Book Generator')).toBeInTheDocument()
      expect(screen.getByLabelText(/book title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/number of chapters/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/topics per chapter/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/keywords/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/tone/i)).toBeInTheDocument()
    })

    it('should render advanced options switches', () => {
      render(<BookGenerator {...defaultProps} />)

      expect(screen.getByText('Use web research')).toBeInTheDocument()
      expect(screen.getByText('Proofread content')).toBeInTheDocument()
      expect(screen.getByText('Humanize content')).toBeInTheDocument()
    })

    it('should render submit button', () => {
      render(<BookGenerator {...defaultProps} />)

      expect(screen.getByRole('button', { name: /generate book/i })).toBeInTheDocument()
    })
  })

  describe('Form Inputs', () => {
    it('should update title when typed', async () => {
      const user = userEvent.setup()
      render(<BookGenerator {...defaultProps} />)

      const titleInput = screen.getByLabelText(/book title/i)
      await user.type(titleInput, 'My Test Book')

      expect(titleInput).toHaveValue('My Test Book')
    })

    it('should update chapters when changed', async () => {
      const user = userEvent.setup()
      render(<BookGenerator {...defaultProps} />)

      const chaptersInput = screen.getByLabelText(/number of chapters/i)
      await user.clear(chaptersInput)
      await user.type(chaptersInput, '10')

      expect(chaptersInput).toHaveValue(10)
    })

    it('should update keywords when typed', async () => {
      const user = userEvent.setup()
      render(<BookGenerator {...defaultProps} />)

      const keywordsInput = screen.getByLabelText(/keywords/i)
      await user.type(keywordsInput, 'AI, technology, future')

      expect(keywordsInput).toHaveValue('AI, technology, future')
    })

    it('should change tone selection', async () => {
      const user = userEvent.setup()
      render(<BookGenerator {...defaultProps} />)

      const toneSelect = screen.getByLabelText(/tone/i)
      await user.selectOptions(toneSelect, 'professional')

      expect(toneSelect).toHaveValue('professional')
    })
  })

  describe('Form Submission', () => {
    it('should require title field', async () => {
      render(<BookGenerator {...defaultProps} />)

      const form = screen.getByRole('button', { name: /generate book/i }).closest('form')
      expect(form).toBeInTheDocument()

      const titleInput = screen.getByLabelText(/book title/i)
      expect(titleInput).toBeRequired()
    })

    it('should call setLoading(true) on submit', async () => {
      const user = userEvent.setup()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<BookGenerator {...defaultProps} />)

      await user.type(screen.getByLabelText(/book title/i), 'Test Book')
      await user.click(screen.getByRole('button', { name: /generate book/i }))

      expect(mockSetLoading).toHaveBeenCalledWith(true)
    })

    it('should use mock data when server is not connected', async () => {
      vi.useFakeTimers()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<BookGenerator {...defaultProps} />)

      // Use fireEvent for simpler async handling
      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      // Advance timers to trigger mock data
      await vi.advanceTimersByTimeAsync(5500)

      expect(mockSetContent).toHaveBeenCalled()
      const contentArg = mockSetContent.mock.calls[0]?.[0]
      expect(contentArg).toBeDefined()
      expect(contentArg!.success).toBe(true)
      expect(contentArg!.type).toBe('book')

      vi.useRealTimers()
    })

    it('should make API call when server is connected', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: true,
          type: 'book',
          content: { title: 'Generated Book', chapters: [] },
        }),
      } as unknown as Response)

      render(<BookGenerator {...defaultProps} />)

      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/generate-book',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test Book'),
          })
        )
      })
    })

    it('should display error message on API failure', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValueOnce({ detail: 'Generation failed' }),
      } as unknown as Response)

      render(<BookGenerator {...defaultProps} />)

      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Generation failed')).toBeInTheDocument()
      })
    })

    it('should call setLoading(false) after completion', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: true,
          type: 'book',
          content: { title: 'Test', chapters: [] },
        }),
      } as unknown as Response)

      render(<BookGenerator {...defaultProps} />)

      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(mockSetLoading).toHaveBeenLastCalledWith(false)
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error and allow dismissal', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

      render(<BookGenerator {...defaultProps} />)

      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })

      // Dismiss error
      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }))

      expect(screen.queryByText('Network error')).not.toBeInTheDocument()
    })

    it('should clear error on new submission', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)

      // First call fails
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('First error'))

      render(<BookGenerator {...defaultProps} />)

      fireEvent.change(screen.getByLabelText(/book title/i), {
        target: { value: 'Test Book' },
      })
      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument()
      })

      // Second call succeeds
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          success: true,
          type: 'book',
          content: { title: 'Test', chapters: [] },
        }),
      } as unknown as Response)

      fireEvent.submit(screen.getByRole('button', { name: /generate book/i }))

      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument()
      })
    })
  })
})
