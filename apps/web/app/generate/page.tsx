import type { Metadata } from 'next'
import GeneratePageClient from './GeneratePageClient'

export const metadata: Metadata = {
  title: 'Generate Content | Blog AI',
  description:
    'Generate brand-consistent blog posts with AI-powered research, fact-checking, and SEO optimization.',
}

export default function GeneratePage() {
  return <GeneratePageClient />
}
