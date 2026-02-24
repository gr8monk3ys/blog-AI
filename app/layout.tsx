import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { Providers } from './providers'
import './globals.css'

const inter = Inter({ subsets: ['latin'], display: 'swap' })

export const metadata: Metadata = {
  title: 'Blog AI Generator',
  description: 'AI-powered blog and book content generator',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  // Inline script to prevent flash of unstyled content (FOUC) on dark mode.
  // This is a static string with no user input — safe to use dangerouslySetInnerHTML.
  const themeScript =
    "(function(){try{var t=localStorage.getItem('theme');" +
    "if(t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme:dark)').matches))" +
    "{document.documentElement.classList.add('dark')}}catch(e){}})()"

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={inter.className}>
        {publishableKey ? (
          <ClerkProvider publishableKey={publishableKey}>
            <Providers>{children}</Providers>
          </ClerkProvider>
        ) : (
          <Providers>{children}</Providers>
        )}
      </body>
    </html>
  )
}
