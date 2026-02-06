import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Blog AI Generator',
  description: 'AI-powered blog and book content generator',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        {children}
      </body>
    </html>
  )
}
