import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../../lib/clerk-auth'
import AdminBlogPageClient from './AdminBlogPageClient'

export const metadata: Metadata = {
  title: 'Blog Admin',
  description: 'Create and manage blog posts in Postgres (Neon).',
}

export default async function BlogAdminPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <AdminBlogPageClient />
}
