import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import { getClerkUserIdOrNull } from '../../../lib/clerk-auth'
import ToolPageClient from './ToolPageClient'

export const metadata: Metadata = {
  title: 'Tool Workspace',
  description:
    'Run AI writing tools with brand voice controls, variations, research, and export options.',
}

export default async function ToolPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-gray-500">Loading tool...</div>}>
      <ToolPageClient />
    </Suspense>
  )
}
