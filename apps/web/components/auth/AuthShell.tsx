import type { ReactNode } from 'react'
import SiteFooter from '../SiteFooter'
import SiteHeader from '../SiteHeader'

// One centred 28rem column (DESIGN.md → Layout): a wall label, the headline
// in Fraunces, a lead, then the form. Shared by every auth page.
export default function AuthShell({
  label,
  title,
  lead,
  children,
}: {
  label: string
  title: string
  lead: string
  children: ReactNode
}): ReactNode {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <section className="mx-auto max-w-md px-4 py-14 sm:px-6 md:py-20">
          <p className="label-mono">{label}</p>
          <h1 className="text-page-title mt-3">{title}</h1>
          <p className="mt-3 text-muted-foreground">{lead}</p>
          <div className="mt-8">{children}</div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
