'use client'

import { useState } from 'react'
import Link from 'next/link'
import { SparklesIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'
import { SignedIn, SignedOut, UserButton } from '@clerk/nextjs'

interface NavLink {
  href: string
  label: string
  authRequired: boolean
}

const navLinks: NavLink[] = [
  { href: '/tool-directory', label: 'Directory', authRequired: false },
  { href: '/tools', label: 'Tools', authRequired: true },
  { href: '/templates', label: 'Templates', authRequired: true },
  { href: '/blog', label: 'Blog', authRequired: false },
  { href: '/pricing', label: 'Pricing', authRequired: false },
  { href: '/history', label: 'History', authRequired: true },
]

const publicLinks = navLinks.filter((link) => !link.authRequired)
const authLinks = navLinks.filter((link) => link.authRequired)

export default function SiteHeader(): React.ReactElement {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isClerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  const renderNavLink = (link: NavLink): React.ReactElement => (
    <Link
      key={link.href}
      href={link.href}
      className="hover:text-amber-600 transition-colors"
    >
      {link.label}
    </Link>
  )

  const renderMobileNavLink = (link: NavLink): React.ReactElement => (
    <li key={link.href}>
      <Link
        href={link.href}
        className="block rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-amber-600 transition-colors"
        onClick={() => setMobileMenuOpen(false)}
      >
        {link.label}
      </Link>
    </li>
  )

  return (
    <header className="sticky top-0 z-20 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-amber-600" aria-hidden="true" />
            <span className="font-semibold text-gray-900">Blog AI</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-gray-700">
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
            {isClerkConfigured ? (
              <>
                <SignedIn>
                  <UserButton afterSignOutUrl="/" />
                </SignedIn>
                <SignedOut>
                  <Link
                    href="/sign-in"
                    className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 transition-colors text-white"
                  >
                    Sign in
                  </Link>
                </SignedOut>
              </>
            ) : (
              <Link
                href="/auth"
                className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 transition-colors text-white"
              >
                Sign in
              </Link>
            )}
            <button
              type="button"
              className="md:hidden -m-2 inline-flex items-center justify-center rounded-md p-2 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-amber-500"
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
          className="md:hidden border-t border-gray-200 bg-white"
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
