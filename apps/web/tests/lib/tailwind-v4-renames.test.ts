/**
 * Tailwind v4 renamed or removed several v3 utilities. The upgrade codemod
 * handled the tree once; this keeps the old spellings from drifting back in
 * via copy-paste from v3-era snippets. Each pattern is a v3 spelling that v4
 * either ignores (silently producing no CSS) or interprets differently.
 *
 * Not listed on purpose:
 * - `shadow-sm`, `backdrop-blur-sm`, `rounded-sm`, `blur-sm`: valid v4 names
 *   (one step larger than in v3). The codemod shifted every v3 use down a
 *   step; a regex cannot tell a correct v4 `shadow-sm` from a pasted v3 one.
 * - `ring-offset-*` and `placeholder-<colour>`: still supported in v4 (the
 *   compiled stylesheet was checked for both).
 * - bare `rounded` / `shadow` / `blur`: deprecated aliases in v4 that still
 *   render the v3 value; the codemod spelled them explicitly, but a regex for
 *   them matches prose and CSS (`blur(18px)`) far more than class strings.
 * - the `!important` prefix: `!flex` in a class string is not separable from
 *   `!flag` in code by regex; the codemod moved every real one to the suffix.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = process.cwd()
const SCAN_DIRS = ['app', 'components', 'hooks', 'lib', 'types']

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) return sourceFiles(full)
    return /\.(tsx|ts|css)$/.test(name) && !/\.d\.ts$/.test(name) ? [full] : []
  })
}

const V3_ONLY: Array<{ pattern: RegExp; v4: string }> = [
  { pattern: /(?<![\w-])outline-none(?![\w-])/, v4: 'outline-hidden' },
  { pattern: /(?<![\w-])bg-gradient-to-(r|l|t|b|tr|tl|br|bl)(?![\w-])/, v4: 'bg-linear-to-*' },
  { pattern: /(?<![\w-])(flex-shrink|flex-grow)(-0)?(?![\w-])/, v4: 'shrink / grow' },
  { pattern: /(?<![\w-])overflow-ellipsis(?![\w-])/, v4: 'text-ellipsis' },
  { pattern: /(?<![\w-])decoration-(slice|clone)(?![\w-])/, v4: 'box-decoration-*' },
  // v4 dropped the *-opacity-* utilities; the colour takes the alpha instead.
  {
    pattern: /(?<![\w-])(bg|text|border|ring|divide|placeholder)-opacity-\d+(?![\w-])/,
    v4: '<colour>/<alpha>, e.g. ring-amber-500/75',
  },
  // CSS variables in arbitrary values use parentheses in v4.
  { pattern: /(?<![\w-])[a-z-]+-\[--[\w-]+\]/, v4: 'utility-(--var)' },
  { pattern: /(?<![\w-])max-w-screen-(sm|md|lg|xl|2xl)(?![\w-])/, v4: 'max-w-(--breakpoint-*)' },
]

describe('Tailwind v4 class names', () => {
  const files = SCAN_DIRS.flatMap((dir) => sourceFiles(join(ROOT, dir)))

  it('scans a realistic number of files', () => {
    expect(files.length).toBeGreaterThan(100)
  })

  for (const { pattern, v4 } of V3_ONLY) {
    it(`uses ${v4} rather than ${pattern.source}`, () => {
      const offenders = files.filter((f) => pattern.test(readFileSync(f, 'utf8')))
      expect(offenders.map((f) => relative(ROOT, f).replace(/\\/g, '/'))).toEqual([])
    })
  }

  it('keeps the v4 setup files and none of the v3 ones', () => {
    expect(statSync(join(ROOT, 'postcss.config.js')).isFile()).toBe(true)
    expect(() => statSync(join(ROOT, 'tailwind.config.js'))).toThrow()
    const css = readFileSync(join(ROOT, 'app/globals.css'), 'utf8')
    expect(css).toMatch(/^@import 'tailwindcss';/)
    expect(css).not.toMatch(/@tailwind (base|components|utilities)/)
  })
})
