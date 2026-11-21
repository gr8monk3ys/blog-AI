import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import { getUserIdOrNull } from '../../../lib/auth-session'
import ToolPageClient from './ToolPageClient'

export const metadata: Metadata = {
  title: 'Tool Workspace',
  description:
    'Run AI writing tools with brand voice controls, variations, research, and export options.',
}

export default async function ToolPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-gray-500">Loading tool…</div>}>
      <ToolPageClient />
    </Suspense>
  )
}
