/**
 * Which optional capabilities this deployment may advertise.
 *
 * The API decides what actually works from its own environment (`/health`
 * reports it: which LLM providers are configured, whether research keys exist,
 * whether Stripe is on). The copy did not follow: the footer said "Powered by
 * GPT-4, Claude & Gemini" with no Gemini key anywhere, pricing sold research
 * mode that needs three keys none of which production has, and the knowledge
 * base page was reachable while the backend flag that enables it was off.
 *
 * This is the one place a page asks "may I say this?". Each getter reads one
 * `NEXT_PUBLIC_*` variable, written out literally so Next.js inlines it into
 * both the server and client bundles at build time -- so a flag must be set
 * for the `build`, not only for `start`. Getters, not constants, so each
 * access re-reads the environment and tests can set a variable without
 * resetting modules.
 *
 * Defaults mirror the live deployment on 2026-10-13: content generation,
 * brand profiles, history, analytics and payments are on; everything else is
 * off until the owner sets the flag in Vercel together with the API key the
 * feature needs. The flag says "we promise this"; the API key makes it true.
 * Set both or neither.
 */

import { getSignupMode, type SignupMode } from './signup-mode'

const TRUE_VALUES = new Set(['1', 'true', 'on', 'yes'])
const FALSE_VALUES = new Set(['0', 'false', 'off', 'no'])

/**
 * Parse a boolean flag. Unset or empty returns `fallback`; anything that is not
 * a recognised true/false word is treated as off, so a typo never turns a
 * promise on.
 */
export function parseFlag(value: string | undefined, fallback = false): boolean {
  const normalised = value?.trim().toLowerCase()
  if (!normalised) return fallback
  if (TRUE_VALUES.has(normalised)) return true
  if (FALSE_VALUES.has(normalised)) return false
  return false
}

export const features = {
  /** `/knowledge` and its nav link. Needs the API's `ENABLE_KNOWLEDGE_BASE` and a vector store. */
  get knowledgeBase(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE)
  },

  /** Gemini as a selectable provider. Needs `GEMINI_API_KEY` and the google-genai extra on the API. */
  get gemini(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_LLM_GEMINI)
  },

  /** Research mode, fact-check sources, SERP analysis. Needs SERP/Tavily/Metaphor keys on the API. */
  get webResearch(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_WEB_RESEARCH)
  },

  /** `/images`. Needs `IMAGE_PROVIDER` plus an OpenAI or Stability key on the API. */
  get imageGeneration(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_IMAGE_GENERATION)
  },

  /** `/plagiarism`. Needs Copyscape or Originality credentials on the API. */
  get plagiarismCheck(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_PLAGIARISM_CHECK)
  },

  /** `/social`. Needs Twitter/LinkedIn OAuth or a Buffer token, and a scheduler worker. */
  get socialPosting(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_SOCIAL_POSTING)
  },

  /** `/team`: organisations and invites. No mailer exists yet to deliver the invites. */
  get teams(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_TEAMS)
  },

  /** Pricing, checkout and the billing portal. On by default: Stripe is live. */
  get billing(): boolean {
    return parseFlag(process.env.NEXT_PUBLIC_FEATURE_BILLING, true)
  },

  /** `open | waitlist | invite`; see lib/signup-mode.ts. */
  get signupMode(): SignupMode {
    return getSignupMode()
  },
}

export type FeatureName = Exclude<keyof typeof features, 'signupMode'>

/** The env var behind each boolean flag, for docs and `scripts/check-env.mjs`. */
export const FEATURE_FLAG_ENV: Record<FeatureName, string> = {
  knowledgeBase: 'NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE',
  gemini: 'NEXT_PUBLIC_LLM_GEMINI',
  webResearch: 'NEXT_PUBLIC_FEATURE_WEB_RESEARCH',
  imageGeneration: 'NEXT_PUBLIC_FEATURE_IMAGE_GENERATION',
  plagiarismCheck: 'NEXT_PUBLIC_FEATURE_PLAGIARISM_CHECK',
  socialPosting: 'NEXT_PUBLIC_FEATURE_SOCIAL_POSTING',
  teams: 'NEXT_PUBLIC_FEATURE_TEAMS',
  billing: 'NEXT_PUBLIC_FEATURE_BILLING',
}

export { getSignupMode, type SignupMode } from './signup-mode'
