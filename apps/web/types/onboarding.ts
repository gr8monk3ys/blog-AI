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
  'marketing-copy': 'Q2 campaign content plan for a SaaS launch aimed at operations teams',
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
    label: 'SEO Blog Workflow',
    description: 'Best for recurring blog production with keywords and brand voice.',
  },
  {
    value: 'marketing-copy',
    label: 'Campaign Copy',
    description: 'For launches, landing pages, email sequences, and supporting assets.',
  },
  {
    value: 'book-chapter',
    label: 'Long-Form Draft',
    description: 'For structured chapters and deeper educational content.',
  },
]
