/**
 * Every text/ground pair the notebook uses must clear WCAG AA (4.5:1) in both
 * themes, measured from the HSL triplets in app/globals.css rather than
 * trusted from DESIGN.md. A future lighter ink cannot silently break the
 * small-text sites that use text-primary.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const CSS = readFileSync(join(process.cwd(), 'app/globals.css'), 'utf8')

function block(selector: string): Record<string, string> {
  const m = CSS.match(new RegExp(`\\n\\s*${selector.replace('.', '\\.')}\\s*\\{([^}]+)\\}`))
  if (!m) throw new Error(`no ${selector} block`)
  const out: Record<string, string> = {}
  for (const line of m[1]!.split('\n')) {
    const kv = line.match(/^\s*(--[\w-]+):\s*([^;]+);/)
    if (kv) out[kv[1]!] = kv[2]!.trim()
  }
  return out
}

function hslToRgb(triplet: string): [number, number, number] {
  const [h = 0, s = 0, l = 0] = triplet.replace(/%/g, '').split(/\s+/).map(Number)
  const S = s / 100
  const L = l / 100
  const k = (n: number) => (n + h / 30) % 12
  const a = S * Math.min(L, 1 - L)
  const f = (n: number) => L - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)))
  return [f(0), f(8), f(4)].map((v) => Math.round(v * 255)) as [number, number, number]
}

const lum = ([r, g, b]: [number, number, number]) => {
  const c = [r, g, b].map((v) => {
    v /= 255
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * c[0]! + 0.7152 * c[1]! + 0.0722 * c[2]!
}

const contrast = (a: string, b: string) => {
  const [l1, l2] = [lum(hslToRgb(a)), lum(hslToRgb(b))].sort((x, y) => y - x) as [number, number]
  return (l1 + 0.05) / (l2 + 0.05)
}

const hex = (triplet: string) =>
  `#${hslToRgb(triplet)
    .map((v) => v.toString(16).padStart(2, '0'))
    .join('')}`

const PAIRS: Array<[string, string, number]> = [
  ['--foreground', '--background', 4.5],
  ['--foreground', '--muted', 4.5],
  ['--card-foreground', '--card', 4.5],
  ['--muted-foreground', '--background', 4.5],
  ['--muted-foreground', '--card', 4.5],
  ['--muted-foreground', '--muted', 4.5],
  ['--primary', '--background', 4.5],
  ['--primary', '--card', 4.5],
  ['--primary', '--muted', 4.5],
  ['--primary-foreground', '--primary', 4.5],
  // --secondary is a fill (Iron Gall Soft), measured against its own
  // foreground; it only doubles as text on paper, asserted below for light.
  ['--secondary-foreground', '--secondary', 4.5],
  ['--destructive', '--background', 4.5],
  ['--destructive-foreground', '--destructive', 4.5],
  ['--success', '--background', 4.5],
  ['--warning', '--background', 4.5],
  ['--info', '--background', 4.5],
  ['--accent-foreground', '--accent', 4.5],
  ['--popover-foreground', '--popover', 4.5],
  ['--ring', '--background', 3], // the focus outline sits on the page, 3:1 is the non-text floor
  ['--border', '--background', 1.15], // a hairline only has to be visible
]

for (const [theme, selector] of [
  ['light', ':root'],
  ['dark', '.dark'],
] as const) {
  describe(`${theme} tokens`, () => {
    const t = block(selector)
    for (const [fg, bg, floor] of PAIRS) {
      it(`${fg} on ${bg} ≥ ${floor}:1`, () => {
        expect(t[fg]).toBeDefined()
        expect(t[bg]).toBeDefined()
        expect(contrast(t[fg]!.split('/')[0]!, t[bg]!.split('/')[0]!)).toBeGreaterThanOrEqual(
          floor
        )
      })
    }
  })
}

describe('the ink', () => {
  const light = block(':root')
  const dark = block('.dark')

  it('is Iron Gall in both themes, at the hexes DESIGN.md records', () => {
    expect(light['--primary']).toBe('224 48% 32%')
    expect(hex(light['--primary']!)).toBe('#2a3f79')
    expect(dark['--primary']).toBe('224 55% 76%')
    expect(hex(dark['--primary']!)).toBe('#a0b2e3')
    expect(hex(light['--secondary']!)).toBe('#465a91')
    expect(hex(dark['--secondary']!)).toBe('#3c4d7c')
  })

  it('measures the ratios DESIGN.md records (to one decimal)', () => {
    const r = (a: string, b: string) => Math.round(contrast(a, b) * 10) / 10
    expect(r(light['--primary']!, light['--background']!)).toBe(9.5)
    expect(r(light['--primary']!, light['--muted']!)).toBe(8.5)
    expect(r(light['--primary-foreground']!, light['--primary']!)).toBe(10.1)
    expect(r(light['--secondary']!, light['--background']!)).toBe(6.3)
    expect(r(dark['--primary']!, dark['--background']!)).toBe(8.8)
    expect(r(dark['--primary']!, dark['--muted']!)).toBe(7.1)
    expect(r(dark['--primary-foreground']!, dark['--primary']!)).toBe(8.8)
  })

  it('sits on the shared paper and night neutrals', () => {
    expect(light['--background']).toBe('38 25% 97%')
    expect(light['--border']).toBe('30 18% 86%')
    expect(dark['--background']).toBe('220 15% 8%')
    expect(dark['--border']).toBe('220 10% 18%')
  })
})

describe('retired tokens', () => {
  it('the amber era rgb variables and glass tokens are gone', () => {
    for (const name of [
      '--foreground-rgb',
      '--background-start-rgb',
      '--accent-rgb',
      '--glass-bg',
      '--glass-shadow',
      '--color-primary-700',
      '--color-danger-600',
      '--color-success-600',
    ]) {
      expect(CSS).not.toContain(`${name}:`)
    }
  })

  it('never defines spacing tokens in @theme (they shadow max-w-*)', () => {
    expect(CSS).not.toMatch(/--spacing-(?:xs|sm|md|lg|xl|\dxl):/)
  })

  it('the body is flat paper, not a gradient', () => {
    const body = CSS.match(/\n\s*body\s*\{([^}]+)\}/)
    expect(body).not.toBeNull()
    expect(body![1]).not.toMatch(/gradient/)
    expect(body![1]).toContain('hsl(var(--background))')
  })
})
