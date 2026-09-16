'use client'

import { useEffect, useRef, useState, type ReactNode } from 'react'

// Scroll-triggered fade-and-rise for the homepage sections below the fold.
//
// This used to be framer-motion (`motion.div` + `useInView`). That cost ~130 KB
// of JavaScript on the home route and, worse, framer serialises its `initial`
// state into the server HTML — so the LCP headline shipped as `opacity:0` and
// stayed invisible until the whole page had hydrated. The motion itself is
// now CSS (see "Homepage entrance motion" in app/globals.css); JS only flips
// `data-inview` once the element scrolls into view. Nothing above the fold
// goes through this component — the hero animates with plain keyframes so it
// is painted on the very first frame.

const ROOT_MARGIN = '-60px' // matches the old useInView(ref, { margin: '-60px' })

function useInViewOnce<T extends Element>(): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node || inView) return

    if (typeof IntersectionObserver === 'undefined') {
      setInView(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setInView(true)
          observer.disconnect()
        }
      },
      { rootMargin: ROOT_MARGIN }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [inView])

  return [ref, inView]
}

interface RevealProps {
  children: ReactNode
  className?: string
  /**
   * Stagger the direct children 120 ms apart (the old STAGGER_CONTAINER
   * variant) instead of moving the wrapper as one block.
   */
  stagger?: boolean
  /** Render as a list instead of a div (keeps the tool strip semantic). */
  as?: 'div' | 'ul'
}

export function Reveal({
  children,
  className,
  stagger = false,
  as: Tag = 'div',
}: RevealProps): React.ReactElement {
  const [ref, inView] = useInViewOnce<HTMLDivElement>()
  const attrs = stagger ? { 'data-reveal-stagger': '' } : { 'data-reveal': '' }

  return (
    <Tag
      ref={ref as React.RefObject<HTMLDivElement & HTMLUListElement>}
      className={className}
      role={Tag === 'ul' ? 'list' : undefined}
      data-inview={inView ? '' : undefined}
      {...attrs}
    >
      {children}
    </Tag>
  )
}
