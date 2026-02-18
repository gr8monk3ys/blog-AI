import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRouter } from 'next/navigation'
import NotFound from '../../app/not-found'

describe('NotFound', () => {
  const mockRouter = {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Override useRouter for this test file to control the mock directly
    vi.mocked(useRouter).mockReturnValue(mockRouter as any)
  })

  describe('Rendering', () => {
    it('should render the 404 status code', () => {
      render(<NotFound />)

      expect(screen.getByText('404')).toBeInTheDocument()
    })

    it('should render the "Page not found" heading', () => {
      render(<NotFound />)

      const heading = screen.getByRole('heading', {
        name: /page not found/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('should render a descriptive error message', () => {
      render(<NotFound />)

      expect(
        screen.getByText(/sorry, we could not find the page/i)
      ).toBeInTheDocument()
    })

    it('should render a "Go back home" link pointing to /', () => {
      render(<NotFound />)

      const homeLink = screen.getByRole('link', { name: /go back home/i })
      expect(homeLink).toBeInTheDocument()
      expect(homeLink).toHaveAttribute('href', '/')
    })

    it('should render a "Go back" button', () => {
      render(<NotFound />)

      const backButton = screen.getByRole('button', { name: /go back/i })
      expect(backButton).toBeInTheDocument()
    })

    it('should render a contact support link', () => {
      render(<NotFound />)

      const supportLink = screen.getByRole('link', {
        name: /contact support/i,
      })
      expect(supportLink).toBeInTheDocument()
      expect(supportLink).toHaveAttribute('href', 'mailto:support@example.com')
    })
  })

  describe('Navigation', () => {
    it('should call router.back() when the "Go back" button is clicked', async () => {
      const user = userEvent.setup()
      render(<NotFound />)

      const backButton = screen.getByRole('button', { name: /go back/i })
      await user.click(backButton)

      expect(mockRouter.back).toHaveBeenCalledTimes(1)
    })

    it('should not call router.back() without user interaction', () => {
      render(<NotFound />)

      expect(mockRouter.back).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should render a main landmark', () => {
      render(<NotFound />)

      const mainElement = screen.getByRole('main')
      expect(mainElement).toBeInTheDocument()
    })

    it('should have aria-labelledby pointing to the heading', () => {
      render(<NotFound />)

      const mainElement = screen.getByRole('main')
      expect(mainElement).toHaveAttribute('aria-labelledby', 'not-found-title')

      const heading = screen.getByRole('heading', {
        name: /page not found/i,
      })
      expect(heading).toHaveAttribute('id', 'not-found-title')
    })

    it('should mark the 404 text as aria-hidden', () => {
      render(<NotFound />)

      const decorativeText = screen.getByText('404')
      expect(decorativeText).toHaveAttribute('aria-hidden', 'true')
    })

    it('should contain a navigation landmark for action buttons', () => {
      render(<NotFound />)

      const nav = screen.getByRole('navigation')
      expect(nav).toBeInTheDocument()
    })
  })
})
