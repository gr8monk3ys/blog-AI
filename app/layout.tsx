import type { Metadata } from 'next'
import Script from 'next/script'
import getBaseUrl from '../lib/site-url'
import './globals.css'

const metadataBase = new URL(getBaseUrl())

export const metadata: Metadata = {
  metadataBase,
  title: {
    default: 'Blog AI',
    template: '%s | Blog AI',
  },
  description: 'AI tools for blog posts, books, SEO briefs, and brand voice training.',
  applicationName: 'Blog AI',
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    siteName: 'Blog AI',
    url: metadataBase,
    title: 'Blog AI',
    description: 'Generate blog posts, books, and marketing content with AI tuned to your brand voice.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Blog AI',
    description: 'Generate blog posts, books, and marketing content with AI tuned to your brand voice.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Inline script to prevent flash of unstyled content (FOUC) on dark mode.
  // This is a static string with no user input — safe to use dangerouslySetInnerHTML.
  const themeScript =
    "(function(){try{var t=localStorage.getItem('theme');" +
    "if(t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme:dark)').matches))" +
    "{document.documentElement.classList.add('dark')}}catch(e){}})()"

  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <Script id="theme-init" strategy="beforeInteractive">
          {themeScript}
        </Script>
        {children}
      </body>
    </html>
  )
}
