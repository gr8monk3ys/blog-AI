import { ImageResponse } from 'next/og'
import { existsSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'

import { MARK_PATH } from '../components/brand/Logo'

// Node.js runtime, not edge: nothing here is request-dependent, so Next
// prerenders the card at build time and no function ships for it.
export const alt = 'Blog AI — Brand-Consistent AI Content'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

// The notebook's stationery, as literal values: @vercel/og renders no CSS
// variables. Paper #f9f8f5, ink #1a1f23, muted #606976, hairline #e2dbd5,
// Iron Gall #2a3f79 — the same tokens as app/globals.css.
const PAPER = '#f9f8f5'
const INK = '#1a1f23'
const INK_MUTED = '#606976'
const HAIRLINE = '#e2dbd5'
const IRON_GALL = '#2a3f79'

// @vercel/og needs a static TTF/WOFF, not the variable woff2 the pages use.
// The @fontsource packages are hoisted to the workspace root by Bun, so the
// build (cwd apps/web) finds them two directories up; a cwd at the repo root
// finds them directly.
function fontFile(relative: string): string {
  for (const base of [process.cwd(), join(process.cwd(), '..', '..')]) {
    const candidate = join(base, 'node_modules', relative)
    if (existsSync(candidate)) return candidate
  }
  throw new Error(`opengraph-image: font not found in node_modules: ${relative}`)
}

export default async function Image() {
  const [displayFont, monoFont] = await Promise.all([
    readFile(fontFile('@fontsource/fraunces/files/fraunces-latin-700-normal.woff')),
    readFile(fontFile('@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff')),
  ])

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '72px 80px',
          backgroundColor: PAPER,
          color: INK,
        }}
      >
        {/* Wall label: the mono kicker above the title. */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            fontFamily: 'IBM Plex Mono',
            fontSize: 20,
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: INK_MUTED,
          }}
        >
          {/* The paragraph mark. Satori serialises inline SVG, so the evenodd
              cut-out shows the paper through the pilcrow. */}
          <svg width={28} height={28} viewBox="0 0 24 24">
            <path fill={IRON_GALL} fillRule="evenodd" d={MARK_PATH} />
          </svg>
          <span>A manuscript in progress</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex', // Satori: any node with several children must be flex
              fontFamily: 'Fraunces',
              fontSize: 112,
              fontWeight: 700,
              lineHeight: 1.02,
              letterSpacing: '-3px',
              color: INK,
            }}
          >
            Blog&nbsp;<span style={{ color: IRON_GALL }}>AI</span>
          </div>
          <div
            style={{
              marginTop: 28,
              fontSize: 32,
              lineHeight: 1.4,
              maxWidth: 900,
              color: INK_MUTED,
            }}
          >
            Train your brand voice once, run repeatable SEO content workflows, and generate
            publish-ready drafts faster.
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderTop: `1px solid ${HAIRLINE}`,
            paddingTop: 24,
            fontFamily: 'IBM Plex Mono',
            fontSize: 20,
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: INK_MUTED,
          }}
        >
          <span>Brand voice · SEO workflows · Drafts</span>
          <span>Free to start</span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: 'Fraunces', data: displayFont, weight: 700, style: 'normal' },
        { name: 'IBM Plex Mono', data: monoFont, weight: 500, style: 'normal' },
      ],
    }
  )
}
