import SiteHeader from '../../components/SiteHeader'
import AppShell from '../../components/app/AppShell'

/**
 * The signed-in pages sit under the same header sheet as the rest of the
 * site, beside the app rail (components/app/AppShell.tsx). The route group
 * adds no URL segment: `app/(app)/history/page.tsx` is still `/history`, and
 * lib/protected-routes.ts keeps matching by pathname.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <AppShell>{children}</AppShell>
    </>
  )
}
