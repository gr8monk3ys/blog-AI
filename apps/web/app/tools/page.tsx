import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import ToolsPageClient from './ToolsPageClient'

export const metadata: Metadata = {
  title: 'AI Tools',
  description:
    'Browse AI writing tools by category and launch purpose-built workflows for blogs, email, social, and more.',
}

export default async function ToolsPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-gray-500">Loading tools...</div>}>
      <ToolsPageClient />
    </Suspense>
  )
}
