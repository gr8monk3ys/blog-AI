import type { Metadata } from 'next'
import Link from 'next/link'
import SiteFooter from '../../components/SiteFooter'
import SiteHeader from '../../components/SiteHeader'
import { SignIn } from '../../lib/clerk-ui'

// Back-compat route: the app previously used /auth for Supabase email/password.
// Keep /auth as a Clerk Sign In page.
export const metadata: Metadata = {
  title: 'Authentication',
  description: 'Sign in to Blog AI and access your content generation workspace.',
}

export default function AuthPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">

      <section className="py-14 sm:py-20">
        <div className="max-w-lg mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 sm:p-8">
            {publishableKey ? (
              <SignIn routing="path" path="/auth" signUpUrl="/sign-up" />
            ) : (
              <div className="text-center space-y-4">
                <h1 className="text-xl font-semibold text-gray-900">
                  No sign-in required
                </h1>
                <p className="text-sm text-gray-600">
                  This deployment runs without authentication, so the full
                  workspace is open. Jump straight in — no account needed.
                </p>
                <Link
                  href="/generate"
                  className="inline-flex items-center justify-center rounded-lg bg-amber-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-amber-700"
                >
                  Open the workspace
                </Link>
                <p className="text-xs text-gray-400">
                  To require accounts, set <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code>{' '}
                  and <code>CLERK_SECRET_KEY</code>.
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      </main>
      <SiteFooter />
    </>
  )
}
