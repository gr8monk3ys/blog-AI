import type { Metadata } from 'next'
import SiteFooter from '../../../components/SiteFooter'
import SiteHeader from '../../../components/SiteHeader'
import { SignUp } from '../../../lib/clerk-ui'
import { clerkAppearance } from '../../../lib/clerk-appearance'

export const metadata: Metadata = {
  title: 'Sign Up',
  description: 'Create your Blog AI account and start generating content with AI-powered workflows.',
}

// One centred 28rem column (DESIGN.md → Layout): a wall label, the headline
// in Fraunces, then Clerk's form on the tokens. The "not configured" notice
// is in the same voice.
export default function SignUpPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <section className="mx-auto max-w-md px-4 py-14 sm:px-6 md:py-20">
          <p className="label-mono">Sign up</p>
          <h1 className="text-page-title mt-3">Start your first draft.</h1>
          <p className="mt-3 text-muted-foreground">
            Free to start. No credit card required.
          </p>
          <div className="mt-8">
            {publishableKey ? (
              <SignUp
                routing="path"
                path="/sign-up"
                signInUrl="/sign-in"
                appearance={clerkAppearance}
              />
            ) : (
              <div className="border-y border-border py-6 text-sm text-muted-foreground">
                <p className="label-mono">Not configured</p>
                <p className="mt-3">
                  Clerk is not configured. Set{' '}
                  <code className="font-mono text-foreground">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> and{' '}
                  <code className="font-mono text-foreground">CLERK_SECRET_KEY</code> to enable sign-up.
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
