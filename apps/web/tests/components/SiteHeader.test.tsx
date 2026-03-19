import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest'
import { render, screen, within, RenderOptions } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '../../hooks/useTheme'
import SiteHeader from '../../components/SiteHeader'

function renderWithProviders(ui: React.ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: ThemeProvider, ...options })
}

describe('SiteHeader', () => {
  const originalClerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  beforeEach(() => {
    vi.clearAllMocks()
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  })

  afterAll(() => {
    if (originalClerkKey) {
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = originalClerkKey
    } else {
      delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    }
  })

  describe('Rendering', () => {
    it('should render the site logo text and link to home', () => {
      renderWithProviders(<SiteHeader />)

      const homeLink = screen.getByRole('link', { name: /blog ai/i })
      expect(homeLink).toBeInTheDocument()
      expect(homeLink).toHaveAttribute('href', '/')
    })

    it('should render all desktop navigation links', () => {
      renderWithProviders(<SiteHeader />)

      const expectedLinks = [
        { label: 'Pricing', href: '/pricing' },
        { label: 'Blog', href: '/blog' },
        { label: 'Brand Voice', href: '/brand' },
        { label: 'Bulk', href: '/bulk' },
        { label: 'Generate', href: '/generate' },
        { label: 'Tools', href: '/tools' },
        { label: 'Templates', href: '/templates' },
        { label: 'Team', href: '/team' },
      ]

      for (const { label, href } of expectedLinks) {
        const link = screen.getByRole('link', { name: label })
        expect(link).toBeInTheDocument()
        expect(link).toHaveAttribute('href', href)
      }
    })

    it('should render a sign-in link', () => {
      renderWithProviders(<SiteHeader />)

      const signInLinks = screen.getAllByRole('link', { name: /sign in/i })
      expect(signInLinks.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Mobile menu toggle', () => {
    it('should render the hamburger menu button', () => {
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toBeInTheDocument()
    })

    it('should have aria-expanded set to false initially', () => {
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toHaveAttribute('aria-expanded', 'false')
    })

    it('should have aria-controls pointing to mobile-nav', () => {
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toHaveAttribute('aria-controls', 'mobile-nav')
    })

    it('should not render the mobile navigation panel initially', () => {
      renderWithProviders(<SiteHeader />)

      const mobileNav = document.getElementById('mobile-nav')
      expect(mobileNav).not.toBeInTheDocument()
    })

    it('should open the mobile menu when the hamburger button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      const mobileNav = document.getElementById('mobile-nav')
      expect(mobileNav).toBeInTheDocument()
    })

    it('should set aria-expanded to true after opening the menu', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      // After clicking, the button label changes to "Close navigation menu"
      const closeButton = screen.getByRole('button', {
        name: /close navigation menu/i,
      })
      expect(closeButton).toHaveAttribute('aria-expanded', 'true')
    })

    it('should show all navigation links in the mobile menu', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      const mobileNav = document.getElementById('mobile-nav')!
      const mobileLinks = within(mobileNav).getAllByRole('link')

      const labels = mobileLinks.map((link) => link.textContent)
      expect(labels).toContain('Pricing')
      expect(labels).toContain('Blog')
      expect(labels).toContain('Brand Voice')
      expect(labels).toContain('Bulk')
      expect(labels).toContain('Generate')
      expect(labels).toContain('Tools')
      expect(labels).toContain('Templates')
      expect(labels).toContain('Team')
    })

    it('should close the mobile menu when a mobile nav link is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SiteHeader />)

      // Open the menu
      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      const mobileNav = document.getElementById('mobile-nav')!
      const blogLink = within(mobileNav).getByRole('link', { name: 'Blog' })
      await user.click(blogLink)

      // The mobile nav should disappear
      expect(document.getElementById('mobile-nav')).not.toBeInTheDocument()
    })

    it('should close the mobile menu when the close button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SiteHeader />)

      // Open the menu
      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      // Click the close button
      const closeButton = screen.getByRole('button', {
        name: /close navigation menu/i,
      })
      await user.click(closeButton)

      expect(document.getElementById('mobile-nav')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should use a header landmark', () => {
      renderWithProviders(<SiteHeader />)

      expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('should contain a navigation landmark for desktop links', () => {
      renderWithProviders(<SiteHeader />)

      const navElements = screen.getAllByRole('navigation')
      expect(navElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should mark decorative icons as aria-hidden', () => {
      const { container } = renderWithProviders(<SiteHeader />)

      const sparklesIcon = container.querySelector(
        'svg[aria-hidden="true"]'
      )
      expect(sparklesIcon).toBeInTheDocument()
    })
  })

  describe('Clerk-configured branch', () => {
    it('should render Clerk auth controls when Clerk is configured', () => {
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock'

      renderWithProviders(<SiteHeader />)

      expect(screen.getByTestId('clerk-user-button')).toBeInTheDocument()
      const signInLink = screen.getByRole('link', { name: /^sign in$/i })
      expect(signInLink).toHaveAttribute('href', '/sign-in')
    })

    it('should render auth links in mobile navigation when Clerk is configured', async () => {
      const user = userEvent.setup()
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock'

      renderWithProviders(<SiteHeader />)

      await user.click(
        screen.getByRole('button', { name: /open navigation menu/i })
      )

      const mobileNav = document.getElementById('mobile-nav')!
      expect(within(mobileNav).getByRole('link', { name: 'Generate' })).toBeInTheDocument()
      expect(within(mobileNav).getByRole('link', { name: 'Brand Voice' })).toBeInTheDocument()
      expect(within(mobileNav).getByRole('link', { name: 'Bulk' })).toBeInTheDocument()
      expect(within(mobileNav).getByRole('link', { name: 'Templates' })).toBeInTheDocument()
      expect(within(mobileNav).getByRole('link', { name: 'Team' })).toBeInTheDocument()
    })
  })
})
