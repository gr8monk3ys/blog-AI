// Framer Motion variants shared across the homepage sections.
// Extracted from HomePageClient.tsx to keep that file focused on layout.

import type { Variants } from 'framer-motion'

export const FADE_UP: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
}

export const FADE_IN: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

export const STAGGER_CONTAINER: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
}
