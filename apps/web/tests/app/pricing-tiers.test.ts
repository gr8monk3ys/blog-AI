import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  FALLBACK_PRICING_TIERS,
  RESEARCH_MODE_FEATURE,
  normalizePricingTiers,
  withoutUnavailableFeatures,
  type PublicPricingTier,
} from '../../app/pricing/tiers'

/**
 * Research mode needs SERP/Tavily keys on the API, which production does not
 * have (`/health` reports `web_research.available=false`). The plans must not
 * sell it unless the deployment has said it can deliver it.
 */
const apiStarter: PublicPricingTier = {
  id: 'starter',
  name: 'Starter',
  price_monthly: 19,
  price_yearly: 190,
  features: ['50 generations per month', RESEARCH_MODE_FEATURE, 'Priority support'],
}

const allFeatures = (tiers: PublicPricingTier[]) => tiers.flatMap((tier) => tier.features)

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('research copy on the plans', () => {
  it('drops research bullets while web research is off', () => {
    vi.stubEnv('NEXT_PUBLIC_FEATURE_WEB_RESEARCH', '')
    expect(allFeatures(normalizePricingTiers([apiStarter]))).not.toContain(RESEARCH_MODE_FEATURE)
    expect(allFeatures(normalizePricingTiers(FALLBACK_PRICING_TIERS))).not.toContain(
      RESEARCH_MODE_FEATURE
    )
    expect(withoutUnavailableFeatures(['Fact-checking', 'Bulk generation'])).toEqual([
      'Bulk generation',
    ])
  })

  it('keeps what the API lists once web research is on', () => {
    vi.stubEnv('NEXT_PUBLIC_FEATURE_WEB_RESEARCH', 'true')
    expect(normalizePricingTiers([apiStarter])[0].features).toEqual(apiStarter.features)
  })
})
