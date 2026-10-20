'use client'

import Link from 'next/link'
import { CheckIcon } from '@heroicons/react/24/outline'
import SiteHeader from '../components/SiteHeader'
import SiteFooter from '../components/SiteFooter'
import { buttonVariants } from '../components/ui/Button'
import { useAuth } from '../lib/clerk-ui'
import {
  FEATURES,
  STEPS,
  PRICING_TIERS,
  SOCIAL_STATS,
  TOOL_CATEGORY_LINKS,
  CAPABILITIES,
} from './_home/data'

// The home page on the notebook (DESIGN.md → Layout, → Components). One
// centred column on open paper; sections divided by a full-width hairline,
// never a background change; every section introduced by a wall label; lists
// as hairline-divided rows with a mono label in the margin; the pricing teaser
// as a ledger on tinted paper. Nothing animates itself in: the first paint is
// the final paint.

const labelLink = 'label-mono label-link ink-underline transition-colors hover:text-primary'

export default function Home(): React.ReactElement {
  const isClerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  const { isLoaded, isSignedIn } = useAuth()

  // Render the signed-out CTA until Clerk positively reports a session.
  // Clerk's <SignedIn>/<SignedOut> BOTH render nothing while clerk.browser.js
  // is still loading — and forever if it fails to load — which left the hero
  // with a subhead, an empty gap, and a "No credit card required" line
  // pointing at no button. The primary action must not depend on a
  // third-party script being reachable.
  const showSignedInCta = isClerkConfigured && isLoaded && isSignedIn
  const startFreeHref = isClerkConfigured ? '/sign-up' : '/auth'

  const primaryCta = showSignedInCta
    ? { href: '/generate', label: 'Start Generating' }
    : { href: startFreeHref, label: 'Start Free' }
  const secondaryCta = showSignedInCta
    ? { href: '/brand', label: 'Open Brand Voice' }
    : { href: '/pricing', label: 'View Plans' }

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        {/* ------------------------------------------------------------- */}
        {/* Masthead                                                      */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 pb-16 pt-14 sm:px-6 md:pb-20 md:pt-20 lg:px-8 lg:pb-24 lg:pt-24">
          <p className="label-mono">AI writing tools · Brand voice training</p>

          {/* The h1 is the LCP element and paints in the server HTML. */}
          <h1 className="text-display mt-6 max-w-4xl">
            Brand-Consistent AI Content For{' '}
            <span className="text-primary">Lean Marketing Teams</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Train your voice once, run repeatable SEO content workflows, and generate
            publish-ready drafts faster without sounding generic.
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link href={primaryCta.href} className={buttonVariants({ size: 'lg' })}>
              {primaryCta.label}
            </Link>
            <Link
              href={secondaryCta.href}
              className={buttonVariants({ variant: 'outline', size: 'lg' })}
            >
              {secondaryCta.label}
            </Link>
          </div>

          <p className="mt-5 text-sm text-muted-foreground">
            No credit card required. Start free, then upgrade when you need bulk and brand
            controls.
          </p>

          {/* The old stat band, as one row of wall labels: the figures are
              catalogue entries, not a display. */}
          <ul className="label-mono mt-14 flex flex-wrap gap-x-6 gap-y-2 border-t border-border/60 pt-6 md:mt-20">
            {SOCIAL_STATS.map((stat) => (
              <li key={stat.label}>
                <span className="text-foreground">{stat.value}</span> {stat.label}
              </li>
            ))}
          </ul>
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* The core system                                               */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <p className="label-mono">The core system</p>
          <h2 className="text-section-title mt-3 max-w-2xl">
            The Core System for Repeatable Content Production
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Focus on the workflows that actually drive upgrades: brand voice, SEO drafting, bulk
            generation, and built-in research.
          </p>
          <NumberedRows items={FEATURES} />
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* Every content type                                            */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <p className="label-mono">Every content type</p>
          <h2 className="text-section-title mt-3 max-w-2xl">Every Content Type Your Team Needs</h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Specialized tools across 8 categories — not one generic prompt box.
          </p>

          {/* Tag lists are not chips (DESIGN.md → Chips): wall-label links. */}
          <nav
            className="mt-10 flex flex-wrap items-baseline gap-x-6 gap-y-1 border-y border-border/60 py-5"
            aria-label="Browse tools by category"
          >
            <span className="label-mono">Browse</span>
            {TOOL_CATEGORY_LINKS.map((category) => (
              <Link
                key={category.key}
                href={`/tools/category/${category.key}`}
                className={labelLink}
              >
                {category.label}
              </Link>
            ))}
          </nav>

          <p className="mt-8">
            <Link href="/tool-directory" className={labelLink}>
              Browse the Full Directory →
            </Link>
          </p>
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* How it works                                                  */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <p className="label-mono">How it works</p>
          <h2 className="text-section-title mt-3 max-w-2xl">
            Three Steps to a Content Engine Your Team Can Reuse
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Stop restarting from prompts and pasting between tools. Save your standards, run the
            workflow, and publish with less cleanup.
          </p>
          <NumberedRows as="ol" items={STEPS} />
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* Premium capabilities                                          */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <p className="label-mono">Premium capabilities</p>
          <h2 className="text-section-title mt-3 max-w-2xl">
            Premium Capabilities That Pay for Themselves
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Each upgrade tier unlocks tools that directly reduce your content production time.
          </p>
          <ul className="mt-10 divide-y divide-border border-y border-border">
            {CAPABILITIES.map((cap) => (
              <li key={cap.title} className="grid gap-2 py-5 sm:grid-cols-[7rem_1fr] sm:gap-8 sm:py-6">
                <span className="label-mono pt-1.5">{cap.tier}</span>
                <div className="min-w-0">
                  <h3 className="text-card-title">{cap.title}</h3>
                  <p className="mt-1.5 max-w-2xl leading-relaxed text-muted-foreground">
                    {cap.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* Plans: the ledger                                             */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <p className="label-mono">Plans</p>
          <h2 className="text-section-title mt-3 max-w-2xl">Plans That Grow with You</h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            Start with the core workflow, then move up when you need more volume, research depth,
            brand controls, and bulk production.
          </p>

          <PricingLedger />

          <p className="mt-8">
            <Link href="/pricing" className={labelLink}>
              Compare All Features in Detail →
            </Link>
          </p>
        </section>

        <hr className="gallery-rule" />

        {/* ------------------------------------------------------------- */}
        {/* Final CTA                                                     */}
        {/* ------------------------------------------------------------- */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8 lg:py-24">
          <div className="max-w-2xl">
            <p className="label-mono">Get started</p>
            <h2 className="text-section-title mt-3">
              Build a Workflow Your Team Will Actually Reuse
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground text-pretty">
              Use Blog AI when prompt-by-prompt writing stops scaling and you need faster, more
              consistent SEO content production.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Link href={primaryCta.href} className={buttonVariants({ size: 'lg' })}>
                {primaryCta.label}
              </Link>
              <Link href="/brand" className={labelLink}>
                See Brand Voice
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

// ---------------------------------------------------------------------------
// Section components
// ---------------------------------------------------------------------------

/**
 * A numbered row list (DESIGN.md → Components → Cards / Rows): a mono numeral
 * in the margin, a Fraunces title, a muted description, hairlines between.
 * The features and the steps share it so they read as the same device.
 */
function NumberedRows({
  items,
  as: Tag = 'ul',
}: {
  items: ReadonlyArray<{ number: string; title: string; description: string }>
  as?: 'ul' | 'ol'
}): React.ReactElement {
  return (
    <Tag className="mt-10 divide-y divide-border border-y border-border">
      {items.map((item) => (
        <li key={item.number} className="grid gap-3 py-6 sm:grid-cols-[5rem_1fr] sm:gap-8 sm:py-8">
          <span className="label-mono pt-1.5" aria-hidden="true">
            {item.number}
          </span>
          <div className="min-w-0">
            <h3 className="text-card-title">{item.title}</h3>
            <p className="mt-2 max-w-2xl leading-relaxed text-muted-foreground">
              {item.description}
            </p>
          </div>
        </li>
      ))}
    </Tag>
  )
}

/**
 * The pricing teaser as a ledger: three columns on tinted paper divided by
 * hairlines, the price in mono tabular, features as hairline rows with the
 * check in ink. The masthead holds this view's one primary button, so every
 * plan's action here is the secondary shape.
 */
function PricingLedger(): React.ReactElement {
  return (
    <div className="mt-12 grid divide-y divide-border/70 border border-border/70 bg-muted/55 md:grid-cols-3 md:divide-x md:divide-y-0">
      {PRICING_TIERS.map((tier, index) => (
        <div key={tier.name} className="flex flex-col p-6 sm:p-8">
          <p className="label-mono">
            {String(index + 1).padStart(2, '0')}
            {tier.highlighted ? ' · Most popular' : ''}
          </p>
          <h3 className="text-card-title mt-3">{tier.name}</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{tier.description}</p>

          <p className="mt-6 flex items-baseline gap-2">
            <span className="text-section-title font-mono font-medium tabular-nums tracking-tight">
              {tier.price}
            </span>
            <span className="label-mono">{tier.period}</span>
          </p>

          <ul className="mt-8 grow divide-y divide-border/70 border-y border-border/70" role="list">
            {tier.features.map((feature) => (
              <li key={feature} className="flex items-start gap-3 py-3 text-sm">
                <CheckIcon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>

          <Link
            href={tier.href}
            className={buttonVariants({ variant: 'outline', className: 'mt-8 w-full' })}
          >
            {tier.cta}
          </Link>
        </div>
      ))}
    </div>
  )
}
