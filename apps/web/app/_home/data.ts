// Static marketing content for the homepage (features, steps, pricing, stats,
// tool-category pills, capabilities). Extracted from HomePageClient.tsx so the
// page component stays focused on layout rather than copy.

import type { ElementType } from 'react'
import {
  SparklesIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  PencilSquareIcon,
  RocketLaunchIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  BookOpenIcon,
  PhotoIcon,
  ArrowDownTrayIcon,
  BoltIcon,
  QueueListIcon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  BriefcaseIcon,
  VideoCameraIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import type { ToolCategory } from '../../types/tools'

export interface Feature {
  icon: ElementType
  title: string
  description: string
}

export const FEATURES: Feature[] = [
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
    icon: QueueListIcon,
    title: 'Bulk Campaign Workflows',
    description:
      'Queue up multiple topics, estimate cost before you run, and produce batches of content for publishing calendars without managing prompts one by one.',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Research & Fact-Checking',
    description:
      'Drafts pull from live web sources via SerpAPI, Tavily, and Metaphor. Claims are extracted and cross-referenced automatically so you publish with confidence scores, not guesswork.',
  },
]

export interface Step {
  number: string
  title: string
  description: string
  icon: ElementType
}

export const STEPS: Step[] = [
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

export interface PricingTier {
  name: string
  price: string
  period: string
  description: string
  features: string[]
  cta: string
  href: string
  highlighted: boolean
}

export const PRICING_TIERS: PricingTier[] = [
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
      'Export formats (JSON, CSV, Markdown)',
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
      'AI image generation',
      'Fact-checking',
      'Webhooks & integrations',
      'Priority support',
    ],
    cta: 'Choose Pro',
    href: '/pricing',
    highlighted: true,
  },
]

export interface Stat {
  value: string
  label: string
}

export const SOCIAL_STATS: Stat[] = [
  { value: '29+', label: 'AI writing tools and templates' },
  { value: '3', label: 'AI providers (GPT-4, Claude, Gemini)' },
  { value: 'bulk', label: 'CSV-powered batch generation' },
  { value: 'brand', label: 'voice training with scoring' },
]

export interface ToolCategoryPill {
  key: ToolCategory
  icon: ElementType
  label: string
}

export const TOOL_CATEGORY_PILLS: ToolCategoryPill[] = [
  { key: 'blog', icon: DocumentTextIcon, label: 'Blog & Articles' },
  { key: 'seo', icon: MagnifyingGlassIcon, label: 'SEO & Keywords' },
  { key: 'email', icon: EnvelopeIcon, label: 'Email & Outreach' },
  { key: 'social-media', icon: ChatBubbleLeftRightIcon, label: 'Social Media' },
  { key: 'business', icon: BriefcaseIcon, label: 'Business & Strategy' },
  { key: 'naming', icon: SparklesIcon, label: 'Naming & Branding' },
  { key: 'video', icon: VideoCameraIcon, label: 'Video Scripts' },
  { key: 'rewriting', icon: ArrowPathIcon, label: 'Rewriting & Editing' },
]

export interface Capability {
  icon: ElementType
  title: string
  description: string
  tier: 'Starter+' | 'Pro'
}

export const CAPABILITIES: Capability[] = [
  {
    icon: BookOpenIcon,
    title: 'Book Generation',
    description: 'Full chapter-by-chapter book drafts with structured outlines and section hierarchy.',
    tier: 'Starter+',
  },
  {
    icon: PhotoIcon,
    title: 'AI Image Generation',
    description: 'DALL-E 3 and Stability AI illustrations generated alongside your content.',
    tier: 'Pro',
  },
  {
    icon: GlobeAltIcon,
    title: 'Live Web Research',
    description: 'SerpAPI, Tavily AI, and Metaphor search integrated into the drafting pipeline.',
    tier: 'Starter+',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Fact-Checking',
    description: 'Claims extracted and cross-referenced against sources with confidence scores.',
    tier: 'Pro',
  },
  {
    icon: ArrowDownTrayIcon,
    title: 'Export & Publish',
    description: 'JSON, CSV, Markdown, and ZIP exports for any publishing workflow.',
    tier: 'Starter+',
  },
  {
    icon: BoltIcon,
    title: 'Webhooks & Integrations',
    description: 'Zapier-compatible webhooks with HMAC signing for content pipeline automation.',
    tier: 'Pro',
  },
]
