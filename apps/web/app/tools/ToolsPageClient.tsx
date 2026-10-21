'use client'

import Link from 'next/link'
import { Suspense } from 'react'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import ToolGrid from '../../components/tools/ToolGrid'
import { buttonVariants } from '../../components/ui/Button'

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@lscaturchio.xyz'

const QUICK_STATS = [
  { value: '29+', label: 'AI Tools' },
  { value: '8', label: 'Categories' },
  { value: '50+', label: 'Content Formats' },
]

// The tools directory on the notebook: a wide index header (wall label,
// headline, description, the figures as one row of wall labels), the
// catalogue as hairline rows, and a closing CTA with the view's one primary
// button. Nothing animates in: the h1 is the LCP element and paints in the
// server HTML.
function ToolsPageContent() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <header className="mx-auto max-w-7xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <p className="label-mono">Tools</p>
          <h1 className="text-page-title mt-3 max-w-3xl">AI Writing Tools</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Discover powerful AI tools to create content for blogs, emails, social media, and
            more. Start writing smarter today.
          </p>
          <ul className="label-mono mt-8 flex flex-wrap gap-x-6 gap-y-2 border-t border-border/60 pt-6">
            {QUICK_STATS.map((stat) => (
              <li key={stat.label}>
                <span className="text-foreground">{stat.value}</span> {stat.label}
              </li>
            ))}
          </ul>
        </header>

        <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 md:pb-20 lg:px-8">
          {/* The rows are the first content under the page <h1>, so their
              titles are the h2 level of this page; the CTA below is the other
              h2. ToolGrid reads ?category= itself, hydration-safely (reading
              window during render here made server and client HTML differ). */}
          <ToolGrid headingLevel={2} />
        </section>

        <hr className="gallery-rule" />

        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <div className="max-w-2xl">
            <p className="label-mono">Need something else</p>
            <h2 className="text-section-title mt-3">Can’t Find What You Need?</h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground text-pretty">
              Use our flexible Blog Post or Book generators for custom content creation with
              advanced options.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Link href="/" className={buttonVariants({ size: 'lg' })}>
                Open Content Generator
              </Link>
              <a
                href={`mailto:${SUPPORT_EMAIL}?subject=Tool%20Request`}
                className="label-mono label-link ink-underline transition-colors hover:text-primary"
              >
                Request a Tool
              </a>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

export default function ToolsPageClient() {
  return (
    <Suspense
      fallback={
        <main className="label-mono flex min-h-screen items-center justify-center">
          Loading tools…
        </main>
      }
    >
      <ToolsPageContent />
    </Suspense>
  )
}
