'use client'

import Link from 'next/link'
import { SignedIn, SignedOut, UserButton } from '@clerk/nextjs'

interface NavLink {
  href: string
  label: string
}

interface AuthNavLinksProps {
  authLinks: NavLink[]
  mobile?: boolean
  onNavigate?: () => void
}

export function AuthNavLinks({
  authLinks,
  mobile = false,
  onNavigate,
}: AuthNavLinksProps) {
  return (
    <SignedIn>
      {authLinks.map((link) =>
        mobile ? (
          <li key={link.href}>
            <Link
              href={link.href}
              className="block rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-amber-600 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-amber-400 transition-colors"
              onClick={onNavigate}
            >
              {link.label}
            </Link>
          </li>
        ) : (
          <Link
            key={link.href}
            href={link.href}
            className="hover:text-amber-600 transition-colors"
          >
            {link.label}
          </Link>
        )
      )}
    </SignedIn>
  )
}

export function AuthControls() {
  return (
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
  )
}
