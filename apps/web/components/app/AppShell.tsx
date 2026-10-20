'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '../../lib/cn'
import { APP_NAV, activeNavHref } from './nav'

/**
 * The signed-in app shell (DESIGN.md → Layout, → Navigation): a 260px rail
 * of the same paper as the page with a hairline right rule — no fill change
 * — beside a content column padded 24px (32px from md). The rail carries a
 * mono section head per group and items in sans, muted until active, when
 * both the text and a 2px left rule take the ink; hover tints the paper to
 * the ink at 5% and nothing lifts. Below md the rail collapses to a
 * hairline-topped bar that scrolls sideways under the header.
 *
 * The shell renders the page's single <main> landmark; pages render a
 * <PageHeader> at the top of their content and nothing else of the chrome.
 */
const RAIL_ITEM =
  'flex w-full items-center border-l-2 border-transparent px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors duration-150 hover:bg-primary/5 hover:text-foreground'

const BAR_ITEM =
  'shrink-0 border-b-2 border-transparent px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors duration-150 hover:text-foreground'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const active = activeNavHref(pathname)

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col md:flex-row">
      {/* The rail. Sticky under the 64px header sheet so long pages keep it. */}
      <nav
        aria-label="App"
        className="hidden w-[260px] shrink-0 border-r border-border md:sticky md:top-16 md:flex md:max-h-[calc(100vh-4rem)] md:flex-col md:overflow-y-auto"
      >
        <div className="flex flex-col gap-6 px-3 pb-8 pt-6">
          {APP_NAV.map((section) => (
            <div key={section.head}>
              <p className="label-mono px-3 pb-2">{section.head}</p>
              <ul className="flex flex-col gap-0.5">
                {section.items.map((item) => {
                  const isActive = item.href === active
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        aria-current={isActive ? 'page' : undefined}
                        className={cn(RAIL_ITEM, isActive && 'border-primary text-primary hover:text-primary')}
                      >
                        {item.label}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      </nav>

      {/* Below md: the same items as one hairline-topped bar. */}
      <nav aria-label="App" className="border-y border-border md:hidden">
        <ul className="flex overflow-x-auto px-2">
          {APP_NAV.flatMap((section) => section.items).map((item) => {
            const isActive = item.href === active
            return (
              <li key={item.href} className="shrink-0">
                <Link
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={cn('block', BAR_ITEM, isActive && 'border-primary text-primary hover:text-primary')}
                >
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <main
        id="main-content"
        tabIndex={-1}
        className="min-w-0 flex-1 px-4 py-6 sm:px-6 md:px-8 md:py-8"
      >
        {children}
      </main>
    </div>
  )
}
