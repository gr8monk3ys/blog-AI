import type { MetadataRoute } from 'next'
import getBaseUrl from '../lib/site-url'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = getBaseUrl()

  return {
    rules: {
      userAgent: '*',
      allow: ['/', '/tools', '/pricing', '/blog'],
      disallow: ['/api/', '/admin/', '/sign-in', '/sign-up', '/onboarding'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
