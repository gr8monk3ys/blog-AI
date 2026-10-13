#!/usr/bin/env node
/* global console, process */
/**
 * generate-brand.mjs — every static brand asset, from one path.
 *
 *   bun run brand:generate        (node scripts/generate-brand.mjs)
 *
 * The mark is the paragraph mark: a square Iron Gall plate with a pilcrow (¶)
 * cut out of it (DESIGN.md → Components → Mark and Wordmark). This script is
 * the source of truth for everything under apps/web/public/brand/, the
 * favicons and app icons in apps/web/public/, and docs/brand/lockups.png; the
 * PNGs are committed so the build never has to run it.
 *
 * Writes:
 *   apps/web/public/brand/mark.svg, mark-dark.svg, mark-mono.svg
 *   apps/web/public/brand/logo-horizontal{,-dark}.svg, logo-stacked{,-dark}.svg
 *     (wordmark converted to outlines with opentype.js — no font reference)
 *   apps/web/public/favicon.ico (16+32+48), favicon-16x16.png, favicon-32x32.png
 *   apps/web/public/apple-touch-icon.png (180), android-chrome-192x192.png,
 *     android-chrome-512x512.png, android-chrome-512x512-maskable.png
 *   docs/brand/lockups.png (a 2x contact sheet for the README and PRs)
 *
 * MARK_PATH must equal the constant in apps/web/components/brand/Logo.tsx;
 * apps/web/tests/brand/brand-assets.test.ts fails when the two drift.
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { Resvg } from '@resvg/resvg-js'
import pngToIco from 'png-to-ico'

// opentype.js ships CJS; createRequire keeps this file plain ESM.
const require = createRequire(import.meta.url)
const opentype = require('opentype.js')

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const PUBLIC = join(ROOT, 'apps', 'web', 'public')
const BRAND = join(PUBLIC, 'brand')
const DOCS = join(ROOT, 'docs', 'brand')
const FONT = join(ROOT, 'node_modules/@fontsource/fraunces/files/fraunces-latin-700-normal.woff')

/* ------------------------------------------------------------------ tokens */

// DESIGN.md → Colors. Literal because an SVG file has no CSS variables.
const IRON_GALL = '#2a3f79'
const IRON_GALL_NIGHT = '#a0b2e3'
const PAPER = '#f9f8f5'
const NIGHT = '#111317'
const INK = '#1a1f23'
const NIGHT_INK = '#fafafa'

/* -------------------------------------------------------------------- mark */

// The plate (first subpath) and the pilcrow (second). With fill-rule evenodd
// the pilcrow is a hole. Same string as Logo.tsx.
const MARK_PATH =
  'M0 0H24V24H0ZM9.6 3.2H18.8V5.6H16.8V20.8H14.4V5.6H12.6V20.8H10.2V13.8H9.6C6.7 13.8 4.4 11.4 4.4 8.5C4.4 5.6 6.7 3.2 9.6 3.2Z'
const PILCROW_PATH = MARK_PATH.slice(MARK_PATH.indexOf('M9.6'))
const MARK_UNITS = 24

// Fraunces 700: sCapHeight 1400 / unitsPerEm 2000.
const CAP_HEIGHT = 0.7
const TRACKING = -0.02

const markPath = (fill) => `<path fill="${fill}" fill-rule="evenodd" d="${MARK_PATH}"/>`

/** The mark alone, viewBox 0 0 24 24. The hole is transparent. */
function markSvg(fill) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${MARK_UNITS} ${MARK_UNITS}">${markPath(fill)}</svg>`
}

/**
 * The mark with the pilcrow filled (the favicon form). Outside the plate
 * stays transparent, but the ¶ is paper rather than a hole so the favicon
 * reads the same on a light and a dark tab strip.
 */
function faviconSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${MARK_UNITS} ${MARK_UNITS}"><path fill="${PAPER}" d="${PILCROW_PATH}"/>${markPath(IRON_GALL)}</svg>`
}

/** The mark on a paper ground with `padding` (fraction of the side) around it. No transparency. */
function appIconSvg(padding) {
  const inner = 1 - padding * 2
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect width="1" height="1" fill="${PAPER}"/><g transform="translate(${padding} ${padding}) scale(${inner / MARK_UNITS})">${markPath(IRON_GALL)}</g></svg>`
}

/* ---------------------------------------------------------------- wordmark */

async function loadFont() {
  const buf = await readFile(FONT)
  // opentype.parse wants the exact ArrayBuffer slice; Buffer.buffer is the pool.
  return opentype.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength))
}

/**
 * Serialise an opentype.js Path to SVG path data at two decimals. Not
 * `Path.toPathData`: opentype.js 2.0 memoises its rounding on the float's
 * fractional part and that cache hands back NaN for some sizes.
 */
function pathData(path) {
  const n = (v) => {
    if (!Number.isFinite(v)) throw new Error(`non-finite coordinate in wordmark path: ${v}`)
    return String(Math.round(v * 100) / 100)
  }
  let d = ''
  for (const c of path.commands) {
    if (c.type === 'M' || c.type === 'L') d += `${c.type}${n(c.x)} ${n(c.y)}`
    else if (c.type === 'Q') d += `Q${n(c.x1)} ${n(c.y1)} ${n(c.x)} ${n(c.y)}`
    else if (c.type === 'C') d += `C${n(c.x1)} ${n(c.y1)} ${n(c.x2)} ${n(c.y2)} ${n(c.x)} ${n(c.y)}`
    else if (c.type === 'Z') d += 'Z'
    else throw new Error(`unknown path command ${c.type}`)
  }
  return d
}

/**
 * "Blog AI" as two outlined paths, "Blog " and "AI", at `fontSize` with the
 * baseline at (x, y). Kerning stays on; the split falls on the word space.
 */
function wordmark(font, x, y, fontSize) {
  const opts = { kerning: true, letterSpacing: TRACKING }
  const blog = font.getPath('Blog ', x, y, fontSize, opts)
  const advance = font.getAdvanceWidth('Blog ', fontSize, opts)
  const ai = font.getPath('AI', x + advance, y, fontSize, opts)
  const a = blog.getBoundingBox()
  const b = ai.getBoundingBox()
  return {
    blog: pathData(blog),
    ai: pathData(ai),
    bbox: { x1: a.x1, y1: Math.min(a.y1, b.y1), x2: b.x2, y2: Math.max(a.y2, b.y2) },
  }
}

const r2 = (n) => Math.round(n * 100) / 100

/**
 * A lockup, drawn at mark size M. Horizontal: mark, a gap of M/2 (12px at the
 * component's default 24px), wordmark with cap height M. Stacked: mark above,
 * the same gap, wordmark centred beneath with cap height M/2. The viewBox is
 * tight around the ink.
 */
function lockupSvg(font, { variant, markFill, inkFill, accentFill }) {
  const M = 96
  const GAP = M / 2
  let markX, markY, wm
  if (variant === 'horizontal') {
    const fontSize = M / CAP_HEIGHT
    markX = 0
    markY = 0
    wm = wordmark(font, M + GAP, M, fontSize)
  } else {
    const cap = M / 2
    const fontSize = cap / CAP_HEIGHT
    const probe = wordmark(font, 0, 0, fontSize)
    const width = probe.bbox.x2 - probe.bbox.x1
    markX = (width - M) / 2 + probe.bbox.x1
    markY = 0
    wm = wordmark(font, 0, M + GAP + cap, fontSize)
  }
  const x1 = Math.min(markX, wm.bbox.x1)
  const y1 = Math.min(markY, wm.bbox.y1)
  const x2 = Math.max(markX + M, wm.bbox.x2)
  const y2 = Math.max(markY + M, wm.bbox.y2)
  const scale = M / MARK_UNITS
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${r2(x1)} ${r2(y1)} ${r2(x2 - x1)} ${r2(y2 - y1)}">` +
    `<title>Blog AI</title>` +
    `<g transform="translate(${r2(markX)} ${r2(markY)}) scale(${r2(scale)})">${markPath(markFill)}</g>` +
    `<path fill="${inkFill}" d="${wm.blog}"/>` +
    `<path fill="${accentFill}" d="${wm.ai}"/>` +
    `</svg>`
  )
}

/* ------------------------------------------------------------------ raster */

function png(svg, width, background) {
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: width },
    ...(background ? { background } : {}),
  })
  return resvg.render().asPng()
}

const dataUri = (buf) => `data:image/png;base64,${buf.toString('base64')}`

/**
 * docs/brand/lockups.png — a 2x contact sheet: the mark at 16/32/88, the two
 * lockups, by day and by night.
 */
function contactSheet(font) {
  const W = 1200
  const H = 760
  const rows = [
    { y: 0, bg: PAPER, mark: IRON_GALL, ink: INK, label: INK },
    { y: H / 2, bg: NIGHT, mark: IRON_GALL_NIGHT, ink: NIGHT_INK, label: NIGHT_INK },
  ]
  const parts = []
  for (const row of rows) {
    parts.push(`<rect y="${row.y}" width="${W}" height="${H / 2}" fill="${row.bg}"/>`)
    let x = 48
    const cy = row.y + 110
    for (const size of [16, 32, 88]) {
      parts.push(
        `<image x="${x}" y="${cy - size / 2}" width="${size}" height="${size}" href="${dataUri(png(markSvg(row.mark), size, row.bg))}"/>`
      )
      x += size + 32
    }
    const horizontal = lockupSvg(font, {
      variant: 'horizontal',
      markFill: row.mark,
      inkFill: row.ink,
      accentFill: row.mark,
    })
    const stacked = lockupSvg(font, {
      variant: 'stacked',
      markFill: row.mark,
      inkFill: row.ink,
      accentFill: row.mark,
    })
    const hw = 420
    parts.push(
      `<image x="${x + 48}" y="${cy - 32}" width="${hw}" height="64" preserveAspectRatio="xMinYMid" href="${dataUri(png(horizontal, hw * 2, row.bg))}"/>`
    )
    const sw = 200
    parts.push(
      `<image x="${x + 48 + hw + 96}" y="${row.y + 40}" width="${sw}" height="${sw * 1.1}" preserveAspectRatio="xMidYMin" href="${dataUri(png(stacked, sw * 2, row.bg))}"/>`
    )
    parts.push(
      `<text x="48" y="${row.y + H / 2 - 40}" font-family="ui-monospace, Menlo, monospace" font-size="13" letter-spacing="2" fill="${row.label}" opacity="0.6">${row.bg === PAPER ? 'PAPER · IRON GALL #2A3F79' : 'NIGHT · IRON GALL #A0B2E3'} · MARK 16 / 32 / 88 · HORIZONTAL · STACKED</text>`
    )
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${parts.join('')}</svg>`
  return png(svg, W * 2)
}

/* -------------------------------------------------------------------- main */

async function main() {
  await mkdir(BRAND, { recursive: true })
  await mkdir(DOCS, { recursive: true })
  const font = await loadFont()

  const svgs = {
    'mark.svg': markSvg(IRON_GALL),
    'mark-dark.svg': markSvg(IRON_GALL_NIGHT),
    'mark-mono.svg': markSvg('#000'),
    'logo-horizontal.svg': lockupSvg(font, {
      variant: 'horizontal',
      markFill: IRON_GALL,
      inkFill: INK,
      accentFill: IRON_GALL,
    }),
    'logo-horizontal-dark.svg': lockupSvg(font, {
      variant: 'horizontal',
      markFill: IRON_GALL_NIGHT,
      inkFill: NIGHT_INK,
      accentFill: IRON_GALL_NIGHT,
    }),
    'logo-stacked.svg': lockupSvg(font, {
      variant: 'stacked',
      markFill: IRON_GALL,
      inkFill: INK,
      accentFill: IRON_GALL,
    }),
    'logo-stacked-dark.svg': lockupSvg(font, {
      variant: 'stacked',
      markFill: IRON_GALL_NIGHT,
      inkFill: NIGHT_INK,
      accentFill: IRON_GALL_NIGHT,
    }),
  }
  for (const [name, svg] of Object.entries(svgs)) {
    await writeFile(join(BRAND, name), `${svg}\n`)
  }

  const favicon = faviconSvg()
  const pngs = {
    'favicon-16x16.png': png(favicon, 16),
    'favicon-32x32.png': png(favicon, 32),
    'apple-touch-icon.png': png(appIconSvg(0.12), 180),
    'android-chrome-192x192.png': png(appIconSvg(0.12), 192),
    'android-chrome-512x512.png': png(appIconSvg(0.12), 512),
    // Maskable safe zone is a circle of 80% diameter; a square inscribed in
    // it has a side of 0.8/√2 ≈ 0.566, so 22% padding keeps the plate inside.
    'android-chrome-512x512-maskable.png': png(appIconSvg(0.22), 512),
  }
  for (const [name, buf] of Object.entries(pngs)) {
    await writeFile(join(PUBLIC, name), buf)
  }
  await writeFile(
    join(PUBLIC, 'favicon.ico'),
    await pngToIco([png(favicon, 16), png(favicon, 32), png(favicon, 48)])
  )

  await writeFile(join(DOCS, 'lockups.png'), contactSheet(font))

  console.log(
    `brand: ${Object.keys(svgs).length} SVGs in apps/web/public/brand, ${Object.keys(pngs).length + 1} icons in apps/web/public, docs/brand/lockups.png`
  )
}

main().catch((err) => {
  console.error(err)
  process.exitCode = 1
})
