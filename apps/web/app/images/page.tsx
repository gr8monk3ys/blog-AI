import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import ImageGenerationPage from './ImageGenerationPage'

export const metadata: Metadata = {
  title: 'AI Image Generation',
  description:
    'Generate images for your blog posts and social media using AI. DALL-E 3 and Stability AI powered.',
}

export default async function ImagesPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <ImageGenerationPage />
}
