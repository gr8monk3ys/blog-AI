import AdminBlogPageClient from './AdminBlogPageClient'

export const metadata = {
  title: 'Blog Admin | Blog AI',
  description: 'Create and manage blog posts in Postgres (Neon).',
}

export default function BlogAdminPage() {
  return <AdminBlogPageClient />
}
