import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ToolsPageClient from './ToolsPageClient'

export default async function ToolsPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <ToolsPageClient />
}
