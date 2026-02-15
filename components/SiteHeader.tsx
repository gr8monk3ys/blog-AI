'use client'

import Link from 'next/link'
import { SparklesIcon } from '@heroicons/react/24/outline'
import { SignedIn, SignedOut, UserButton } from '@clerk/nextjs'

export default function SiteHeader() {
  const isClerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <header className="sticky top-0 z-20 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-amber-600" aria-hidden="true" />
            <span className="font-semibold text-gray-900">Blog AI</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-gray-700">
            <Link href="/tool-directory" className="hover:text-amber-600 transition-colors">Directory</Link>
            <Link href="/tools" className="hover:text-amber-600 transition-colors">Tools</Link>
            <Link href="/templates" className="hover:text-amber-600 transition-colors">Templates</Link>
            <Link href="/blog" className="hover:text-amber-600 transition-colors">Blog</Link>
            <Link href="/pricing" className="hover:text-amber-600 transition-colors">Pricing</Link>
            <Link href="/history" className="hover:text-amber-600 transition-colors">History</Link>
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
          </div>
        </div>
      </div>
    </header>
  )
}
