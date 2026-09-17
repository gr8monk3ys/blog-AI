import type { Metadata } from 'next'
import PricingPageClient from './PricingPageClient'
import { loadPricingTiers } from './tiers'

export const metadata: Metadata = {
  title: 'Pricing',
  description:
    'Compare plans for Blog AI and choose the right tier for content generation limits, features, and billing options.',
}

export default async function PricingPage() {
  // Resolved on the server so the plan cards are in the document. See the note
  // on FALLBACK_PRICING_TIERS in ./tiers for why this is not a client fetch.
  const initialTiers = await loadPricingTiers()

  return <PricingPageClient initialTiers={initialTiers} />
}
