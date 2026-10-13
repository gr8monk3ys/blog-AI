/**
 * Fonts are self-hosted and never fetched at build time. next/font/local
 * reads the files from the hoisted node_modules/@fontsource* packages, so the
 * check is that each referenced file exists and that nothing under apps/web
 * imports next/font/google.
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = process.cwd()
const FONTS_TS = readFileSync(join(ROOT, 'lib/fonts.ts'), 'utf8')

const SCAN_DIRS = ['app', 'components', 'hooks', 'lib']

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? walk(p) : /\.(ts|tsx)$/.test(n) ? [p] : []
  })
}

describe('self-hosted fonts', () => {
  it('references woff2 files that exist on disk', () => {
    const srcs = [...FONTS_TS.matchAll(/(?:src|path):\s*'([^']+\.woff2)'/g)].map((m) => m[1]!)
    expect(srcs.length).toBeGreaterThanOrEqual(5)
    for (const src of srcs) {
      expect({ src, exists: existsSync(join(ROOT, 'lib', src)) }).toEqual({ src, exists: true })
    }
  })

  it('exposes the three voices as CSS variables', () => {
    for (const v of ['--font-display', '--font-body', '--font-mono']) {
      expect(FONTS_TS).toContain(`variable: '${v}'`)
    }
  })

  it('preloads the body and display voices; the mono label is optional and not preloaded', () => {
    const blocks = FONTS_TS.split(/export const /).slice(1)
    const by = (name: string) => blocks.find((b) => b.startsWith(name))!
    expect(by('fontBody')).not.toContain('preload: false')
    // The home h1 is the LCP element in this face; a late swap measured
    // 0.117 CLS on CI. See the comment in lib/fonts.ts.
    expect(by('fontDisplay')).toContain('preload: true')
    expect(by('fontDisplay')).toContain("adjustFontFallback: 'Times New Roman'")
    expect(by('fontMono')).toContain('preload: false')
    expect(by('fontMono')).toContain("display: 'optional'")
  })

  it('never imports next/font/google anywhere under apps/web', () => {
    const offenders = SCAN_DIRS.flatMap((d) => walk(join(ROOT, d))).filter((f) =>
      readFileSync(f, 'utf8').includes('next/font/google')
    )
    expect(offenders).toEqual([])
  })

  it('the layout wires the three variables onto the document', () => {
    const layout = readFileSync(join(ROOT, 'app/layout.tsx'), 'utf8')
    for (const v of ['fontBody.variable', 'fontDisplay.variable', 'fontMono.variable']) {
      expect(layout).toContain(v)
    }
  })
})
