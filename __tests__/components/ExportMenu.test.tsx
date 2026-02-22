import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ExportMenu from '../../components/ExportMenu'
import type { ExportContent } from '../../components/ExportMenu'

// Mock the api module to control getDefaultHeaders
vi.mock('../../lib/api', () => ({
  getDefaultHeaders: vi.fn().mockResolvedValue({
    'Content-Type': 'application/json',
    Authorization: 'Bearer mock-token',
  }),
}))

const sampleContent: ExportContent = {
  title: 'Test Blog Post',
  content: '# Test\n\nThis is test content.',
  type: 'blog',
  metadata: {
    date: '2026-02-16',
    description: 'A test blog post',
    tags: ['test', 'blog'],
  },
}

describe('ExportMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(global.fetch).mockReset()
  })

  describe('Rendering', () => {
    it('should render the Export button', () => {
      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      expect(exportButton).toBeInTheDocument()
    })

    it('should render the button with a down arrow icon', () => {
      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      // The button should contain aria-hidden icons
      const icons = exportButton.querySelectorAll('svg[aria-hidden="true"]')
      expect(icons.length).toBeGreaterThanOrEqual(1)
    })

    it('should disable the button when the disabled prop is true', () => {
      render(<ExportMenu content={sampleContent} disabled />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      expect(exportButton).toBeDisabled()
    })
  })

  describe('Export format options', () => {
    it('should show download options when the menu is opened', async () => {
      const user = userEvent.setup()
      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      expect(screen.getByText('Download')).toBeInTheDocument()
      expect(screen.getByText('Copy to Clipboard')).toBeInTheDocument()
      expect(screen.getByText('Markdown')).toBeInTheDocument()
      expect(screen.getByText('HTML')).toBeInTheDocument()
      expect(screen.getByText('Plain Text')).toBeInTheDocument()
      expect(screen.getByText('PDF')).toBeInTheDocument()
    })

    it('should show publishing options when the menu is opened', async () => {
      const user = userEvent.setup()
      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      expect(screen.getByText('Copy for Publishing')).toBeInTheDocument()
      expect(screen.getByText('WordPress')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
    })

    it('should display descriptions for each option', async () => {
      const user = userEvent.setup()
      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      expect(screen.getByText('Copy content as plain text')).toBeInTheDocument()
      expect(screen.getByText('Download as .md file')).toBeInTheDocument()
      expect(screen.getByText('Download styled HTML')).toBeInTheDocument()
      expect(screen.getByText('Download as .txt file')).toBeInTheDocument()
      expect(screen.getByText('Download as PDF document')).toBeInTheDocument()
    })
  })

  describe('Auth headers in fetch calls', () => {
    it('should include auth headers when exporting markdown', async () => {
      const user = userEvent.setup()

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(['# test'], { type: 'text/markdown' })),
      } as Response)

      // Mock URL.createObjectURL and URL.revokeObjectURL for file download
      const createObjectURLSpy = vi.fn().mockReturnValue('blob:test-url')
      const revokeObjectURLSpy = vi.fn()
      global.URL.createObjectURL = createObjectURLSpy
      global.URL.revokeObjectURL = revokeObjectURLSpy

      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      const markdownOption = screen.getByText('Markdown')
      await user.click(markdownOption)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1)
      })

      const [fetchUrl, fetchOptions] = vi.mocked(global.fetch).mock.calls[0]!
      expect(fetchUrl).toContain('/export/markdown')
      expect(fetchOptions?.method).toBe('POST')

      // Verify auth headers were awaited and included
      const headers = fetchOptions?.headers as Record<string, string>
      expect(headers['Content-Type']).toBe('application/json')
      expect(headers['Authorization']).toBe('Bearer mock-token')
    })

    it('should include auth headers when exporting PDF', async () => {
      const user = userEvent.setup()

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(['pdf-data'], { type: 'application/pdf' })),
      } as Response)

      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:test-url')
      global.URL.revokeObjectURL = vi.fn()

      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      const pdfOption = screen.getByText('PDF')
      await user.click(pdfOption)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1)
      })

      const [fetchUrl, fetchOptions] = vi.mocked(global.fetch).mock.calls[0]!
      expect(fetchUrl).toContain('/export/pdf')

      const headers = fetchOptions?.headers as Record<string, string>
      expect(headers['Authorization']).toBe('Bearer mock-token')
    })

    it('should send the correct request body for export', async () => {
      const user = userEvent.setup()

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(['<html>test</html>'])),
      } as Response)

      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:test-url')
      global.URL.revokeObjectURL = vi.fn()

      render(<ExportMenu content={sampleContent} />)

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      const htmlOption = screen.getByText('HTML')
      await user.click(htmlOption)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1)
      })

      const [, fetchOptions] = vi.mocked(global.fetch).mock.calls[0]!
      const body = JSON.parse(fetchOptions?.body as string)

      expect(body.title).toBe('Test Blog Post')
      expect(body.content).toBe('# Test\n\nThis is test content.')
      expect(body.content_type).toBe('blog')
      expect(body.metadata).toEqual(sampleContent.metadata)
    })
  })

  describe('Callbacks', () => {
    it('should call onExportStart when an export begins', async () => {
      const user = userEvent.setup()
      const onExportStart = vi.fn()

      // Mock clipboard for the clipboard export path
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: vi.fn().mockResolvedValue(undefined) },
      })

      render(
        <ExportMenu content={sampleContent} onExportStart={onExportStart} />
      )

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      const clipboardOption = screen.getByText('Copy to Clipboard')
      await user.click(clipboardOption)

      await waitFor(() => {
        expect(onExportStart).toHaveBeenCalledTimes(1)
      })
    })

    it('should call onExportComplete after a successful export', async () => {
      const user = userEvent.setup()
      const onExportComplete = vi.fn()

      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: vi.fn().mockResolvedValue(undefined) },
      })

      render(
        <ExportMenu
          content={sampleContent}
          onExportComplete={onExportComplete}
        />
      )

      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      const clipboardOption = screen.getByText('Copy to Clipboard')
      await user.click(clipboardOption)

      await waitFor(() => {
        expect(onExportComplete).toHaveBeenCalledWith('clipboard', true)
      })
    })
  })
})
