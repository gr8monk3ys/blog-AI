import type { Metadata } from 'next'
import HomePageClient from './HomePageClient'

export const metadata: Metadata = {
  title: {
    absolute: 'Blog AI — Brand-Consistent AI Content',
  },
  description:
    'Train your brand voice, run repeatable SEO content workflows, and generate publish-ready drafts faster.',
}

export default function HomePage() {
  return <HomePageClient />
}
