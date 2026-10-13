import localFont from 'next/font/local'

// Three voices, all self-hosted from the @fontsource packages so the build
// never fetches a font. Fraunces speaks (headings, the wordmark), Instrument
// Sans reads (body), IBM Plex Mono catalogues (the wall label). See
// DESIGN.md → Typography. The packages are hoisted to the workspace root
// node_modules by Bun, hence the three `..`; tests/lib/fonts.test.ts checks
// that every file below exists.

export const fontDisplay = localFont({
  src: '../../../node_modules/@fontsource-variable/fraunces/files/fraunces-latin-wght-normal.woff2',
  weight: '100 900',
  style: 'normal',
  display: 'swap',
  // Preloaded, unlike the sibling sites: the home h1 is the LCP element and
  // is set in this face, and the file is 37 KB. Without the preload the font
  // was only requested once the CSS applied (384 ms, after a 378 ms FCP on
  // the CI runner) and the swap moved everything under the hero — 0.117 CLS
  // on desktop, which is what held the home performance score at the floor.
  preload: true,
  variable: '--font-display',
  fallback: ['ui-serif', 'Georgia', 'serif'],
  // Belt and braces for a load that still misses first paint: a
  // metric-adjusted Times New Roman (size-adjust, ascent/descent overrides).
  adjustFontFallback: 'Times New Roman',
})

export const fontBody = localFont({
  src: '../../../node_modules/@fontsource-variable/instrument-sans/files/instrument-sans-latin-wght-normal.woff2',
  weight: '400 700',
  style: 'normal',
  display: 'swap',
  variable: '--font-body',
  fallback: ['ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial', 'sans-serif'],
})

export const fontMono = localFont({
  src: [
    {
      path: '../../../node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2',
      weight: '400',
    },
    {
      path: '../../../node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2',
      weight: '500',
    },
    {
      path: '../../../node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-600-normal.woff2',
      weight: '600',
    },
  ],
  style: 'normal',
  // `optional`, not `swap`: the mono voice only ever paints small uppercase
  // labels, and a swap there flips a metadata row between one line and two.
  // The sibling site measured 0.135 CLS from exactly that.
  display: 'optional',
  preload: false,
  variable: '--font-mono',
  fallback: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
  // Without this next/font puts a metric-adjusted Arial face ahead of the
  // fallback list, so a load that misses the `optional` window painted every
  // wall label in sans. The fallback for a mono label is a mono font.
  adjustFontFallback: false,
})
