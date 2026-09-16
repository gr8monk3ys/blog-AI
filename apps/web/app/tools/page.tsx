import type { Metadata } from 'next'
import { Suspense } from 'react'
import ToolsPageClient from './ToolsPageClient'

export const metadata: Metadata = {
  title: 'AI Tools',
  description:
    'Browse AI writing tools by category and launch purpose-built workflows for blogs, email, social, and more.',
}

// Public marketing/SEO page: it is listed in app/sitemap.ts, linked from
// SiteFooter and /tool-directory, and renders entirely from the bundled
// SAMPLE_TOOLS catalogue with no authenticated request. Signing in is only
// required to open an individual tool workspace at /tools/[slug].
export default function ToolsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-gray-500">Loading tools...</div>}>
      <ToolsPageClient />
    </Suspense>
  )
}
