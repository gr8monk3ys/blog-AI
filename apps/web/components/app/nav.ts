/**
 * The signed-in app's rail (DESIGN.md → Navigation). Five mono section heads,
 * each a short list of pages. Route patterns are URL-based and must stay in
 * step with lib/protected-routes.ts; the Knowledge Base entry follows the same
 * build-time flag SiteHeader uses so the rail never advertises a route the
 * backend rejects.
 */
export interface AppNavItem {
  href: string
  label: string
}

export interface AppNavSection {
  /** The wall label above the items. */
  head: string
  items: AppNavItem[]
}

const knowledgeBaseEnabled = process.env.NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE === 'true'

export const APP_NAV: AppNavSection[] = [
  {
    head: 'Write',
    items: [
      { href: '/generate', label: 'Generate' },
      { href: '/bulk', label: 'Bulk' },
      { href: '/tools', label: 'Tools' },
      { href: '/remix', label: 'Remix' },
      { href: '/images', label: 'Images' },
    ],
  },
  {
    head: 'Brand',
    items: [
      { href: '/brand', label: 'Brand voice' },
      { href: '/brand/train', label: 'Voice training' },
      { href: '/brand/score', label: 'Brand score' },
    ],
  },
  {
    head: 'Library',
    items: [
      { href: '/history', label: 'History' },
      { href: '/templates', label: 'Templates' },
      ...(knowledgeBaseEnabled ? [{ href: '/knowledge', label: 'Knowledge base' }] : []),
      { href: '/plagiarism', label: 'Plagiarism' },
    ],
  },
  {
    head: 'Publish',
    items: [
      { href: '/social', label: 'Social' },
      { href: '/analytics', label: 'Analytics' },
      { href: '/settings/webhooks', label: 'Webhooks' },
    ],
  },
  {
    head: 'Account',
    items: [
      { href: '/team', label: 'Team' },
      { href: '/pricing', label: 'Plan' },
    ],
  },
]

/**
 * The one active item for a pathname: the longest href that is the path or a
 * parent of it, so `/brand/train` lights "Voice training" and not "Brand
 * voice". Returns null on a page the rail does not list (onboarding, admin).
 */
export function activeNavHref(pathname: string | null): string | null {
  if (!pathname) return null
  let best: string | null = null
  for (const section of APP_NAV) {
    for (const { href } of section.items) {
      const matches = pathname === href || pathname.startsWith(`${href}/`)
      if (matches && (best === null || href.length > best.length)) best = href
    }
  }
  return best
}
