'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@clerk/nextjs'
import { motion } from 'framer-motion'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
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

const TIER_ORDER: UsageTier[] = ['free', 'starter', 'pro', 'business']

const TIER_ICONS: Record<UsageTier, React.ElementType> = {
  free: SparklesIcon,
  starter: PencilSquareIcon,
  pro: RocketLaunchIcon,
  business: BuildingOffice2Icon,
}

function sortTiers(a: PublicPricingTier, b: PublicPricingTier) {
  return TIER_ORDER.indexOf(a.id) - TIER_ORDER.indexOf(b.id)
}

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<BillingCycle>('monthly')
  const [currentTier, setCurrentTier] = useState<UsageTier | null>(null)
  const [tiers, setTiers] = useState<PublicPricingTier[]>([])
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
        // We don’t sell the Business/Agency tier yet (no seats/invites/etc).
        const filtered = (data.tiers as PublicPricingTier[])
          .filter((t) => t.id !== 'business')
          .sort(sortTiers)
        setTiers(filtered)
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
    return tier === 'free' ? 'Get Started' : 'Checkout'
  }

  const getButtonStyle = (tier: UsageTier) => {
    if (tier === currentTier) {
      return 'bg-gray-100 text-gray-500 cursor-default'
    }
    if (tier === 'starter' || tier === 'pro') {
      return 'bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white'
    }
    return 'border border-gray-300 text-gray-700 hover:bg-gray-50'
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <SiteHeader />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto mb-8">
              Choose the plan that fits your content creation needs.
              Upgrade or downgrade anytime.
            </p>

            {/* Billing toggle */}
            <div className="inline-flex items-center gap-4 bg-white/10 rounded-full p-1">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingCycle === 'monthly'
                    ? 'bg-white text-amber-600'
                    : 'text-white hover:bg-white/10'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
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
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 pb-16">
        {/* Success/Error messages */}
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl text-center"
          >
            <p className="text-green-700">{success}</p>
          </motion.div>
        )}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-center"
          >
            <p className="text-red-700">{error}</p>
          </motion.div>
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
              <motion.div
                key={tier.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`relative bg-white rounded-2xl shadow-lg border-2 ${
                  isPopular
                    ? 'border-amber-500'
                    : tier.id === currentTier
                    ? 'border-green-500'
                    : 'border-gray-200'
                }`}
              >
                {/* Popular badge */}
                {isPopular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-amber-500 to-amber-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Current plan badge */}
                {tier.id === currentTier && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-green-500 text-white text-sm font-medium px-4 py-1 rounded-full">
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
                    <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                    <p className="text-sm text-gray-500">{tier.description || ''}</p>
                  </div>
                </div>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-gray-900">
                        ${price === 0 ? '0' : perMonth}
                      </span>
                      <span className="text-gray-500">/month</span>
                    </div>
                    {billingCycle === 'yearly' && price > 0 && (
                      <p className="text-sm text-gray-500 mt-1">
                        ${price} billed annually
                      </p>
                    )}
                  </div>

                  {/* Limits */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Daily limit</span>
                      <span className="font-semibold text-gray-900">
                        {tier.daily_limit === -1 ? 'Unlimited' : (tier.daily_limit ?? '—')}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-2">
                      <span className="text-gray-600">Monthly limit</span>
                      <span className="font-semibold text-gray-900">
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
                  <button
                    onClick={() => tier.id !== currentTier && handleUpgrade(tier.id)}
                    disabled={tier.id === currentTier || upgrading !== null}
                    className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${getButtonStyle(tier.id)} disabled:opacity-50`}
                  >
                    {getButtonText(tier.id)}
                  </button>

                  {/* Features */}
                  <div className="mt-8">
                    <h4 className="text-sm font-semibold text-gray-900 mb-4">
                      What&apos;s included
                    </h4>
                    <ul className="space-y-3">
                      {tier.features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                          <span className="text-sm text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="bg-white border-t border-gray-200 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-12">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-4 pr-8 text-sm font-semibold text-gray-900">
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
                  ].map((feature, i) => (
                    <tr key={i} className="border-b border-gray-100">
                      <td className="py-4 pr-8 text-sm text-gray-600">{feature.name}</td>
                      <td className="py-4 px-4 text-center">
                        {feature.free ? (
                          <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 mx-auto" />
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.starter ? (
                          <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 mx-auto" />
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.pro ? (
                          <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-12">
              Frequently Asked Questions
            </h2>

            <div className="space-y-6">
              {[
                {
                  q: 'Can I upgrade or downgrade anytime?',
                  a: 'Yes, you can change your plan at any time. When upgrading, you will get immediate access to the new features. When downgrading, the change will take effect at the end of your current billing period.',
                },
                {
                  q: 'What happens when I reach my limit?',
                  a: 'When you reach your daily or monthly limit, you will not be able to generate new content until the limit resets. Daily limits reset at midnight UTC, and monthly limits reset on the first of each month.',
                },
                {
                  q: 'Do unused generations roll over?',
                  a: 'No, unused generations do not roll over to the next period. Each day and month starts with a fresh limit based on your plan.',
                },
                {
                  q: 'Is there a free trial for Pro?',
                  a: 'The Free plan allows you to try out Blog AI with limited features. If you need more generations or access to premium features, you can upgrade to Pro at any time.',
                },
                {
                  q: 'What payment methods do you accept?',
                  a: 'We accept all major credit cards, including Visa, Mastercard, American Express, and Discover.',
                },
              ].map((faq, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.q}</h3>
                  <p className="text-gray-600">{faq.a}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to create amazing content?</h2>
          <p className="text-amber-100 mb-6">
            Start with our free plan and upgrade when you need more.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-6 py-3 bg-white text-amber-600 font-medium rounded-lg hover:bg-amber-50 transition-colors"
          >
            Start Creating for Free
          </Link>
        </div>
      </section>

      <SiteFooter />
    </main>
  )
}
