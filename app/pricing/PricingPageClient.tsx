'use client'

import { useEffect, useState, type ElementType } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@clerk/nextjs'
import { m } from 'framer-motion'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import {
  BuildingOffice2Icon,
  CheckIcon,
  PencilSquareIcon,
  RocketLaunchIcon,
  SparklesIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { TIER_DISPLAY, type UsageTier } from '../../types/usage'

type BillingCycle = 'monthly' | 'yearly'

interface PublicPricingTier {
  id: UsageTier
  name: string
  description?: string
  price_monthly: number
  price_yearly: number
  daily_limit?: number
  monthly_limit?: number
  generations_per_month?: number
  features: string[]
  stripe_price_id_monthly?: string
  stripe_price_id_yearly?: string
}

interface PricingPageState {
  currentTier: UsageTier | null
  tiers: PublicPricingTier[]
  loading: boolean
  upgrading: UsageTier | null
  error: string | null
  success: string | null
}

const TIER_ORDER: UsageTier[] = ['free', 'starter', 'pro', 'business']

const TIER_ICONS: Record<UsageTier, ElementType> = {
  free: SparklesIcon,
  starter: PencilSquareIcon,
  pro: RocketLaunchIcon,
  business: BuildingOffice2Icon,
}

const COMPARISON_FEATURES = [
  { name: 'Blog generation', free: true, starter: true, pro: true },
  { name: 'Book generation', free: false, starter: true, pro: true },
  { name: 'Export formats', free: false, starter: true, pro: true },
  { name: 'Research mode', free: false, starter: true, pro: true },
  { name: 'Bulk generation', free: false, starter: false, pro: true },
  { name: 'Brand voice training', free: false, starter: false, pro: true },
  { name: 'Priority support', free: false, starter: true, pro: true },
] as const

const FAQS = [
  {
    question: 'Can I upgrade or downgrade anytime?',
    answer:
      'Yes. Upgrades apply immediately, and downgrades take effect at the end of the current billing period.',
  },
  {
    question: 'What happens when I reach my limit?',
    answer:
      'Generation stops until the relevant daily or monthly limit resets for your plan.',
  },
  {
    question: 'Do unused generations roll over?',
    answer:
      'No. Limits reset on schedule rather than accumulating across billing periods.',
  },
  {
    question: 'Is there a free trial for Pro?',
    answer:
      'The Free plan functions as the trial experience. Upgrade whenever you need more volume or advanced features.',
  },
  {
    question: 'What payment methods do you accept?',
    answer:
      'All major credit cards are supported through the billing flow.',
  },
] as const

function sortTiers(a: PublicPricingTier, b: PublicPricingTier) {
  return TIER_ORDER.indexOf(a.id) - TIER_ORDER.indexOf(b.id)
}

function PricingHero({
  billingCycle,
  onBillingCycleChange,
}: {
  billingCycle: BillingCycle
  onBillingCycleChange: (cycle: BillingCycle) => void
}) {
  return (
    <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto mb-8">
            Choose the plan that fits your content creation needs. Upgrade or downgrade anytime.
          </p>

          <div className="inline-flex items-center gap-4 bg-white/10 rounded-full p-1">
            <button
              type="button"
              onClick={() => onBillingCycleChange('monthly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingCycle === 'monthly'
                  ? 'bg-white text-amber-600'
                  : 'text-white hover:bg-white/10'
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => onBillingCycleChange('yearly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingCycle === 'yearly'
                  ? 'bg-white text-amber-600'
                  : 'text-white hover:bg-white/10'
              }`}
            >
              Yearly
              <span className="ml-1 text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">
                Save 17%
              </span>
            </button>
          </div>
        </m.div>
      </div>
    </section>
  )
}

function PricingAlerts({
  success,
  error,
}: {
  success: string | null
  error: string | null
}) {
  return (
    <>
      {success ? (
        <m.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-xl text-center"
        >
          <p className="text-green-700 dark:text-green-400">{success}</p>
        </m.div>
      ) : null}
      {error ? (
        <m.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl text-center"
        >
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </m.div>
      ) : null}
    </>
  )
}

function PricingCards({
  tiers,
  billingCycle,
  currentTier,
  upgrading,
  loading,
  onUpgrade,
  getButtonText,
  getButtonStyle,
}: {
  tiers: PublicPricingTier[]
  billingCycle: BillingCycle
  currentTier: UsageTier | null
  upgrading: UsageTier | null
  loading: boolean
  onUpgrade: (tier: UsageTier) => void
  getButtonText: (tier: UsageTier) => string
  getButtonStyle: (tier: UsageTier) => string
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      {tiers.map((tier, index) => {
        const Icon = TIER_ICONS[tier.id]
        const price = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly
        const perMonth =
          billingCycle === 'yearly' && tier.price_yearly > 0
            ? Math.round(tier.price_yearly / 12)
            : tier.price_monthly
        const isPopular = tier.id === 'pro'

        return (
          <m.article
            key={tier.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={`relative bg-white dark:bg-gray-900 rounded-2xl shadow-lg border-2 ${
              isPopular
                ? 'border-amber-500'
                : tier.id === currentTier
                  ? 'border-green-500'
                  : 'border-gray-200 dark:border-gray-800'
            }`}
          >
            {isPopular ? (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="bg-gradient-to-r from-amber-500 to-amber-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                  Most Popular
                </span>
              </div>
            ) : null}

            {tier.id === currentTier ? (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="bg-green-500 text-white text-sm font-medium px-4 py-1 rounded-full">
                  Current Plan
                </span>
              </div>
            ) : null}

            <div className="p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${TIER_DISPLAY[tier.id].bgColor}`}>
                  <Icon className={`w-6 h-6 ${TIER_DISPLAY[tier.id].color}`} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{tier.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{tier.description || ''}</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                    ${price === 0 ? '0' : perMonth}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">/month</span>
                </div>
                {billingCycle === 'yearly' && price > 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    ${price} billed annually
                  </p>
                ) : null}
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6">
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

              <button
                type="button"
                onClick={() => tier.id !== currentTier && onUpgrade(tier.id)}
                disabled={tier.id === currentTier || upgrading !== null || loading}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${getButtonStyle(tier.id)} disabled:opacity-50`}
              >
                {getButtonText(tier.id)}
              </button>

              <div className="mt-8">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  What&apos;s included
                </h4>
                <ul className="space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </m.article>
        )
      })}
    </div>
  )
}

function FeatureComparisonSection({ tiers }: { tiers: PublicPricingTier[] }) {
  return (
    <section className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
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
                {COMPARISON_FEATURES.map((feature) => (
                  <tr key={feature.name} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="py-4 pr-8 text-sm text-gray-600 dark:text-gray-400">{feature.name}</td>
                    <td className="py-4 px-4 text-center">
                      {feature.free ? (
                        <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                      )}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {feature.starter ? (
                        <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                      )}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {feature.pro ? (
                        <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <XMarkIcon className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </m.div>
      </div>
    </section>
  )
}

function PricingFaqSection() {
  return (
    <section className="py-16">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            {FAQS.map((faq) => (
              <div key={faq.question} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {faq.question}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">{faq.answer}</p>
              </div>
            ))}
          </div>
        </m.div>
      </div>
    </section>
  )
}

function PricingFooterCta() {
  return (
    <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to create amazing content?</h2>
        <p className="text-amber-100 mb-6">
          Start with the free plan and upgrade when you need more.
        </p>
        <Link
          href="/"
          className="inline-flex items-center px-6 py-3 bg-white text-amber-600 font-medium rounded-lg hover:bg-amber-50 transition-colors"
        >
          Start Creating for Free
        </Link>
      </div>
    </section>
  )
}

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<BillingCycle>('monthly')
  const [state, setState] = useState<PricingPageState>({
    currentTier: null,
    tiers: [],
    loading: true,
    upgrading: null,
    error: null,
    success: null,
  })

  const router = useRouter()
  const { isSignedIn } = useAuth()

  const { currentTier, tiers, loading, upgrading, error, success } = state

  useEffect(() => {
    void fetchPricing()
    void fetchCurrentTier()

    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      const checkout = url.searchParams.get('checkout')

      if (checkout === 'success') {
        setState((current) => ({
          ...current,
          success: 'Subscription updated successfully.',
          error: null,
        }))
      }

      if (checkout === 'cancelled') {
        setState((current) => ({
          ...current,
          success: null,
          error: 'Checkout cancelled.',
        }))
      }
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
        const filtered = (data.tiers as PublicPricingTier[])
          .filter((tier) => tier.id !== 'business')
          .sort(sortTiers)

        setState((current) => ({
          ...current,
          tiers: filtered,
        }))
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
        if (data?.tier) {
          setState((current) => ({
            ...current,
            currentTier: data.tier,
          }))
        }
      }
    } catch (err) {
      console.error('Error fetching current tier:', err)
    } finally {
      setState((current) => ({
        ...current,
        loading: false,
      }))
    }
  }

  const handleUpgrade = async (tier: UsageTier) => {
    if (tier === currentTier) return

    setState((current) => ({
      ...current,
      upgrading: tier,
      error: null,
      success: null,
    }))

    try {
      if (!isSignedIn) {
        router.push('/sign-in?redirect_url=/pricing')
        return
      }

      const tierData = tiers.find((item) => item.id === tier)
      if (!tierData) {
        throw new Error('Unknown tier')
      }

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
      setState((current) => ({
        ...current,
        error: err instanceof Error ? err.message : 'Failed to upgrade. Please try again.',
      }))
    } finally {
      setState((current) => ({
        ...current,
        upgrading: null,
      }))
    }
  }

  const getButtonText = (tier: UsageTier) => {
    if (loading) return 'Loading...'
    if (upgrading === tier) return 'Processing...'
    if (tier === currentTier) return 'Current Plan'
    if (tier === 'free' && currentTier && currentTier !== 'free') return 'Manage in Portal'
    return tier === 'free' ? 'Get Started' : 'Checkout'
  }

  const getButtonStyle = (tier: UsageTier) => {
    if (tier === currentTier) {
      return 'bg-gray-100 dark:bg-gray-800 text-gray-500 cursor-default'
    }

    if (tier === 'starter' || tier === 'pro') {
      return 'bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white'
    }

    return 'border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      <SiteHeader />
      <PricingHero billingCycle={billingCycle} onBillingCycleChange={setBillingCycle} />

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 pb-16">
        <PricingAlerts success={success} error={error} />
        <PricingCards
          tiers={tiers}
          billingCycle={billingCycle}
          currentTier={currentTier}
          upgrading={upgrading}
          loading={loading}
          onUpgrade={handleUpgrade}
          getButtonText={getButtonText}
          getButtonStyle={getButtonStyle}
        />
      </section>

      <FeatureComparisonSection tiers={tiers} />
      <PricingFaqSection />
      <PricingFooterCta />
      <SiteFooter />
    </main>
  )
}
