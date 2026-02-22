import type { Metadata } from 'next'
import PricingPageClient from './PricingPageClient'

export const metadata: Metadata = {
  title: 'Pricing | Blog AI',
  description:
    'Compare plans for Blog AI and choose the right tier for content generation limits, features, and billing options.',
}

export default function PricingPage() {
  return <PricingPageClient />
}
