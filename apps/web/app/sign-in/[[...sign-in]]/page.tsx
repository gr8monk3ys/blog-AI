import type { Metadata } from 'next'
import SiteFooter from '../../../components/SiteFooter'
import SiteHeader from '../../../components/SiteHeader'
import { SignIn } from '../../../lib/clerk-ui'
import { clerkAppearance } from '../../../lib/clerk-appearance'

export const metadata: Metadata = {
  title: 'Sign In',
  description: 'Sign in to your Blog AI account to access content generation tools and workspace data.',
}

// One centred 28rem column (DESIGN.md → Layout): a wall label, the headline
// in Fraunces, then Clerk's form on the tokens. The "not configured" notice
// is in the same voice.
export default function SignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <section className="mx-auto max-w-md px-4 py-14 sm:px-6 md:py-20">
          <p className="label-mono">Sign in</p>
          <h1 className="text-page-title mt-3">Welcome back.</h1>
          <p className="mt-3 text-muted-foreground">
            Pick up where your last draft left off.
          </p>
          <div className="mt-8">
            {publishableKey ? (
              <SignIn
                routing="path"
                path="/sign-in"
                signUpUrl="/sign-up"
                appearance={clerkAppearance}
              />
            ) : (
              <div className="border-y border-border py-6 text-sm text-muted-foreground">
                <p className="label-mono">Not configured</p>
                <p className="mt-3">
                  Clerk is not configured. Set{' '}
                  <code className="font-mono text-foreground">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> and{' '}
                  <code className="font-mono text-foreground">CLERK_SECRET_KEY</code> to enable sign-in.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
