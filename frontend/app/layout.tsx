import type { Metadata } from 'next'
import { Inter, Source_Serif_4 } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })
const sourceSerif = Source_Serif_4({ subsets: ['latin'], variable: '--font-serif' })

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
      <body className={`${inter.className} ${sourceSerif.variable}`}>
        {children}
      </body>
    </html>
  )
}
