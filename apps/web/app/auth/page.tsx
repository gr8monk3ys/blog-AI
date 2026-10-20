import type { Metadata } from 'next'
import Link from 'next/link'
import SiteFooter from '../../components/SiteFooter'
import SiteHeader from '../../components/SiteHeader'
import { buttonVariants } from '../../components/ui/Button'
import { SignIn } from '../../lib/clerk-ui'
import { clerkAppearance } from '../../lib/clerk-appearance'

// Back-compat route: the app previously used /auth for Supabase email/password.
// Keep /auth as a Clerk Sign In page.
export const metadata: Metadata = {
  title: 'Authentication',
  description: 'Sign in to Blog AI and access your content generation workspace.',
}

// One centred 28rem column (DESIGN.md → Layout): a wall label, the headline
// in Fraunces, then Clerk's form on the tokens — or, with no Clerk key, an
// honest notice in the same voice with the view's one primary action.
export default function AuthPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <section className="mx-auto max-w-md px-4 py-14 sm:px-6 md:py-20">
          {publishableKey ? (
            <>
              <p className="label-mono">Sign in</p>
              <h1 className="text-page-title mt-3">Welcome back.</h1>
              <p className="mt-3 text-muted-foreground">
                Pick up where your last draft left off.
              </p>
              <div className="mt-8">
                <SignIn
                  routing="path"
                  path="/auth"
                  signUpUrl="/sign-up"
                  appearance={clerkAppearance}
                />
              </div>
            </>
          ) : (
            <>
              <p className="label-mono">Open workspace</p>
              <h1 className="text-page-title mt-3">
                No <span className="whitespace-nowrap">Sign-In</span> Required
              </h1>
              <p className="mt-4 text-muted-foreground">
                This deployment runs without authentication, so the full workspace is open. Jump
                straight in — no account needed.
              </p>
              <Link href="/generate" className={buttonVariants({ size: 'lg', className: 'mt-8' })}>
                Open the Workspace
              </Link>
              <p className="mt-8 border-t border-border pt-6 text-sm text-muted-foreground">
                To require accounts, set{' '}
                <code className="font-mono text-foreground">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> and{' '}
                <code className="font-mono text-foreground">CLERK_SECRET_KEY</code>.
              </p>
            </>
          )}
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
