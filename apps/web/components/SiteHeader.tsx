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

/**
 * The header sheet (DESIGN.md → Components → Navigation): sticky, 72px, 90%
 * paper with a 12px blur, a 40% hairline beneath and the one structural
 * shadow — all four in the `header-sheet` utility in globals.css, so the one
 * glass surface and one of the two sanctioned shadows live in one place. The
 * paragraph mark at the left; nav links in the body sans with the ink
 * underline; the theme toggle and the sign-in control in a round hairline
 * pill at the right, the sign-in button being the header's `cta-primary`.
 */
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
      className="ink-underline py-1 text-sm text-foreground transition-colors hover:text-primary"
    >
      {link.label}
    </Link>
  )

  const renderMobileNavLink = (link: NavLink): React.ReactElement => (
    <li key={link.href}>
      <Link
        href={link.href}
        className="flex min-h-11 items-center text-foreground transition-colors hover:text-primary"
        onClick={() => setMobileMenuOpen(false)}
      >
        {link.label}
      </Link>
    </li>
  )

  const signInLink = (href: string): React.ReactElement => (
    <Link href={href} className="cta-primary h-9 rounded-full px-4 text-sm">
      Sign In
    </Link>
  )

  return (
    <header className="header-sheet sticky top-0 z-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-18 items-center justify-between gap-6">
          <Link href="/" className="flex shrink-0 items-center">
            <Logo size={18} />
          </Link>

          <nav className="hidden items-center gap-7 md:flex" aria-label="Primary">
            {isClerkConfigured ? (
              <>
                {publicLinks.map(renderNavLink)}
                <SignedIn>{authLinks.map(renderNavLink)}</SignedIn>
              </>
            ) : (
              navLinks.map(renderNavLink)
            )}
          </nav>

          {/* The round hairline pill: theme, then the account control. */}
          <div className="flex items-center gap-1 rounded-full border border-border bg-card p-1">
            <button
              type="button"
              onClick={cycleTheme}
              className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
              aria-label={themeLabel}
              title={themeLabel}
            >
              {/* All three icons render; CSS shows the one matching
                  <html data-theme-pref> (set before first paint), so the
                  icon never flashes while the stored preference loads. */}
              <SunIcon className="theme-pref-icon size-5" data-pref="light" aria-hidden="true" />
              <MoonIcon className="theme-pref-icon size-5" data-pref="dark" aria-hidden="true" />
              <ComputerDesktopIcon
                className="theme-pref-icon size-5"
                data-pref="system"
                aria-hidden="true"
              />
            </button>
            {isClerkConfigured ? (
              <>
                <SignedIn>
                  <span className="inline-flex size-9 items-center justify-center">
                    <UserButton afterSignOutUrl="/" />
                  </span>
                </SignedIn>
                <SignedOut>{signInLink('/sign-in')}</SignedOut>
              </>
            ) : (
              signInLink('/auth')
            )}
            <button
              type="button"
              className="inline-flex size-9 items-center justify-center rounded-full text-foreground transition-colors hover:bg-muted hover:text-primary md:hidden"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav"
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              onClick={() => setMobileMenuOpen((prev) => !prev)}
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="size-5" aria-hidden="true" />
              ) : (
                <Bars3Icon className="size-5" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {mobileMenuOpen && (
        <nav
          id="mobile-nav"
          className="border-t border-border/60 bg-background md:hidden"
          aria-label="Primary"
        >
          <ul className="mx-auto max-w-7xl divide-y divide-border/60 px-4 py-2 sm:px-6">
            {isClerkConfigured ? (
              <>
                {publicLinks.map(renderMobileNavLink)}
                <SignedIn>{authLinks.map(renderMobileNavLink)}</SignedIn>
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
