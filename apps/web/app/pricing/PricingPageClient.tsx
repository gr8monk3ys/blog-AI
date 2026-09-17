'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { Reveal } from '../_home/Reveal'
import { useAuth } from '../../lib/clerk-ui'
import {
  CheckIcon,
  XMarkIcon,
  SparklesIcon,
  RocketLaunchIcon,
  BuildingOffice2Icon,
  PencilSquareIcon,
} from '@heroicons/react/24/outline'
import { UsageTier, TIER_DISPLAY } from '../../types/usage'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { normalizePricingTiers, type PublicPricingTier } from './tiers'

type BillingCycle = 'monthly' | 'yearly'

// Entrance motion is CSS (see "Entrance motion" in app/globals.css).
// This page used framer-motion, and framer serialises its `initial` state into
// the server HTML: the hero subhead — this route's LCP element — shipped as
// `opacity: 0` and stayed invisible until the whole page had hydrated, which is
// the entire 4.48 s of "element render delay" behind a 4.7 s mobile LCP. The
// hero now rises with a transform-only keyframe so it is painted in the first
// frame; sections below the fold use the same <Reveal> as the home page.
const CARD_STAGGER = ['', '[animation-delay:120ms]', '[animation-delay:240ms]']

const TIER_ICONS: Record<UsageTier, React.ElementType> = {
  free: SparklesIcon,
  starter: PencilSquareIcon,
  pro: RocketLaunchIcon,
  business: BuildingOffice2Icon,
}

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

interface PricingPageClientProps {
  /**
   * Plans resolved on the server (see ./tiers). They are rendered in the
   * document, so the card grid never grows after hydration.
   */
  initialTiers: PublicPricingTier[]
}

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
    if (loading) return 'Loading...'
    if (upgrading === tier) return 'Processing...'
    if (tier === currentTier) return 'Current Plan'
    if (tier === 'free' && currentTier && currentTier !== 'free') return 'Manage in Portal'
    return TIER_POSITIONING[tier as Exclude<UsageTier, 'business'>]?.cta || 'Checkout'
  }

  const getButtonStyle = (tier: UsageTier) => {
    if (tier === currentTier) {
      // gray-500 was 4.39:1 on gray-100 and 3.04:1 on gray-800 — under AA in
      // both themes. Now 6.87:1 and 5.78:1.
      return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-default'
    }
    if (tier === 'starter' || tier === 'pro') {
      return 'bg-gradient-to-r from-amber-700 to-amber-800 hover:from-amber-800 hover:to-amber-900 text-white'
    }
    return 'border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
  }

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-700 to-amber-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* hero-rise-lcp moves without ever being transparent: Chrome does not
              count an opacity:0 element as painted, and the <p> below is this
              route's LCP element. */}
          <div className="hero-rise-lcp">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Pricing For Brand-Safe Content Production
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto mb-8">
              Pick the plan that matches your publishing volume and workflow maturity.
              Start free, move to Starter when you publish regularly, and upgrade to Pro when
              the team needs brand controls and bulk production.
            </p>

            {/* Billing toggle */}
            <div className="inline-flex items-center gap-4 bg-white/10 rounded-full p-1">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingCycle === 'monthly'
                    ? 'bg-white text-amber-700'
                    : 'text-white hover:bg-white/10'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingCycle === 'yearly'
                    ? 'bg-white text-amber-700'
                    : 'text-white hover:bg-white/10'
                }`}
              >
                Yearly
                <span className="ml-1 text-xs bg-emerald-700 text-white px-2 py-0.5 rounded-full">
                  Save 17%
                </span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 pb-16">
        {/* Success/Error messages */}
        {success && (
          <div className="hero-fade mb-6 p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-xl text-center">
            <p className="text-emerald-700 dark:text-emerald-400">{success}</p>
          </div>
        )}
        {error && (
          <div className="hero-fade mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl text-center">
            <p className="text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {tiers.map((tier, index) => {
            const Icon = TIER_ICONS[tier.id]
            const price = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly
            const perMonth = billingCycle === 'yearly' && tier.price_yearly > 0
              ? Math.round(tier.price_yearly / 12)
              : tier.price_monthly
            const isPopular = tier.id === 'pro'

            return (
              <div
                key={tier.id}
                className={`hero-rise ${CARD_STAGGER[index] ?? ''} relative bg-white dark:bg-gray-900 rounded-2xl shadow-lg border-2 ${
                  isPopular
                    ? 'border-amber-500'
                    : tier.id === currentTier
                    ? 'border-emerald-500'
                    : 'border-gray-200 dark:border-gray-800'
                }`}
              >
                {/* Popular badge */}
                {isPopular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    {/* amber-500/600 put white text at 2.15:1 / 3.19:1; the
                        700/800 pair used by every other amber CTA on this page
                        is 5.02:1 / 7.09:1. axe cannot score text over a
                        gradient, so nothing ever flagged this one. */}
                    <span className="bg-gradient-to-r from-amber-700 to-amber-800 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Current plan badge */}
                {tier.id === currentTier && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-emerald-700 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Current Plan
                    </span>
                  </div>
                )}

                <div className="p-8">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg ${TIER_DISPLAY[tier.id].bgColor}`}>
                      <Icon className={`w-6 h-6 ${TIER_DISPLAY[tier.id].color}`} />
                    </div>
                  <div>
                    {/* h2, not h3: the only heading above it is the hero h1,
                        so an h3 here skipped a level (axe heading-order). */}
                    <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">{tier.name}</h2>
                    <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
                      {TIER_POSITIONING[tier.id as Exclude<UsageTier, 'business'>]?.audience || ''}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{tier.description || ''}</p>
                  </div>
                </div>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                        ${price === 0 ? '0' : perMonth}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">/month</span>
                    </div>
                    {billingCycle === 'yearly' && price > 0 && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        ${price} billed annually
                      </p>
                    )}
                  </div>

                  {/* Limits */}
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                      {TIER_POSITIONING[tier.id as Exclude<UsageTier, 'business'>]?.valueProp || ''}
                    </p>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Daily limit</span>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {tier.daily_limit === -1 ? 'Unlimited' : (tier.daily_limit ?? '—')}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-2">
                      <span className="text-gray-600 dark:text-gray-400">Monthly limit</span>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {tier.monthly_limit === -1
                          ? 'Unlimited'
                          : typeof tier.monthly_limit === 'number'
                          ? tier.monthly_limit.toLocaleString()
                          : typeof tier.generations_per_month === 'number'
                          ? tier.generations_per_month.toLocaleString()
                          : '—'}
                      </span>
                    </div>
                  </div>

                  {/* CTA Button */}
                  {(() => {
                    const stripePriceId =
                      billingCycle === 'monthly'
                        ? tier.stripe_price_id_monthly
                        : tier.stripe_price_id_yearly
                    const stripeAvailable = tier.id === 'free' || Boolean(stripePriceId)
                    // While the plans are still the server-rendered ones we do
                    // not know the Stripe price ids yet. Render the button shape
                    // (disabled, "Loading...") rather than the "Contact Us" link,
                    // so the CTA never flips between two different labels.
                    if (loading || stripeAvailable) {
                      return (
                        <button
                          onClick={() => tier.id !== currentTier && handleUpgrade(tier.id)}
                          disabled={loading || tier.id === currentTier || upgrading !== null}
                          className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${getButtonStyle(tier.id)} disabled:opacity-50`}
                        >
                          {getButtonText(tier.id)}
                        </button>
                      )
                    }
                    return (
                      <a
                        href="mailto:support@blogai.com"
                        className={`w-full py-3 px-4 rounded-lg font-medium transition-all text-center block ${getButtonStyle(tier.id)}`}
                      >
                        Contact Us
                      </a>
                    )
                  })()}

                  {/* Features */}
                  <div className="mt-8">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      What&apos;s included
                    </h3>
                    <ul className="space-y-3">
                      {tier.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3">
                          <CheckIcon className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                          <span className="text-sm text-gray-600 dark:text-gray-400">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Reveal>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center mb-12">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800">
                    <th className="text-left py-4 pr-8 text-sm font-semibold text-gray-900 dark:text-gray-100">
                      Feature
                    </th>
                    {tiers.map((tier) => (
                      <th
                        key={tier.id}
                        className={`text-center py-4 px-4 text-sm font-semibold ${TIER_DISPLAY[tier.id].color}`}
                      >
                        {tier.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'Blog generation', free: true, starter: true, pro: true },
                    { name: 'Book generation', free: false, starter: true, pro: true },
                    { name: 'Export formats', free: false, starter: true, pro: true },
                    { name: 'Research mode', free: false, starter: true, pro: true },
                    { name: 'Bulk generation', free: false, starter: false, pro: true },
                    { name: 'Brand voice training', free: false, starter: false, pro: true },
                    { name: 'Priority support', free: false, starter: true, pro: true },
                  ].map((feature) => (
                    <tr key={feature.name} className="border-b border-gray-100 dark:border-gray-800">
                      <td className="py-4 pr-8 text-sm text-gray-600 dark:text-gray-400">{feature.name}</td>
                      <td className="py-4 px-4 text-center">
                        {feature.free ? (
                          <CheckIcon className="w-5 h-5 text-emerald-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.starter ? (
                          <CheckIcon className="w-5 h-5 text-emerald-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.pro ? (
                          <CheckIcon className="w-5 h-5 text-emerald-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Reveal>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <Reveal>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center mb-12">
              Frequently Asked Questions
            </h2>

            <div className="space-y-6">
              {[
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
              ].map((faq) => (
                <div key={faq.q} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{faq.q}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{faq.a}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="bg-gradient-to-r from-amber-700 to-amber-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to create amazing content?</h2>
          <p className="text-amber-100 mb-6">
            Start with our free plan and upgrade when you need more.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-6 py-3 bg-white text-amber-700 font-medium rounded-lg hover:bg-amber-50 transition-colors"
          >
            Start Creating for Free
          </Link>
        </div>
      </section>

      </main>
      <SiteFooter />
    </>
  )
}
