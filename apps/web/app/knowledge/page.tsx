import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import KnowledgePage from './KnowledgePage'

export const metadata: Metadata = {
  title: 'Knowledge Base',
  description:
    'Upload company documents (style guides, product specs) so the AI references them during blog generation.',
}

export default async function KnowledgeBaseRoute() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <KnowledgePage />
}
