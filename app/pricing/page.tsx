'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowLeftIcon,
  CheckIcon,
  XMarkIcon,
  SparklesIcon,
  RocketLaunchIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline'
import { UsageTier, TierInfo, AllTiersResponse, TIER_DISPLAY } from '../../types/usage'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'

interface PricingTier {
  id: UsageTier
  name: string
  description: string
  price_monthly: number
  price_yearly: number
  daily_limit: number
  monthly_limit: number
  features: string[]
  notIncluded: string[]
  popular?: boolean
  icon: React.ElementType
}

const PRICING_TIERS: PricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Perfect for trying out Blog AI',
    price_monthly: 0,
    price_yearly: 0,
    daily_limit: 10,
    monthly_limit: 100,
    features: [
      '10 generations per day',
      '100 generations per month',
      'Blog post generation',
      'Basic AI tools',
      'Standard quality',
    ],
    notIncluded: [
      'Book generation',
      'Bulk generation',
      'Web research',
      'Priority support',
      'API access',
    ],
    icon: SparklesIcon,
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'For content creators and marketers',
    price_monthly: 29,
    price_yearly: 290,
    daily_limit: 100,
    monthly_limit: 2000,
    features: [
      '100 generations per day',
      '2,000 generations per month',
      'Blog post generation',
      'Book generation',
      'Bulk generation (up to 50)',
      'All AI tools',
      'Web research mode',
      'Priority support',
      'Higher quality outputs',
    ],
    notIncluded: [
      'API access',
      'Custom integrations',
      'Dedicated support',
    ],
    popular: true,
    icon: RocketLaunchIcon,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For teams and businesses',
    price_monthly: 99,
    price_yearly: 990,
    daily_limit: -1,
    monthly_limit: -1,
    features: [
      'Unlimited generations',
      'Everything in Pro',
      'Full API access',
      'Custom integrations',
      'Dedicated support',
      'Team collaboration',
      'Advanced analytics',
      'Custom models',
      'SLA guarantee',
    ],
    notIncluded: [],
    icon: BuildingOffice2Icon,
  },
]

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [currentTier, setCurrentTier] = useState<UsageTier | null>(null)
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState<UsageTier | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchCurrentTier()
  }, [])

  const fetchCurrentTier = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.usage.tiers, {
        headers: getDefaultHeaders(),
      })

      if (response.ok) {
        const data: AllTiersResponse = await response.json()
        setCurrentTier(data.current_tier)
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
      const response = await fetch(API_ENDPOINTS.usage.upgrade, {
        method: 'POST',
        headers: getDefaultHeaders(),
        body: JSON.stringify({ tier }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to upgrade')
      }

      const data = await response.json()
      setCurrentTier(tier)
      setSuccess(`Successfully upgraded to ${PRICING_TIERS.find((t) => t.id === tier)?.name}!`)
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
    if (tier === 'free' && currentTier !== 'free') return 'Downgrade'
    return tier === 'enterprise' ? 'Contact Sales' : 'Upgrade'
  }

  const getButtonStyle = (tier: UsageTier) => {
    if (tier === currentTier) {
      return 'bg-gray-100 text-gray-500 cursor-default'
    }
    if (tier === 'pro') {
      return 'bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white'
    }
    if (tier === 'enterprise') {
      return 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white'
    }
    return 'border border-gray-300 text-gray-700 hover:bg-gray-50'
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>Back to Generator</span>
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-indigo-600" />
              <span className="font-semibold text-gray-900">Blog AI</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="text-lg sm:text-xl text-indigo-100 max-w-2xl mx-auto mb-8">
              Choose the plan that fits your content creation needs.
              Upgrade or downgrade anytime.
            </p>

            {/* Billing toggle */}
            <div className="inline-flex items-center gap-4 bg-white/10 rounded-full p-1">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingCycle === 'monthly'
                    ? 'bg-white text-indigo-600'
                    : 'text-white hover:bg-white/10'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingCycle === 'yearly'
                    ? 'bg-white text-indigo-600'
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
          {PRICING_TIERS.map((tier, index) => {
            const Icon = tier.icon
            const price = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly
            const perMonth = billingCycle === 'yearly' && tier.price_yearly > 0
              ? Math.round(tier.price_yearly / 12)
              : tier.price_monthly

            return (
              <motion.div
                key={tier.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`relative bg-white rounded-2xl shadow-lg border-2 ${
                  tier.popular
                    ? 'border-indigo-500'
                    : tier.id === currentTier
                    ? 'border-green-500'
                    : 'border-gray-200'
                }`}
              >
                {/* Popular badge */}
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm font-medium px-4 py-1 rounded-full">
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
                      <p className="text-sm text-gray-500">{tier.description}</p>
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
                        {tier.daily_limit === -1 ? 'Unlimited' : tier.daily_limit}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-2">
                      <span className="text-gray-600">Monthly limit</span>
                      <span className="font-semibold text-gray-900">
                        {tier.monthly_limit === -1 ? 'Unlimited' : tier.monthly_limit.toLocaleString()}
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

                    {tier.notIncluded.length > 0 && (
                      <>
                        <h4 className="text-sm font-semibold text-gray-400 mt-6 mb-4">
                          Not included
                        </h4>
                        <ul className="space-y-3">
                          {tier.notIncluded.map((feature, i) => (
                            <li key={i} className="flex items-start gap-3">
                              <XMarkIcon className="w-5 h-5 text-gray-300 flex-shrink-0" />
                              <span className="text-sm text-gray-400">{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
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
                    {PRICING_TIERS.map((tier) => (
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
                    { name: 'Blog generation', free: true, pro: true, enterprise: true },
                    { name: 'Book generation', free: false, pro: true, enterprise: true },
                    { name: 'Bulk generation', free: false, pro: true, enterprise: true },
                    { name: 'Web research', free: false, pro: true, enterprise: true },
                    { name: 'All AI tools', free: false, pro: true, enterprise: true },
                    { name: 'API access', free: false, pro: false, enterprise: true },
                    { name: 'Custom integrations', free: false, pro: false, enterprise: true },
                    { name: 'Priority support', free: false, pro: true, enterprise: true },
                    { name: 'Dedicated support', free: false, pro: false, enterprise: true },
                    { name: 'Team collaboration', free: false, pro: false, enterprise: true },
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
                        {feature.pro ? (
                          <CheckIcon className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <XMarkIcon className="w-5 h-5 text-gray-300 mx-auto" />
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        {feature.enterprise ? (
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
                  a: 'We accept all major credit cards, including Visa, Mastercard, American Express, and Discover. For Enterprise plans, we also offer invoicing.',
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
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to create amazing content?</h2>
          <p className="text-indigo-100 mb-6">
            Start with our free plan and upgrade when you need more.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-6 py-3 bg-white text-indigo-600 font-medium rounded-lg hover:bg-indigo-50 transition-colors"
          >
            Start Creating for Free
          </Link>
        </div>
      </section>
    </main>
  )
}
