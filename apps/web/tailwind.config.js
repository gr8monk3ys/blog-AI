/** @type {import('tailwindcss').Config} */
const colors = require('tailwindcss/colors')

module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    // types/usage.ts holds the per-tier class names (TIER_DISPLAY). They used
    // to be generated only by coincidence — every one of them also appeared in
    // a scanned file — so adding a dark: variant there produced a class that
    // was never emitted and a tier chip that silently lost its colour.
    './types/**/*.{js,ts}',
  ],
  theme: {
    extend: {
      colors: {
        // Semantic aliases for the de-facto palette (amber primary, emerald
        // success). New code should prefer these; raw amber-*/emerald-*
        // classes remain valid while existing code migrates.
        primary: colors.amber,
        success: colors.emerald,
        danger: colors.red,
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['var(--font-serif)', 'Iowan Old Style', 'Times New Roman', 'serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
