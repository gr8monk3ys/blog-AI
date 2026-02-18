import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ToolPageClient from './ToolPageClient'

export default async function ToolPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <ToolPageClient />
}
