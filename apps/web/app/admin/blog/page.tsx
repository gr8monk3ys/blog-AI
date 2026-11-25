import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../../lib/auth-session'
import AdminBlogPageClient from './AdminBlogPageClient'

export const metadata: Metadata = {
  title: 'Blog Admin',
  description: 'Create and manage blog posts in Postgres (Neon).',
}

export default async function BlogAdminPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <AdminBlogPageClient />
}
