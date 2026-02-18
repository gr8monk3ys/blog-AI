import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SiteHeader from '../../components/SiteHeader'

describe('SiteHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the site logo text and link to home', () => {
      render(<SiteHeader />)

      const homeLink = screen.getByRole('link', { name: /blog ai/i })
      expect(homeLink).toBeInTheDocument()
      expect(homeLink).toHaveAttribute('href', '/')
    })

    it('should render all desktop navigation links', () => {
      render(<SiteHeader />)

      const expectedLinks = [
        { label: 'Directory', href: '/tool-directory' },
        { label: 'Tools', href: '/tools' },
        { label: 'Templates', href: '/templates' },
        { label: 'Blog', href: '/blog' },
        { label: 'Pricing', href: '/pricing' },
        { label: 'History', href: '/history' },
      ]

      for (const { label, href } of expectedLinks) {
        const link = screen.getByRole('link', { name: label })
        expect(link).toBeInTheDocument()
        expect(link).toHaveAttribute('href', href)
      }
    })

    it('should render a sign-in link', () => {
      render(<SiteHeader />)

      const signInLinks = screen.getAllByRole('link', { name: /sign in/i })
      expect(signInLinks.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Mobile menu toggle', () => {
    it('should render the hamburger menu button', () => {
      render(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toBeInTheDocument()
    })

    it('should have aria-expanded set to false initially', () => {
      render(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toHaveAttribute('aria-expanded', 'false')
    })

    it('should have aria-controls pointing to mobile-nav', () => {
      render(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      expect(menuButton).toHaveAttribute('aria-controls', 'mobile-nav')
    })

    it('should not render the mobile navigation panel initially', () => {
      render(<SiteHeader />)

      const mobileNav = document.getElementById('mobile-nav')
      expect(mobileNav).not.toBeInTheDocument()
    })

    it('should open the mobile menu when the hamburger button is clicked', async () => {
      const user = userEvent.setup()
      render(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      const mobileNav = document.getElementById('mobile-nav')
      expect(mobileNav).toBeInTheDocument()
    })

    it('should set aria-expanded to true after opening the menu', async () => {
      const user = userEvent.setup()
      render(<SiteHeader />)

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
      render(<SiteHeader />)

      const menuButton = screen.getByRole('button', {
        name: /open navigation menu/i,
      })
      await user.click(menuButton)

      const mobileNav = document.getElementById('mobile-nav')!
      const mobileLinks = within(mobileNav).getAllByRole('link')

      const labels = mobileLinks.map((link) => link.textContent)
      expect(labels).toContain('Directory')
      expect(labels).toContain('Tools')
      expect(labels).toContain('Templates')
      expect(labels).toContain('Blog')
      expect(labels).toContain('Pricing')
      expect(labels).toContain('History')
    })

    it('should close the mobile menu when a mobile nav link is clicked', async () => {
      const user = userEvent.setup()
      render(<SiteHeader />)

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
      render(<SiteHeader />)

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
      render(<SiteHeader />)

      expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('should contain a navigation landmark for desktop links', () => {
      render(<SiteHeader />)

      const navElements = screen.getAllByRole('navigation')
      expect(navElements.length).toBeGreaterThanOrEqual(1)
    })

    it('should mark decorative icons as aria-hidden', () => {
      const { container } = render(<SiteHeader />)

      const sparklesIcon = container.querySelector(
        'svg[aria-hidden="true"]'
      )
      expect(sparklesIcon).toBeInTheDocument()
    })
  })
})
