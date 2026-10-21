'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { buttonVariants } from '../components/ui/Button'

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@lscaturchio.xyz'

/**
 * The 404 page: an honest empty state in the house voice (DESIGN.md → Do) —
 * a wall label, one serif line, one primary action — in a single column at
 * the reading measure. No watermark numeral, no glow.
 */
export default function NotFound() {
  const router = useRouter()

  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="flex min-h-screen flex-col justify-center"
      role="main"
      aria-labelledby="not-found-title"
    >
      <div className="mx-auto w-full max-w-2xl px-4 py-16 sm:px-6 md:py-24 lg:px-8">
        <p className="label-mono">
          <span aria-hidden="true">404</span>
          <span className="sr-only">Error 404</span> · Not found
        </p>

        <h1 id="not-found-title" className="text-page-title mt-4">
          Page Not Found
        </h1>

        <p className="mt-4 max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
          Sorry, we could not find the page you are looking for. It may have been moved, deleted,
          or the URL might be incorrect.
        </p>

        <nav className="mt-8 flex flex-wrap items-center gap-5" aria-label="Where to go next">
          <Link href="/" className={buttonVariants({ size: 'lg' })}>
            Go Back Home
          </Link>
          <button
            type="button"
            onClick={() => router.back()}
            className="label-mono label-link ink-underline transition-colors hover:text-primary"
          >
            Go Back
          </button>
        </nav>

        <p className="mt-12 border-t border-border pt-6 text-sm text-muted-foreground">
          If you believe this is a mistake, please{' '}
          <a href={`mailto:${SUPPORT_EMAIL}`} className="ink-underline text-primary">
            contact support
          </a>
          .
        </p>
      </div>
    </main>
  )
}
