import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConversationHistory from '../../components/ConversationHistory'
import * as api from '../../lib/api'

// Mock the api module
vi.mock('../../lib/api', () => ({
  API_ENDPOINTS: {
    conversation: (id: string) => `http://localhost:8000/conversations/${id}`,
    websocket: (id: string) => `ws://localhost:8000/ws/conversation/${id}`,
  },
  getDefaultHeaders: vi.fn(() => ({ 'Content-Type': 'application/json' })),
  checkServerConnection: vi.fn(),
}))

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('ConversationHistory', () => {
  const defaultProps = {
    conversationId: 'test-conversation-123',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(global.fetch).mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('should render the component title', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ConversationHistory {...defaultProps} />)

      expect(screen.getByText('Conversation')).toBeInTheDocument()
    })

    it('should show loading state initially', () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ConversationHistory {...defaultProps} />)

      // The loading dots should be present
      const loadingContainer = screen.getByText('Conversation').parentElement?.parentElement
      expect(loadingContainer).toBeInTheDocument()
    })
  })

  describe('Mock Data (Server Disconnected)', () => {
    it('should display mock messages when server is not connected', async () => {
      vi.useFakeTimers()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ConversationHistory {...defaultProps} />)

      // Advance timer to trigger mock data loading
      await vi.advanceTimersByTimeAsync(1500)

      expect(
        screen.getByText(/Can you write a blog post about artificial intelligence/i)
      ).toBeInTheDocument()

      vi.useRealTimers()
    })

    it('should show message count badge with mock messages', async () => {
      vi.useFakeTimers()
      vi.mocked(api.checkServerConnection).mockResolvedValue(false)

      render(<ConversationHistory {...defaultProps} />)

      await vi.advanceTimersByTimeAsync(1500)

      expect(screen.getByText('4 messages')).toBeInTheDocument()

      vi.useRealTimers()
    })
  })

  describe('Server Connection', () => {
    it('should fetch conversation history when server is connected', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          conversation: [
            {
              role: 'user',
              content: 'Hello',
              timestamp: new Date().toISOString(),
            },
            {
              role: 'assistant',
              content: 'Hi there!',
              timestamp: new Date().toISOString(),
            },
          ],
        }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/conversations/test-conversation-123',
          expect.objectContaining({
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
            }),
          })
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Hello')).toBeInTheDocument()
        expect(screen.getByText('Hi there!')).toBeInTheDocument()
      })
    })

    it('should display error when fetch fails', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(
          screen.getByText('Failed to load conversation history. Please try again.')
        ).toBeInTheDocument()
      })
    })

    it('should show retry button on error', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should display empty state when no messages', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({ conversation: [] }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('No messages yet')).toBeInTheDocument()
        expect(
          screen.getByText('Start a conversation by generating content')
        ).toBeInTheDocument()
      })
    })
  })

  describe('Message Display', () => {
    it('should display user messages with correct styling', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          conversation: [
            {
              role: 'user',
              content: 'User message',
              timestamp: new Date().toISOString(),
            },
          ],
        }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('You')).toBeInTheDocument()
        expect(screen.getByText('User message')).toBeInTheDocument()
      })
    })

    it('should display assistant messages with correct label', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          conversation: [
            {
              role: 'assistant',
              content: 'Assistant response',
              timestamp: new Date().toISOString(),
            },
          ],
        }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('AI Assistant')).toBeInTheDocument()
        expect(screen.getByText('Assistant response')).toBeInTheDocument()
      })
    })

    it('should display relative timestamps', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          conversation: [
            {
              role: 'user',
              content: 'Recent message',
              timestamp: new Date().toISOString(),
            },
          ],
        }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('just now')).toBeInTheDocument()
      })
    })
  })

  describe('Message Grouping', () => {
    it('should group consecutive messages from same sender', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({
          conversation: [
            {
              role: 'user',
              content: 'First message',
              timestamp: new Date().toISOString(),
            },
            {
              role: 'user',
              content: 'Second message',
              timestamp: new Date().toISOString(),
            },
          ],
        }),
      } as unknown as Response)

      render(<ConversationHistory {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('First message')).toBeInTheDocument()
        expect(screen.getByText('Second message')).toBeInTheDocument()
        // Only one "You" label should be present for grouped messages
        expect(screen.getAllByText('You')).toHaveLength(1)
      })
    })
  })

  describe('Conversation ID Changes', () => {
    it('should refetch when conversationId changes', async () => {
      vi.mocked(api.checkServerConnection).mockResolvedValue(true)
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({ conversation: [] }),
      } as unknown as Response)

      const { rerender } = render(<ConversationHistory conversationId="conv-1" />)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/conversations/conv-1',
          expect.any(Object)
        )
      })

      rerender(<ConversationHistory conversationId="conv-2" />)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/conversations/conv-2',
          expect.any(Object)
        )
      })
    })
  })
})
