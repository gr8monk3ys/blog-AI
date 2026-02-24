import type { Metadata } from 'next'

import PrivacyPageClient from './PrivacyPageClient'

export const metadata: Metadata = {
  title: 'Privacy Policy | Blog AI',
  description:
    'Learn how Blog AI collects, uses, and protects your personal information.',
}

export default function PrivacyPage(): React.ReactElement {
  return <PrivacyPageClient />
}
