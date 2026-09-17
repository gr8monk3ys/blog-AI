import { API_ENDPOINTS } from '../../lib/api'
import type { UsageTier } from '../../types/usage'

export interface PublicPricingTier {
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

export const TIER_ORDER: UsageTier[] = ['free', 'starter', 'pro', 'business']

/**
 * The public plans, rendered in the server HTML.
 *
 * /pricing used to start with an empty grid and fill it in from
 * `GET /api/payments/pricing` after hydration. Three cards appearing at once
 * pushed the comparison table and everything under it down the page, which is
 * where the route's mobile CLS of 0.359 came from (Lighthouse blamed
 * `main > section.bg-white`, the section the cards shove downwards). It also
 * meant the page showed nothing at all whenever the API was unreachable.
 *
 * So the plans ship in the document and the API only ever refines them. These
 * values mirror the backend, which is the source of truth:
 *   - prices + feature bullets: PRICING_TIERS in apps/api/src/types/payments.py
 *   - limits + descriptions:    TIER_CONFIGS in apps/api/src/types/usage.py
 * (`GET /api/payments/pricing` joins exactly those two, see
 * apps/api/app/routes/payments.py.) They are also the prices the home page
 * has always hardcoded in app/_home/data.ts. If you change a price in the
 * backend, change it here in the same PR.
 *
 * `stripe_price_id_*` are deliberately absent: they come from Stripe env vars
 * that only the API knows. Until the fetch lands, the CTA renders as a
 * disabled "Loading..." button of exactly the same size, so resolving them
 * costs no layout shift.
 */
export const FALLBACK_PRICING_TIERS: PublicPricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Perfect for trying out Blog AI',
    price_monthly: 0,
    price_yearly: 0,
    daily_limit: 2,
    monthly_limit: 5,
    generations_per_month: 5,
    features: [
      '5 generations per month',
      'Basic blog generation',
      'Standard support',
    ],
  },
  {
    id: 'starter',
    name: 'Starter',
    description: 'For individuals getting started with content creation',
    price_monthly: 19,
    price_yearly: 190,
    daily_limit: 10,
    monthly_limit: 50,
    generations_per_month: 50,
    features: [
      '50 generations per month',
      'Blog and book generation',
      'Research mode',
      'Priority support',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'For content creators and marketers',
    price_monthly: 49,
    price_yearly: 490,
    daily_limit: 50,
    monthly_limit: 200,
    generations_per_month: 200,
    features: [
      '200 generations per month',
      'All content types',
      'Bulk generation',
      'Brand voice training',
      'Priority support',
    ],
  },
]

/**
 * We do not sell the Business/Agency tier yet (no seats, no invites), so it
 * never reaches the page even when the API returns it.
 */
export function normalizePricingTiers(tiers: PublicPricingTier[]): PublicPricingTier[] {
  return tiers
    .filter((tier) => tier.id !== 'business')
    .sort((a, b) => TIER_ORDER.indexOf(a.id) - TIER_ORDER.indexOf(b.id))
}

/**
 * Server-side read of the live plans, used to render the cards in the document.
 *
 * Never throws and never blocks the page for long: a slow or missing API just
 * means the page renders FALLBACK_PRICING_TIERS, which is what CI and local
 * builds (no backend on NEXT_PUBLIC_API_URL) always do.
 */
export async function loadPricingTiers(): Promise<PublicPricingTier[]> {
  try {
    const response = await fetch(API_ENDPOINTS.payments.pricing, {
      // Public data; revalidate rather than refetch on every render so the
      // extra hop does not sit on the critical path of each page view.
      next: { revalidate: 600 },
      signal: AbortSignal.timeout(2500),
    })

    if (!response.ok) return FALLBACK_PRICING_TIERS

    const data = await response.json()
    if (!data?.success || !Array.isArray(data?.tiers)) return FALLBACK_PRICING_TIERS

    const tiers = normalizePricingTiers(data.tiers as PublicPricingTier[])
    return tiers.length > 0 ? tiers : FALLBACK_PRICING_TIERS
  } catch {
    // Unreachable API, DNS failure, timeout — the page still has plans to show.
    return FALLBACK_PRICING_TIERS
  }
}
