'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { CheckIcon, MinusIcon } from '@heroicons/react/24/outline'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { Badge } from '../../components/ui/Badge'
import { buttonVariants } from '../../components/ui/Button'
import { useAuth } from '../../lib/clerk-ui'
import { UsageTier } from '../../types/usage'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { normalizePricingTiers, type PublicPricingTier } from './tiers'
import { formatNumber } from '@/lib/format'

type BillingCycle = 'monthly' | 'yearly'

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@lscaturchio.xyz'

const TIER_POSITIONING: Record<Exclude<UsageTier, 'business'>, {
  audience: string
  valueProp: string
  cta: string
}> = {
  free: {
    audience: 'Best for evaluation',
    valueProp: 'Test the core writing workflow before you commit to a paid content process.',
    cta: 'Start Free',
  },
  starter: {
    audience: 'Best for solo operators',
    valueProp: 'Use Starter when you publish regularly and need more volume, research, and exports without team complexity.',
    cta: 'Choose Starter',
  },
  pro: {
    audience: 'Best for lean marketing teams',
    valueProp: 'Use Pro when brand voice consistency, bulk generation, and higher monthly throughput directly save the team time.',
    cta: 'Choose Pro',
  },
}

const COMPARISON_ROWS: Array<{ name: string } & Record<Exclude<UsageTier, 'business'>, boolean>> = [
  { name: 'Blog generation', free: true, starter: true, pro: true },
  { name: 'Book generation', free: false, starter: true, pro: true },
  { name: 'Export formats', free: false, starter: true, pro: true },
  { name: 'Research mode', free: false, starter: true, pro: true },
  { name: 'Bulk generation', free: false, starter: false, pro: true },
  { name: 'Brand voice training', free: false, starter: false, pro: true },
  { name: 'Priority support', free: false, starter: true, pro: true },
]

const FAQ = [
  {
    q: 'Can I upgrade or downgrade anytime?',
    a: 'Yes, you can change your plan at any time. When upgrading, you will get immediate access to the new features. When downgrading, the change will take effect at the end of your current billing period.',
  },
  {
    q: 'How should I choose between Starter and Pro?',
    a: 'Choose Starter if one person is running the content workflow and mostly needs more volume, research, and exports. Choose Pro if you need brand voice controls, bulk generation, and enough capacity for a recurring team workflow.',
  },
  {
    q: 'What happens when I reach my limit?',
    a: 'When you hit your daily or monthly limit, new generations stop until the limit resets or you upgrade. That makes plan limits a real workflow boundary, not just a billing detail.',
  },
  {
    q: 'Do unused generations roll over?',
    a: 'No. Limits reset on the normal schedule for your plan, so the right way to buy is based on your steady publishing volume, not occasional spikes.',
  },
  {
    q: 'Why is Business not listed here?',
    a: 'Business stays off the public pricing page until the team and admin surface is strong enough to support it. The current public plans are the ones we are ready to sell confidently.',
  },
  {
    q: 'What payment methods do you accept?',
    a: 'We accept major credit cards through Stripe checkout.',
  },
]

interface PricingPageClientProps {
  /**
   * Plans resolved on the server (see ./tiers). They are rendered in the
   * document, so the ledger never grows after hydration.
   */
  initialTiers: PublicPricingTier[]
}

// The pricing page on the notebook: an index header, the plans as a ledger
// on tinted paper (DESIGN.md → Components → Cards / Rows), the comparison as
// a hairline table, the FAQ as a definition list. Nothing animates itself in.
export default function PricingPage({ initialTiers }: PricingPageClientProps) {
  const [billingCycle, setBillingCycle] = useState<BillingCycle>('monthly')
  const [currentTier, setCurrentTier] = useState<UsageTier | null>(null)
  const [tiers, setTiers] = useState<PublicPricingTier[]>(initialTiers)
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState<UsageTier | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const router = useRouter()
  const { isSignedIn } = useAuth()

  const fetchPricing = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.payments.pricing, {
        headers: await getDefaultHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to load pricing')
      }

      const data = await response.json()
      if (data?.success && Array.isArray(data?.tiers)) {
        const filtered = normalizePricingTiers(data.tiers as PublicPricingTier[])
        // Only ever replace the server-rendered plans with a non-empty list:
        // an empty grid is what used to shove the rest of the page around.
        if (filtered.length > 0) setTiers(filtered)
      }
    } catch (err) {
      console.error('Error fetching pricing:', err)
    }
  }

  const fetchCurrentTier = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.usage.stats, {
        headers: await getDefaultHeaders(),
      })

      if (response.ok) {
        const data = await response.json()
        if (data?.tier) setCurrentTier(data.tier)
      }
    } catch (err) {
      console.error('Error fetching current tier:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPricing()
    fetchCurrentTier()

    // Handle Stripe redirect states
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      const checkout = url.searchParams.get('checkout')
      if (checkout === 'success') setSuccess('Subscription updated successfully.')
      if (checkout === 'cancelled') setError('Checkout cancelled.')
    }
  }, [])

  const handleUpgrade = async (tier: UsageTier) => {
    if (tier === currentTier) return

    setUpgrading(tier)
    setError(null)
    setSuccess(null)

    try {
      if (!isSignedIn) {
        router.push('/sign-in?redirect_url=/pricing')
        return
      }

      const tierData = tiers.find((t) => t.id === tier)
      if (!tierData) throw new Error('Unknown tier')

      // Downgrades/cancellations are handled in the Stripe customer portal.
      if (tier === 'free' && currentTier && currentTier !== 'free') {
        const portalResponse = await fetch(API_ENDPOINTS.payments.portal, {
          method: 'POST',
          headers: await getDefaultHeaders(),
          body: JSON.stringify({
            return_url: typeof window !== 'undefined' ? window.location.href : '',
          }),
        })

        if (!portalResponse.ok) {
          const portalData = await portalResponse.json().catch(() => ({}))
          throw new Error(portalData.detail?.error || portalData.error || 'Failed to open billing portal')
        }

        const portalData = await portalResponse.json()
        if (portalData.url && typeof window !== 'undefined') {
          window.location.assign(portalData.url)
          return
        }
        return
      }

      const stripePriceId =
        billingCycle === 'monthly'
          ? tierData.stripe_price_id_monthly
          : tierData.stripe_price_id_yearly

      if (!stripePriceId) {
        throw new Error(
          billingCycle === 'yearly'
            ? 'Yearly billing is not available for this plan yet.'
            : 'This plan is not available for checkout yet.'
        )
      }

      const checkoutResponse = await fetch(API_ENDPOINTS.payments.checkout, {
        method: 'POST',
        headers: await getDefaultHeaders(),
        body: JSON.stringify({
          price_id: stripePriceId,
          success_url: `${window.location.origin}/pricing?checkout=success`,
          cancel_url: `${window.location.origin}/pricing?checkout=cancelled`,
        }),
      })

      if (!checkoutResponse.ok) {
        const checkoutData = await checkoutResponse.json().catch(() => ({}))
        throw new Error(checkoutData.detail?.error || checkoutData.error || 'Failed to create checkout session')
      }

      const checkoutData = await checkoutResponse.json()
      if (checkoutData.url && typeof window !== 'undefined') {
        window.location.assign(checkoutData.url)
        return
      }

      throw new Error('Failed to create checkout session')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upgrade. Please try again.')
    } finally {
      setUpgrading(null)
    }
  }

  const getButtonText = (tier: UsageTier) => {
    if (loading) return 'Loading…'
    if (upgrading === tier) return 'Processing…'
    if (tier === currentTier) return 'Current Plan'
    if (tier === 'free' && currentTier && currentTier !== 'free') return 'Manage in Portal'
    return TIER_POSITIONING[tier as Exclude<UsageTier, 'business'>]?.cta || 'Checkout'
  }

  // Pro carries the ledger's one filled button; the other plans and the
  // current plan take the secondary shape (DESIGN.md → Components → Buttons).
  const getButtonClassName = (tier: UsageTier) =>
    buttonVariants({
      variant: tier === 'pro' && tier !== currentTier ? 'default' : 'outline',
      className: 'w-full',
    })

  const billingButton = (cycle: BillingCycle, label: React.ReactNode) => {
    const selected = billingCycle === cycle
    return (
      <button
        type="button"
        onClick={() => setBillingCycle(cycle)}
        aria-pressed={selected}
        className={`inline-flex h-9 items-center gap-2 rounded-full px-4 text-sm font-medium transition-colors ${
          selected
            ? 'border border-border bg-card text-foreground'
            : 'text-muted-foreground hover:text-primary'
        }`}
      >
        {label}
      </button>
    )
  }

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        {/* Index header */}
        <section className="mx-auto max-w-5xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <header className="max-w-2xl">
            <p className="label-mono">Pricing</p>
            <h1 className="text-page-title mt-3">
              Pricing For Brand-Safe Content Production
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground text-pretty">
              Pick the plan that matches your publishing volume and workflow maturity. Start free,
              move to Starter when you publish regularly, and upgrade to Pro when the team needs
              brand controls and bulk production.
            </p>
          </header>

          {/* Billing toggle: a segmented pill on tinted paper. */}
          <div
            className="mt-8 inline-flex items-center gap-1 rounded-full bg-muted/70 p-1"
            role="group"
            aria-label="Billing cycle"
          >
            {billingButton('monthly', 'Monthly')}
            {billingButton(
              'yearly',
              <>
                Yearly
                <span className="label-mono text-success">Save 17%</span>
              </>
            )}
          </div>

          {success && (
            <p
              className="mt-6 max-w-2xl border-l-2 border-success py-1 pl-4 text-sm text-success"
              role="status"
            >
              {success}
            </p>
          )}
          {error && (
            <p
              className="mt-6 max-w-2xl border-l-2 border-destructive py-1 pl-4 text-sm text-destructive"
              role="alert"
            >
              {error}
            </p>
          )}
        </section>

        {/* The ledger: three columns on tinted paper, hairlines between. */}
        <section className="mx-auto max-w-5xl px-4 pb-16 sm:px-6 lg:px-8">
          <div className="grid divide-y divide-border/70 border border-border/70 bg-muted/55 md:grid-cols-3 md:divide-x md:divide-y-0">
            {tiers.map((tier, index) => {
              const price = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly
              const perMonth = billingCycle === 'yearly' && tier.price_yearly > 0
                ? Math.round(tier.price_yearly / 12)
                : tier.price_monthly
              const isPopular = tier.id === 'pro'
              const isCurrent = tier.id === currentTier
              const positioning = TIER_POSITIONING[tier.id as Exclude<UsageTier, 'business'>]
              const stripePriceId =
                billingCycle === 'monthly'
                  ? tier.stripe_price_id_monthly
                  : tier.stripe_price_id_yearly
              const stripeAvailable = tier.id === 'free' || Boolean(stripePriceId)

              return (
                <div key={tier.id} className="flex flex-col p-6 sm:p-8">
                  <p className="label-mono">
                    {String(index + 1).padStart(2, '0')}
                    {positioning ? ` · ${positioning.audience}` : ''}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    {/* h2, not h3: the only heading above it is the page h1. */}
                    <h2 className="text-section-title">{tier.name}</h2>
                    {isCurrent ? (
                      <Badge variant="success">Current Plan</Badge>
                    ) : isPopular ? (
                      <Badge>Most Popular</Badge>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {tier.description || ''}
                  </p>

                  {/* Price in mono tabular; the period as a wall label. */}
                  <p className="mt-6 flex items-baseline gap-2">
                    <span className="text-section-title font-mono font-medium tabular-nums tracking-tight">
                      ${price === 0 ? '0' : perMonth}
                    </span>
                    <span className="label-mono">/ month</span>
                  </p>
                  {billingCycle === 'yearly' && price > 0 && (
                    <p className="label-mono mt-2">${price} billed annually</p>
                  )}

                  <p className="mt-6 text-sm leading-relaxed text-muted-foreground">
                    {positioning?.valueProp || ''}
                  </p>

                  {/* Limits as two hairline rows with tabular figures. */}
                  <dl className="mt-6 divide-y divide-border/70 border-y border-border/70 text-sm">
                    <div className="flex items-center justify-between gap-4 py-2.5">
                      <dt className="text-muted-foreground">Daily limit</dt>
                      <dd className="font-mono tabular-nums">
                        {tier.daily_limit === -1 ? 'Unlimited' : (tier.daily_limit ?? '—')}
                      </dd>
                    </div>
                    <div className="flex items-center justify-between gap-4 py-2.5">
                      <dt className="text-muted-foreground">Monthly limit</dt>
                      <dd className="font-mono tabular-nums">
                        {tier.monthly_limit === -1
                          ? 'Unlimited'
                          : typeof tier.monthly_limit === 'number'
                          ? formatNumber(tier.monthly_limit)
                          : typeof tier.generations_per_month === 'number'
                          ? formatNumber(tier.generations_per_month)
                          : '—'}
                      </dd>
                    </div>
                  </dl>

                  {/* While the plans are still the server-rendered ones we do
                      not know the Stripe price ids yet. Render the button shape
                      (disabled, "Loading…") rather than the "Contact Us" link,
                      so the CTA never flips between two different labels. */}
                  <div className="mt-8">
                    {loading || stripeAvailable ? (
                      <button
                        type="button"
                        onClick={() => !isCurrent && handleUpgrade(tier.id)}
                        disabled={loading || isCurrent || upgrading !== null}
                        className={getButtonClassName(tier.id)}
                      >
                        {getButtonText(tier.id)}
                      </button>
                    ) : (
                      <a href={`mailto:${SUPPORT_EMAIL}`} className={getButtonClassName(tier.id)}>
                        Contact Us
                      </a>
                    )}
                  </div>

                  <h3 className="label-mono mt-8">What’s Included</h3>
                  <ul className="mt-3 grow divide-y divide-border/70 border-y border-border/70">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3 py-3 text-sm">
                        <CheckIcon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        </section>

        <hr className="gallery-rule" />

        {/* Feature comparison: a hairline table, heads as wall labels. */}
        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <p className="label-mono">Compare</p>
          <h2 className="text-section-title mt-3">Feature Comparison</h2>

          <div className="mt-8 overflow-x-auto">
            <table className="w-full border-y border-border text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th scope="col" className="label-mono py-3 pr-8 text-left font-medium">
                    Feature
                  </th>
                  {tiers.map((tier) => (
                    <th
                      key={tier.id}
                      scope="col"
                      className="label-mono px-4 py-3 text-center font-medium"
                    >
                      {tier.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/70">
                {COMPARISON_ROWS.map((row) => (
                  <tr key={row.name}>
                    <th scope="row" className="py-3.5 pr-8 text-left font-normal text-foreground">
                      {row.name}
                    </th>
                    {tiers.map((tier) => {
                      const included = row[tier.id as Exclude<UsageTier, 'business'>] ?? false
                      return (
                        <td key={tier.id} className="px-4 py-3.5 text-center">
                          {included ? (
                            <>
                              <CheckIcon className="mx-auto size-4 text-primary" aria-hidden="true" />
                              <span className="sr-only">Included</span>
                            </>
                          ) : (
                            <>
                              <MinusIcon className="mx-auto size-4 text-muted-foreground" aria-hidden="true" />
                              <span className="sr-only">Not included</span>
                            </>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <hr className="gallery-rule" />

        {/* FAQ as a definition list on hairlines. */}
        <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <p className="label-mono">FAQ</p>
          <h2 className="text-section-title mt-3">Frequently Asked Questions</h2>
          <dl className="mt-8 divide-y divide-border border-y border-border">
            {FAQ.map((faq) => (
              <div key={faq.q} className="py-6">
                <dt>
                  <h3 className="text-subsection">{faq.q}</h3>
                </dt>
                <dd className="mt-2 leading-relaxed text-muted-foreground">{faq.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <hr className="gallery-rule" />

        {/* Final CTA: a wall label, a title, one primary button. */}
        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <div className="max-w-2xl">
            <p className="label-mono">Get started</p>
            <h2 className="text-section-title mt-3">Ready to Create Amazing Content?</h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground text-pretty">
              Start with our free plan and upgrade when you need more.
            </p>
            <Link href="/" className={buttonVariants({ size: 'lg', className: 'mt-8' })}>
              Start Creating for Free
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
