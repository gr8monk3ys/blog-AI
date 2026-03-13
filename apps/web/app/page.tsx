import type { Metadata } from 'next'
import { redirect } from 'next/navigation'

export const metadata: Metadata = {
  title: 'Blog AI | AI Content Generator for Blogs, Books, and Marketing',
  description:
    'Create SEO-optimized blogs, books, and marketing content with AI tools, brand voice controls, and multi-provider model support.',
}

export default function HomePage() {
  redirect('/home.html')
}
