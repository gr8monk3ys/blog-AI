/**
 * The static brand assets are committed output of scripts/generate-brand.mjs.
 * These checks keep them present, well-formed, on-system (no gradient, no
 * filter) and in agreement with the React mark.
 */
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import { MARK_PATH } from '../../components/brand/Logo'

const ROOT = process.cwd()
const PUBLIC = join(ROOT, 'public')
const BRAND = join(PUBLIC, 'brand')
const REPO = join(ROOT, '..', '..')

const SVGS = [
  'mark.svg',
  'mark-dark.svg',
  'mark-mono.svg',
  'logo-horizontal.svg',
  'logo-horizontal-dark.svg',
  'logo-stacked.svg',
  'logo-stacked-dark.svg',
]

const PNGS: Array<[string, number]> = [
  ['favicon-16x16.png', 16],
  ['favicon-32x32.png', 32],
  ['apple-touch-icon.png', 180],
  ['android-chrome-192x192.png', 192],
  ['android-chrome-512x512.png', 512],
  ['android-chrome-512x512-maskable.png', 512],
]

function pngSize(file: string) {
  const buf = readFileSync(file)
  // PNG: 8-byte signature, then the IHDR chunk: length(4) "IHDR"(4) width(4) height(4).
  expect(buf.subarray(0, 8)).toEqual(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))
  expect(buf.subarray(12, 16).toString('ascii')).toBe('IHDR')
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }
}

describe('brand assets', () => {
  it.each(SVGS)('public/brand/%s parses as XML with no gradient or filter', (name) => {
    const file = join(BRAND, name)
    expect(existsSync(file)).toBe(true)
    const text = readFileSync(file, 'utf8')
    const doc = new DOMParser().parseFromString(text, 'image/svg+xml')
    expect(doc.querySelector('parsererror')).toBeNull()
    expect(doc.documentElement.tagName).toBe('svg')
    expect(doc.documentElement.getAttribute('viewBox')).toMatch(/^-?[\d.]+ -?[\d.]+ [\d.]+ [\d.]+$/)
    expect(doc.querySelector('linearGradient, radialGradient, filter')).toBeNull()
    expect(text).not.toMatch(/font-family|@font-face|<text/)
    expect(text).not.toMatch(/NaN/)
  })

  it('the mark files carry the same path as <LogoMark>', () => {
    for (const name of ['mark.svg', 'mark-dark.svg', 'mark-mono.svg']) {
      const doc = new DOMParser().parseFromString(
        readFileSync(join(BRAND, name), 'utf8'),
        'image/svg+xml'
      )
      const path = doc.querySelector('path')
      expect(path?.getAttribute('d')).toBe(MARK_PATH)
      expect(path?.getAttribute('fill-rule')).toBe('evenodd')
    }
    expect(readFileSync(join(BRAND, 'mark.svg'), 'utf8')).toContain('#2a3f79')
    expect(readFileSync(join(BRAND, 'mark-dark.svg'), 'utf8')).toContain('#a0b2e3')
    expect(readFileSync(join(BRAND, 'mark-mono.svg'), 'utf8')).toContain('fill="#000"')
  })

  it('the generator carries the same path as <LogoMark>', () => {
    const script = readFileSync(join(REPO, 'scripts', 'generate-brand.mjs'), 'utf8')
    expect(script).toContain(`'${MARK_PATH}'`)
  })

  it('the mark is a plate with the pilcrow as an evenodd hole', () => {
    // Plate first (the full 24-unit square), pilcrow second.
    expect(MARK_PATH.startsWith('M0 0H24V24H0Z')).toBe(true)
    expect(MARK_PATH.split('Z').filter(Boolean)).toHaveLength(2)
  })

  it('ships a README with the rules', () => {
    const readme = readFileSync(join(BRAND, 'README.md'), 'utf8')
    expect(readme).toMatch(/clear space/i)
    expect(readme).toMatch(/16px/)
    expect(readme).toMatch(/96px/)
    expect(readme).toMatch(/do not.*rotate/i)
  })

  it.each(PNGS)('public/%s is a %ipx square PNG', (name, size) => {
    const file = join(PUBLIC, name)
    expect(existsSync(file)).toBe(true)
    expect(pngSize(file)).toEqual({ width: size, height: size })
  })

  it('favicon.ico holds the 16, 32 and 48 sizes', () => {
    const buf = readFileSync(join(PUBLIC, 'favicon.ico'))
    // ICONDIR: reserved(2)=0, type(2)=1, count(2); then 16-byte entries with width, height.
    expect(buf.readUInt16LE(0)).toBe(0)
    expect(buf.readUInt16LE(2)).toBe(1)
    const count = buf.readUInt16LE(4)
    const sizes = Array.from({ length: count }, (_, i) => buf.readUInt8(6 + i * 16))
    expect(sizes.sort((a, b) => a - b)).toEqual([16, 32, 48])
  })

  it('the amber icon is gone and the manifest points at the paragraph mark', () => {
    expect(existsSync(join(PUBLIC, 'icon.svg'))).toBe(false)
    expect(existsSync(join(PUBLIC, 'manifest.json'))).toBe(false)
    const manifest = readFileSync(join(ROOT, 'app', 'manifest.ts'), 'utf8')
    expect(manifest).toContain("theme_color: '#2a3f79'")
    expect(manifest).toContain("background_color: '#f9f8f5'")
    expect(manifest).toContain('/android-chrome-512x512.png')
    const layout = readFileSync(join(ROOT, 'app', 'layout.tsx'), 'utf8')
    expect(layout).toContain('/favicon.ico')
    expect(layout).toContain('/apple-touch-icon.png')
    expect(layout).not.toContain('icon.svg')
  })
})
