'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Bars3Icon, XMarkIcon, SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline'
import { useTheme } from '../hooks/useTheme'
import { SignedIn, SignedOut, UserButton } from '../lib/clerk-ui'
import { Logo } from './brand/Logo'

interface NavLink {
  href: string
  label: string
  authRequired: boolean
  /** When set, the link only appears if this build-time flag is enabled. */
  flag?: boolean
}

// The Knowledge Base surface is gated behind a backend feature flag
// (ENABLE_KNOWLEDGE_BASE, default off). Mirror that on the frontend with
// NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE so we don't advertise a route that the
// backend will reject. Defaults to off to match the backend.
const knowledgeBaseEnabled =
  process.env.NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE === 'true'

const navLinks: NavLink[] = [
  { href: '/pricing', label: 'Pricing', authRequired: false },
  { href: '/blog', label: 'Blog', authRequired: false },
  { href: '/brand', label: 'Brand Voice', authRequired: true },
  { href: '/bulk', label: 'Bulk', authRequired: true },
  { href: '/generate', label: 'Generate', authRequired: true },
  { href: '/tools', label: 'Tools', authRequired: true },
  { href: '/knowledge', label: 'Knowledge Base', authRequired: true, flag: knowledgeBaseEnabled },
  { href: '/templates', label: 'Templates', authRequired: true },
  { href: '/images', label: 'Images', authRequired: true },
  { href: '/social', label: 'Social', authRequired: true },
  { href: '/team', label: 'Team', authRequired: true },
].filter((link) => link.flag !== false)

const publicLinks = navLinks.filter((link) => !link.authRequired)
const authLinks = navLinks.filter((link) => link.authRequired)

const THEME_CYCLE = ['light', 'dark', 'system'] as const

export default function SiteHeader(): React.ReactElement {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isClerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  const { theme, setTheme } = useTheme()

  const cycleTheme = (): void => {
    const idx = THEME_CYCLE.indexOf(theme)
    const next = THEME_CYCLE[(idx + 1) % THEME_CYCLE.length] as typeof THEME_CYCLE[number]
    setTheme(next)
  }

  const themeLabel = theme === 'dark' ? 'Dark mode' : theme === 'light' ? 'Light mode' : 'System theme'

  const renderNavLink = (link: NavLink): React.ReactElement => (
    <Link
      key={link.href}
      href={link.href}
      className="ink-underline hover:text-primary transition-colors"
    >
      {link.label}
    </Link>
  )

  const renderMobileNavLink = (link: NavLink): React.ReactElement => (
    <li key={link.href}>
      <Link
        href={link.href}
        className="block rounded-md px-3 py-2 text-sm text-foreground hover:bg-card hover:text-primary transition-colors"
        onClick={() => setMobileMenuOpen(false)}
      >
        {link.label}
      </Link>
    </li>
  )

  // The header sheet (`header-sheet` in globals.css): 90% paper with a 12px
  // blur over the content scrolling under it, a 40% hairline beneath, and the
  // one structural shadow (DESIGN.md → Elevation → The Two Sheets Rule).
  return (
    <header className="header-sheet sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center">
            <Logo size={18} />
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-foreground">
            {isClerkConfigured ? (
              <>
                {publicLinks.map(renderNavLink)}
                <SignedIn>
                  {authLinks.map(renderNavLink)}
                </SignedIn>
              </>
            ) : (
              navLinks.map(renderNavLink)
            )}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <button
              type="button"
              onClick={cycleTheme}
              className="rounded-md p-1.5 text-muted-foreground hover:text-primary hover:bg-card transition-colors"
              aria-label={themeLabel}
              title={themeLabel}
            >
              {/* All three icons render; CSS shows the one matching
                  <html data-theme-pref> (set before first paint), so the
                  icon never flashes while the stored preference loads. */}
              <SunIcon className="theme-pref-icon h-5 w-5" data-pref="light" aria-hidden="true" />
              <MoonIcon className="theme-pref-icon h-5 w-5" data-pref="dark" aria-hidden="true" />
              <ComputerDesktopIcon
                className="theme-pref-icon h-5 w-5"
                data-pref="system"
                aria-hidden="true"
              />
            </button>
            {isClerkConfigured ? (
              <>
                <SignedIn>
                  <UserButton afterSignOutUrl="/" />
                </SignedIn>
                <SignedOut>
                  <Link href="/sign-in" className="cta-primary rounded-lg px-3 py-1.5">
                    Sign In
                  </Link>
                </SignedOut>
              </>
            ) : (
              <Link href="/auth" className="cta-primary rounded-lg px-3 py-1.5">
                Sign In
              </Link>
            )}
            <button
              type="button"
              className="md:hidden -m-2 inline-flex items-center justify-center rounded-md p-2 text-foreground hover:bg-card hover:text-primary transition-colors"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav"
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              onClick={() => setMobileMenuOpen((prev) => !prev)}
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" aria-hidden="true" />
              ) : (
                <Bars3Icon className="h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {mobileMenuOpen && (
        <nav
          id="mobile-nav"
          className="md:hidden border-t border-border bg-background"
        >
          <ul className="space-y-1 px-4 py-3">
            {isClerkConfigured ? (
              <>
                {publicLinks.map(renderMobileNavLink)}
                <SignedIn>
                  {authLinks.map(renderMobileNavLink)}
                </SignedIn>
              </>
            ) : (
              navLinks.map(renderMobileNavLink)
            )}
          </ul>
        </nav>
      )}
    </header>
  )
}
