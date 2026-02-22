import type { Metadata } from 'next'

import TermsPageClient from './TermsPageClient'

export const metadata: Metadata = {
  title: 'Terms of Service | Blog AI',
  description:
    'Read the terms and conditions governing your use of the Blog AI platform.',
}

export default function TermsPage(): React.ReactElement {
  return <TermsPageClient />
}
