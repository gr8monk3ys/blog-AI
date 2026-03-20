import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import KnowledgePage from './KnowledgePage'

export const metadata: Metadata = {
  title: 'Knowledge Base',
  description:
    'Upload company documents (style guides, product specs) so the AI references them during blog generation.',
}

export default async function KnowledgeBaseRoute() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <KnowledgePage />
}
