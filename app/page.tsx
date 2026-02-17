'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { motion, useInView } from 'framer-motion'
import { SignedIn, SignedOut } from '@clerk/nextjs'
import SiteHeader from '../components/SiteHeader'
import SiteFooter from '../components/SiteFooter'
import {
  SparklesIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  ArrowRightIcon,
  CheckIcon,
  UserGroupIcon,
  PencilSquareIcon,
  RocketLaunchIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline'

// ---------------------------------------------------------------------------
// Animation helpers
// ---------------------------------------------------------------------------

const FADE_UP = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
}

const FADE_IN = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

const STAGGER_CONTAINER = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
}

interface RevealSectionProps {
  children: React.ReactNode
  className?: string
}

function RevealSection({ children, className = '' }: RevealSectionProps) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={FADE_UP}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

interface Feature {
  icon: React.ElementType
  title: string
  description: string
}

const FEATURES: Feature[] = [
  {
    icon: SparklesIcon,
    title: 'Brand Voice Training',
    description:
      'Feed in your existing content and define your tone, vocabulary, and style. Every piece of generated content sounds authentically like you -- not like a chatbot.',
  },
  {
    icon: DocumentTextIcon,
    title: 'Blog and Book Generation',
    description:
      'Go from topic to a structured, publish-ready blog post or full-length book draft in minutes. Section outlines, FAQs, and chapters are all handled automatically.',
  },
  {
    icon: MagnifyingGlassIcon,
    title: 'SEO-Optimized Content',
    description:
      'Built-in keyword targeting, meta descriptions, heading structure, and readability scoring. Your content is ready to rank from the moment it is generated.',
  },
  {
    icon: CpuChipIcon,
    title: 'Multi-Provider AI',
    description:
      'Choose from GPT-4, Claude, or Gemini for every generation. Switch providers freely or let Blog AI pick the best model for the task at hand.',
  },
]

interface Step {
  number: string
  title: string
  description: string
  icon: React.ElementType
}

const STEPS: Step[] = [
  {
    number: '01',
    title: 'Train Your Voice',
    description:
      'Create a brand profile with your tone, vocabulary, and example content. The AI learns what makes your writing yours.',
    icon: PencilSquareIcon,
  },
  {
    number: '02',
    title: 'Generate Content',
    description:
      'Pick a topic, add keywords, and hit generate. Get structured blog posts, books, or marketing copy in minutes.',
    icon: RocketLaunchIcon,
  },
  {
    number: '03',
    title: 'Publish Everywhere',
    description:
      'Export to WordPress, GitHub, or Medium. Your content is formatted, optimized, and ready to go live.',
    icon: GlobeAltIcon,
  },
]

interface PricingTier {
  name: string
  price: string
  period: string
  description: string
  features: string[]
  cta: string
  href: string
  highlighted: boolean
}

const PRICING_TIERS: PricingTier[] = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    description: 'For individuals getting started with AI content.',
    features: [
      'Blog post generation',
      'Basic SEO optimization',
      '5 generations per day',
      'Community support',
    ],
    cta: 'Start Free',
    href: '/sign-up',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    description: 'For creators and marketers who publish regularly.',
    features: [
      'Everything in Free',
      'Book generation',
      'Brand voice training',
      'Bulk generation',
      'Research mode',
      'Export to WordPress and Medium',
      'Priority support',
    ],
    cta: 'Start Pro Trial',
    href: '/pricing',
    highlighted: true,
  },
  {
    name: 'Business',
    price: '$99',
    period: '/month',
    description: 'For teams and agencies managing multiple brands.',
    features: [
      'Everything in Pro',
      'Unlimited generations',
      'Multiple brand profiles',
      'Team collaboration',
      'API access',
      'Dedicated account manager',
    ],
    cta: 'Contact Sales',
    href: '/pricing',
    highlighted: false,
  },
]

interface Stat {
  value: string
  label: string
}

const SOCIAL_STATS: Stat[] = [
  { value: '12,000+', label: 'articles generated' },
  { value: '2,400+', label: 'active creators' },
  { value: '98%', label: 'satisfaction rate' },
  { value: '3', label: 'AI providers supported' },
]

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Home(): React.ReactElement {
  const isClerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <main className="min-h-screen">
      <SiteHeader />

      {/* ----------------------------------------------------------------- */}
      {/* Hero Section                                                      */}
      {/* ----------------------------------------------------------------- */}
      <section className="relative overflow-hidden">
        {/* Subtle background gradient orbs */}
        <div
          className="pointer-events-none absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, rgb(217 119 6) 0%, transparent 70%)' }}
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute -bottom-60 -left-40 h-[500px] w-[500px] rounded-full opacity-[0.05]"
          style={{ background: 'radial-gradient(circle, rgb(217 119 6) 0%, transparent 70%)' }}
          aria-hidden="true"
        />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28 lg:py-36">
          <div className="max-w-3xl mx-auto text-center">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={STAGGER_CONTAINER}
            >
              {/* Badge */}
              <motion.div variants={FADE_UP} transition={{ duration: 0.5 }}>
                <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-100/70 text-amber-800 text-xs font-medium tracking-wide">
                  <SparklesIcon className="w-3.5 h-3.5" aria-hidden="true" />
                  Now with Brand Voice Training
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1
                variants={FADE_UP}
                transition={{ duration: 0.5 }}
                className="mt-6 text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-gray-900 font-serif leading-[1.1]"
              >
                AI-Powered Content That{' '}
                <span className="text-amber-600">Sounds Like You</span>
              </motion.h1>

              {/* Subheading */}
              <motion.p
                variants={FADE_UP}
                transition={{ duration: 0.5 }}
                className="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed"
              >
                Train the AI on your brand voice, generate blog posts and books in minutes,
                and publish SEO-optimized content that your audience actually wants to read.
              </motion.p>

              {/* CTAs */}
              <motion.div
                variants={FADE_UP}
                transition={{ duration: 0.5 }}
                className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
              >
                {isClerkConfigured ? (
                  <>
                    <SignedOut>
                      <Link
                        href="/sign-up"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors shadow-sm shadow-amber-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Start Creating for Free
                        <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                      </Link>
                      <Link
                        href="/tools"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Explore Tools
                      </Link>
                    </SignedOut>
                    <SignedIn>
                      <Link
                        href="/tools"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors shadow-sm shadow-amber-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Go to Dashboard
                        <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                      </Link>
                      <Link
                        href="/brand"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Train Your Voice
                      </Link>
                    </SignedIn>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors shadow-sm shadow-amber-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                    >
                      Start Creating for Free
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                    <Link
                      href="/tools"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                    >
                      Explore Tools
                    </Link>
                  </>
                )}
              </motion.div>

              {/* Trust indicator */}
              <motion.p
                variants={FADE_IN}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="mt-6 text-sm text-gray-400"
              >
                No credit card required. Free plan available.
              </motion.p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* Social Proof Bar                                                  */}
      {/* ----------------------------------------------------------------- */}
      <section className="border-y border-amber-100/60 bg-white/60 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <RevealSection>
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 text-sm font-medium text-gray-500">
                <UserGroupIcon className="w-5 h-5 text-amber-500" aria-hidden="true" />
                Trusted by creators, marketers, and agencies worldwide
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
              {SOCIAL_STATS.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-2xl sm:text-3xl font-semibold text-gray-900">
                    {stat.value}
                  </div>
                  <div className="mt-1 text-sm text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* Feature Grid                                                      */}
      {/* ----------------------------------------------------------------- */}
      <section className="py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <RevealSection className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 font-serif">
              Everything you need to create content at scale
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              From brand voice training to multi-platform publishing, Blog AI handles
              the entire content pipeline.
            </p>
          </RevealSection>

          <FeatureGrid />
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* How It Works                                                      */}
      {/* ----------------------------------------------------------------- */}
      <section className="py-20 sm:py-28 bg-white/70 border-y border-amber-100/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <RevealSection className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 font-serif">
              Three steps to content that converts
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Stop spending hours writing from scratch. Train your voice once, then generate
              and publish endlessly.
            </p>
          </RevealSection>

          <StepsSection />
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* Pricing Preview                                                   */}
      {/* ----------------------------------------------------------------- */}
      <section className="py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <RevealSection className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 font-serif">
              Plans that grow with you
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Start free and upgrade as your content needs expand. Every plan includes
              core AI generation features.
            </p>
          </RevealSection>

          <PricingGrid />

          <RevealSection className="text-center mt-10">
            <Link
              href="/pricing"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 hover:text-amber-700 transition-colors"
            >
              Compare all features in detail
              <ArrowRightIcon className="w-3.5 h-3.5" aria-hidden="true" />
            </Link>
          </RevealSection>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* Final CTA                                                         */}
      {/* ----------------------------------------------------------------- */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-24 text-center">
          <RevealSection>
            <h2 className="text-3xl sm:text-4xl font-semibold text-white font-serif">
              Your content engine starts here
            </h2>
            <p className="mt-4 text-lg text-amber-100 max-w-xl mx-auto">
              Join thousands of creators who write faster, rank higher, and stay on-brand
              with Blog AI.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              {isClerkConfigured ? (
                <>
                  <SignedOut>
                    <Link
                      href="/sign-up"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                    >
                      Start Creating for Free
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                  </SignedOut>
                  <SignedIn>
                    <Link
                      href="/tools"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                    >
                      Go to Dashboard
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                  </SignedIn>
                </>
              ) : (
                <Link
                  href="/auth"
                  className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                >
                  Start Creating for Free
                  <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                </Link>
              )}
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white border border-white/30 hover:bg-white/10 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
              >
                View Pricing
              </Link>
            </div>
          </RevealSection>
        </div>
      </section>

      <SiteFooter />
    </main>
  )
}

// ---------------------------------------------------------------------------
// Section Components
// ---------------------------------------------------------------------------

function FeatureGrid(): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={STAGGER_CONTAINER}
      className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8"
    >
      {FEATURES.map((feature) => {
        const Icon = feature.icon
        return (
          <motion.div
            key={feature.title}
            variants={FADE_UP}
            transition={{ duration: 0.5 }}
            className="glass-card rounded-2xl p-8 hover:shadow-lg transition-shadow"
          >
            <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 text-amber-700 mb-5">
              <Icon className="w-5 h-5" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {feature.title}
            </h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              {feature.description}
            </p>
          </motion.div>
        )
      })}
    </motion.div>
  )
}

function StepsSection(): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={STAGGER_CONTAINER}
      className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12"
    >
      {STEPS.map((step, index) => {
        const Icon = step.icon
        return (
          <motion.div
            key={step.number}
            variants={FADE_UP}
            transition={{ duration: 0.5 }}
            className="relative text-center"
          >
            {/* Connector line between steps on desktop */}
            {index < STEPS.length - 1 && (
              <div
                className="hidden md:block absolute top-10 left-[calc(50%+32px)] w-[calc(100%-64px)] h-px bg-amber-200"
                aria-hidden="true"
              />
            )}

            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-amber-50 border border-amber-100 mb-6">
              <Icon className="w-8 h-8 text-amber-600" aria-hidden="true" />
            </div>
            <div className="text-xs font-medium text-amber-600 uppercase tracking-wider mb-2">
              Step {step.number}
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              {step.title}
            </h3>
            <p className="text-sm text-gray-600 leading-relaxed max-w-xs mx-auto">
              {step.description}
            </p>
          </motion.div>
        )
      })}
    </motion.div>
  )
}

function PricingGrid(): React.ReactElement {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={STAGGER_CONTAINER}
      className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
    >
      {PRICING_TIERS.map((tier) => (
        <motion.div
          key={tier.name}
          variants={FADE_UP}
          transition={{ duration: 0.5 }}
          className={`relative rounded-2xl p-8 transition-shadow ${
            tier.highlighted
              ? 'bg-white border-2 border-amber-500 shadow-lg shadow-amber-500/10'
              : 'glass-card'
          }`}
        >
          {tier.highlighted && (
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span className="inline-flex items-center px-3.5 py-1 bg-amber-600 text-white text-xs font-medium rounded-full">
                Most Popular
              </span>
            </div>
          )}

          <h3 className="text-lg font-semibold text-gray-900">{tier.name}</h3>
          <p className="mt-1 text-sm text-gray-500">{tier.description}</p>

          <div className="mt-6 flex items-baseline gap-1">
            <span className="text-4xl font-semibold text-gray-900">
              {tier.price}
            </span>
            <span className="text-sm text-gray-500">{tier.period}</span>
          </div>

          <Link
            href={tier.href}
            className={`mt-6 block w-full py-3 px-4 text-center text-sm font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 ${
              tier.highlighted
                ? 'bg-amber-600 text-white hover:bg-amber-700'
                : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
            }`}
          >
            {tier.cta}
          </Link>

          <ul className="mt-8 space-y-3" role="list">
            {tier.features.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-gray-600">
                <CheckIcon
                  className="w-5 h-5 text-amber-500 flex-shrink-0 mt-px"
                  aria-hidden="true"
                />
                {feature}
              </li>
            ))}
          </ul>
        </motion.div>
      ))}
    </motion.div>
  )
}
