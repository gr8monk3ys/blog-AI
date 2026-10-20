import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import AppShell from '@/components/app/AppShell'
import PageHeader from '@/components/app/PageHeader'
import EmptyState from '@/components/app/EmptyState'
import { APP_NAV, activeNavHref } from '@/components/app/nav'

const pathname = vi.hoisted(() => ({ current: '/history' }))
vi.mock('next/navigation', () => ({
  usePathname: () => pathname.current,
}))

describe('activeNavHref', () => {
  it('lights the longest matching item, so a child route does not light its parent', () => {
    expect(activeNavHref('/brand')).toBe('/brand')
    expect(activeNavHref('/brand/train')).toBe('/brand/train')
    expect(activeNavHref('/settings/webhooks')).toBe('/settings/webhooks')
    expect(activeNavHref('/tools/blog-post-generator')).toBe('/tools')
  })

  it('returns null for pages the rail does not list', () => {
    expect(activeNavHref('/onboarding')).toBeNull()
    expect(activeNavHref('/admin/blog')).toBeNull()
    expect(activeNavHref(null)).toBeNull()
  })

  it('never advertises the Knowledge Base when its flag is off', () => {
    const hrefs = APP_NAV.flatMap((s) => s.items.map((i) => i.href))
    expect(hrefs).not.toContain('/knowledge')
  })
})

describe('AppShell', () => {
  it('renders the single main landmark, the rail with mono section heads, and aria-current on the active item', () => {
    pathname.current = '/history'
    render(
      <AppShell>
        <p>page</p>
      </AppShell>
    )
    const main = screen.getByRole('main')
    expect(main).toHaveAttribute('id', 'main-content')
    expect(screen.getAllByRole('main')).toHaveLength(1)

    for (const section of APP_NAV) {
      expect(screen.getAllByText(section.head)[0]).toHaveClass('label-mono')
    }

    const active = screen.getAllByRole('link', { name: 'History' })
    // One in the rail, one in the mobile bar; both mark the current page.
    expect(active).toHaveLength(2)
    for (const link of active) {
      expect(link).toHaveAttribute('aria-current', 'page')
      expect(link).toHaveClass('border-primary', 'text-primary')
    }
    const inactive = screen.getAllByRole('link', { name: 'Generate' })[0]
    expect(inactive).not.toHaveAttribute('aria-current')
  })
})

describe('PageHeader and EmptyState', () => {
  it('PageHeader is a wall label, one h1 in the display scale and a muted description', () => {
    render(<PageHeader kicker="Library" title="Content History" description="All of it." />)
    expect(screen.getByText('Library')).toHaveClass('label-mono')
    const h1 = screen.getByRole('heading', { level: 1, name: 'Content History' })
    expect(h1).toHaveClass('text-page-title')
    expect(screen.getByText('All of it.')).toHaveClass('text-muted-foreground')
  })

  it('EmptyState is a wall label, one serif line and at most one action', () => {
    render(
      <EmptyState
        kicker="History"
        title="No content history"
        description="Generate something."
        action={<button type="button">Start</button>}
      />
    )
    expect(screen.getByText('History')).toHaveClass('label-mono')
    expect(screen.getByRole('heading', { level: 2, name: 'No content history' })).toHaveClass(
      'text-section-title'
    )
    expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument()
  })
})
