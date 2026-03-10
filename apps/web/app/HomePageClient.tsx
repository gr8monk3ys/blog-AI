'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { motion, useInView } from 'framer-motion'
import SiteHeader from '../components/SiteHeader'
import SiteFooter from '../components/SiteFooter'
import { SignedIn, SignedOut } from '../lib/clerk-ui'
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
      'Turn your best writing into reusable guidance for every draft. Keep tone, vocabulary, and positioning consistent across blogs, landing pages, and campaign copy.',
  },
  {
    icon: DocumentTextIcon,
    title: 'SEO Content Production',
    description:
      'Generate structured blog posts, landing page copy, and campaign assets with built-in outlines, keyword targeting, and publish-ready formatting.',
  },
  {
    icon: MagnifyingGlassIcon,
    title: 'Bulk Campaign Workflows',
    description:
      'Queue up multiple topics, estimate cost before you run, and produce batches of content for publishing calendars without managing prompts one by one.',
  },
  {
    icon: CpuChipIcon,
    title: 'Provider Flexibility',
    description:
      'Run the same workflow on OpenAI, Anthropic, or Gemini. Choose for quality, speed, or cost depending on the job.',
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
    title: 'Capture Your Brand Voice',
    description:
      'Save your tone, vocabulary, audience, and sample copy so every output starts from your positioning instead of a blank prompt.',
    icon: PencilSquareIcon,
  },
  {
    number: '02',
    title: 'Run A Repeatable Workflow',
    description:
      'Choose a content workflow, add topics and keywords, and generate SEO-ready drafts in bulk when needed.',
    icon: RocketLaunchIcon,
  },
  {
    number: '03',
    title: 'Review And Publish Faster',
    description:
      'Export, edit, and publish with less rewriting because the content already matches your structure, angle, and voice.',
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
    description: 'For testing the core workflow before you commit.',
    features: [
      '5 generations per month',
      'Basic blog generation',
      'Starter SEO workflow access',
      'Standard support',
    ],
    cta: 'Start Free',
    href: '/sign-up',
    highlighted: false,
  },
  {
    name: 'Starter',
    price: '$19',
    period: '/month',
    description: 'For solo operators publishing on a real schedule.',
    features: [
      'Everything in Free',
      '50 generations per month',
      'Book generation',
      'Research mode',
      'Priority support',
    ],
    cta: 'Choose Starter',
    href: '/pricing',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$49',
    period: '/month',
    description: 'For lean marketing teams running brand-safe content ops.',
    features: [
      'Everything in Starter',
      '200 generations per month',
      'Brand voice training',
      'Bulk generation',
      'All content types',
      'Priority support',
    ],
    cta: 'Choose Pro',
    href: '/pricing',
    highlighted: true,
  },
]

interface Stat {
  value: string
  label: string
}

const SOCIAL_STATS: Stat[] = [
  { value: '29+', label: 'content workflows and tools' },
  { value: '3', label: 'AI providers supported' },
  { value: 'bulk', label: 'campaign-ready generation mode' },
  { value: 'brand', label: 'voice-first content system' },
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
                <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-100/70 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 text-xs font-medium tracking-wide">
                  <SparklesIcon className="w-3.5 h-3.5" aria-hidden="true" />
                  Now with Brand Voice Training
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1
                variants={FADE_UP}
                transition={{ duration: 0.5 }}
                className="mt-6 text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-gray-900 dark:text-gray-100 font-serif leading-[1.1]"
              >
                Brand-Consistent AI Content For{' '}
                <span className="text-amber-600">Lean Marketing Teams</span>
              </motion.h1>

              {/* Subheading */}
              <motion.p
                variants={FADE_UP}
                transition={{ duration: 0.5 }}
                className="mt-6 text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed"
              >
                Train your voice once, run repeatable SEO content workflows, and generate
                publish-ready drafts faster without sounding generic.
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
                        Start Free
                        <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                      </Link>
                      <Link
                        href="/pricing"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        View Plans
                      </Link>
                    </SignedOut>
                    <SignedIn>
                      <Link
                        href="/bulk"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors shadow-sm shadow-amber-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Run Bulk Workflow
                        <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                      </Link>
                      <Link
                        href="/brand"
                        className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                      >
                        Open Brand Voice
                      </Link>
                    </SignedIn>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors shadow-sm shadow-amber-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                    >
                      Start Free
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                    <Link
                      href="/pricing"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
                    >
                      View Plans
                    </Link>
                  </>
                )}
              </motion.div>

              {/* Trust indicator */}
              <motion.p
                variants={FADE_IN}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="mt-6 text-sm text-gray-400 dark:text-gray-500"
              >
                No credit card required. Start free, then upgrade when you need bulk and brand controls.
              </motion.p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* Social Proof Bar                                                  */}
      {/* ----------------------------------------------------------------- */}
      <section className="border-y border-amber-100/60 dark:border-gray-800 bg-white/60 dark:bg-gray-900/60 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <RevealSection>
            <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
                  <UserGroupIcon className="w-5 h-5 text-amber-500" aria-hidden="true" />
                Best fit for founders, consultants, and lean marketing teams
                </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
              {SOCIAL_STATS.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-2xl sm:text-3xl font-semibold text-gray-900 dark:text-gray-100">
                    {stat.value}
                  </div>
                  <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">{stat.label}</div>
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
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
              The core system for repeatable content production
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Focus on the workflows that actually drive upgrades: brand voice,
              SEO drafting, bulk generation, and flexible model routing.
            </p>
          </RevealSection>

          <FeatureGrid />
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* How It Works                                                      */}
      {/* ----------------------------------------------------------------- */}
      <section className="py-20 sm:py-28 bg-white/70 dark:bg-gray-900/70 border-y border-amber-100/60 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <RevealSection className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
              Three steps to a content engine your team can reuse
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Stop restarting from prompts and pasting between tools. Save your standards,
              run the workflow, and publish with less cleanup.
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
            <h2 className="text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
              Plans that grow with you
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Start with the core workflow, then move up when you need more volume,
              research depth, brand controls, and bulk production.
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
              Build a workflow your team will actually reuse
            </h2>
            <p className="mt-4 text-lg text-amber-100 max-w-xl mx-auto">
              Use Blog AI when prompt-by-prompt writing stops scaling and you need
              faster, more consistent SEO content production.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              {isClerkConfigured ? (
                <>
                  <SignedOut>
                    <Link
                      href="/sign-up"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                    >
                      Start Free
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                  </SignedOut>
                  <SignedIn>
                    <Link
                      href="/bulk"
                      className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                    >
                      Run Bulk Workflow
                      <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                    </Link>
                  </SignedIn>
                </>
              ) : (
                <Link
                  href="/auth"
                  className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-amber-700 bg-white hover:bg-amber-50 rounded-lg transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
                >
                  Start Free
                  <ArrowRightIcon className="w-4 h-4" aria-hidden="true" />
                </Link>
              )}
              <Link
                href="/brand"
                className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-medium text-white border border-white/30 hover:bg-white/10 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-amber-600"
              >
                See Brand Voice
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
            <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700 mb-5">
              <Icon className="w-5 h-5" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {feature.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
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
                className="hidden md:block absolute top-10 left-[calc(50%+32px)] w-[calc(100%-64px)] h-px bg-amber-200 dark:bg-amber-800"
                aria-hidden="true"
              />
            )}

            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-amber-50 dark:bg-amber-950/50 border border-amber-100 dark:border-amber-800 mb-6">
              <Icon className="w-8 h-8 text-amber-600" aria-hidden="true" />
            </div>
            <div className="text-xs font-medium text-amber-600 uppercase tracking-wider mb-2">
              Step {step.number}
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
              {step.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed max-w-xs mx-auto">
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
              ? 'bg-white dark:bg-gray-900 border-2 border-amber-500 shadow-lg shadow-amber-500/10'
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

          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{tier.name}</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{tier.description}</p>

          <div className="mt-6 flex items-baseline gap-1">
            <span className="text-4xl font-semibold text-gray-900 dark:text-gray-100">
              {tier.price}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">{tier.period}</span>
          </div>

          <Link
            href={tier.href}
            className={`mt-6 block w-full py-3 px-4 text-center text-sm font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 ${
              tier.highlighted
                ? 'bg-amber-600 text-white hover:bg-amber-700'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {tier.cta}
          </Link>

          <ul className="mt-8 space-y-3" role="list">
            {tier.features.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-gray-600 dark:text-gray-400">
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
