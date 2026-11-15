import { existsSync, readdirSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { describe, it, expect } from 'vitest'
import { createPathMatcher } from '@clerk/shared/pathMatcher'
import { PROTECTED_ROUTE_PATTERNS } from '../../lib/protected-routes'

const APP_DIR = resolve(__dirname, '../../app')
const isProtected = createPathMatcher(PROTECTED_ROUTE_PATTERNS)

function pageDirs(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isDirectory()) return pageDirs(join(dir, entry.name))
    return entry.name === 'page.tsx' ? [dir] : []
  })
}

// app/tools/[slug] -> /tools/slug; optional catch-alls and route groups drop out.
function pathnameOf(dir: string): string {
  const segments = relative(APP_DIR, dir)
    .split('/')
    .filter((s) => s && !s.startsWith('(') && !s.startsWith('[[...'))
    .map((s) => s.replace(/^\[(?:\.\.\.)?(.+)\]$/, '$1'))
  return `/${segments.join('/')}`
}

function hasLoadingAbove(dir: string): boolean {
  for (let d = dir; d.startsWith(APP_DIR); d = dirname(d)) {
    if (existsSync(join(d, 'loading.tsx'))) return true
  }
  return false
}

// A loading.tsx makes the server send its spinner first and swap the page in
// afterwards. That is right for a signed-in workspace and wrong for a public
// page, whose headline would then paint late behind "Loading your workspace…".
describe('route loading state', () => {
  it.each(pageDirs(APP_DIR).map((dir) => [pathnameOf(dir), dir] as const))(
    '%s has a loading.tsx only if it needs a session',
    (pathname, dir) => {
      const where = relative(APP_DIR, dir) || '.'
      const message = isProtected(pathname)
        ? `app/${where} is protected: add loading.tsx re-exporting components/RouteLoading to its top folder.`
        : `app/${where} is public: remove the loading.tsx above it (keep loading.tsx inside protected folders only).`
      expect(hasLoadingAbove(dir), message).toBe(isProtected(pathname))
    }
  )
})
