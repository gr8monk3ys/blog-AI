/**
 * Types for the onboarding wizard
 */

import type { WritingStyle, ToneKeyword } from './brand'

/**
 * Content type choices presented in step 3
 */
export type FirstContentType = 'blog-post' | 'marketing-copy' | 'book-chapter'

/**
 * Full onboarding form state persisted across wizard steps
 */
export interface OnboardingFormData {
  /** Step 1 */
  name: string
  company: string

  /** Step 2 */
  writingStyle: WritingStyle
  toneKeywords: ToneKeyword[]
  sampleWriting: string

  /** Step 3 */
  firstContentType: FirstContentType
  topicSuggestion: string
}

/**
 * Metadata for each onboarding step
 */
export interface OnboardingStep {
  id: number
  title: string
  description: string
}

/**
 * The four steps shown in the wizard
 */
export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: 0,
    title: 'Welcome',
    description: 'Tell us about yourself',
  },
  {
    id: 1,
    title: 'Brand Voice',
    description: 'Set your writing style',
  },
  {
    id: 2,
    title: 'First Generation',
    description: 'Create your first piece',
  },
  {
    id: 3,
    title: 'Done',
    description: 'You are all set',
  },
]

/**
 * Pre-filled topic suggestions per content type
 */
export const TOPIC_SUGGESTIONS: Record<FirstContentType, string> = {
  'blog-post': '10 Ways AI Is Transforming Content Marketing in 2026',
  'marketing-copy': 'Product launch email sequence for a SaaS tool',
  'book-chapter': 'Chapter 1: The Rise of AI-Assisted Writing',
}

/**
 * Labels and descriptions for the first-content options in step 3
 */
export const FIRST_CONTENT_OPTIONS: {
  value: FirstContentType
  label: string
  description: string
}[] = [
  {
    value: 'blog-post',
    label: 'Blog Post',
    description: 'A long-form article optimized for SEO and engagement.',
  },
  {
    value: 'marketing-copy',
    label: 'Marketing Copy',
    description: 'Ad copy, landing pages, or email campaigns.',
  },
  {
    value: 'book-chapter',
    label: 'Book Chapter',
    description: 'A structured chapter with sections and sub-topics.',
  },
]
