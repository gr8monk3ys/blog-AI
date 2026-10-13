import type { SVGProps } from 'react'
import { cn } from '../../lib/cn'

/**
 * The paragraph mark.
 *
 * Blog AI writes long-form prose, and the editor's mark for a paragraph is
 * the pilcrow. The mark is a square plate of Iron Gall ink — square corners,
 * because squareness marks the work — with a pilcrow (¶) cut out of it in
 * paper: a 24-unit grid, the bowl a half-disc on the left, two stems to the
 * baseline. It was rendered and checked at 16/24/32/88/160 on paper and on
 * night; a pen-nib alternative was rejected because it read as a map pin.
 *
 * One path, `fill-rule="evenodd"`: the plate is the first subpath and the
 * pilcrow the second, so the ¶ is a true hole and whatever the mark sits on
 * shows through. The ink is `hsl(var(--primary))`, so the same element is
 * Iron Gall on paper by day and the lifted Iron Gall on night without a
 * `dark:` override. `scripts/generate-brand.mjs` carries the same path for
 * the static assets in `public/brand/`; `tests/brand/brand-assets.test.ts`
 * keeps the two equal.
 */
export const MARK_PATH =
  'M0 0H24V24H0ZM9.6 3.2H18.8V5.6H16.8V20.8H14.4V5.6H12.6V20.8H10.2V13.8H9.6C6.7 13.8 4.4 11.4 4.4 8.5C4.4 5.6 6.7 3.2 9.6 3.2Z'

/**
 * Fraunces 700's cap height as a fraction of the em (`sCapHeight` 1400 over
 * 2000 units per em). The mark's height equals the wordmark's cap height, so
 * a wordmark set beside a mark of `size` px is `size / WORDMARK_CAP_HEIGHT`
 * px of type.
 */
export const WORDMARK_CAP_HEIGHT = 0.7

export interface LogoMarkProps extends Omit<SVGProps<SVGSVGElement>, 'width' | 'height'> {
  /** Rendered width and height in px. A `size-*` class on `className` overrides it. */
  size?: number
  /** An accessible name. Without one the mark is decorative (`aria-hidden`). */
  title?: string
  className?: string
}

export function LogoMark({ size = 24, title, className, ...rest }: LogoMarkProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      className={cn('shrink-0', className)}
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      <path fill="hsl(var(--primary))" fillRule="evenodd" d={MARK_PATH} />
    </svg>
  )
}

export interface LogoProps {
  /**
   * `horizontal`: mark, 12px gap, wordmark, with the mark as tall as the
   * wordmark's capitals. `stacked`: mark above, 12px gap, wordmark centred
   * beneath, the mark twice the wordmark's cap height. `mark`: the stamp alone.
   */
  variant?: 'horizontal' | 'stacked' | 'mark'
  /** The mark's height in px. The wordmark is sized from it. */
  size?: number
  className?: string
}

/**
 * The signature: the paragraph mark beside the name. The wordmark is live
 * text in Fraunces 700, Ink, with "AI" in Iron Gall — one phrase in ink, the
 * house device. Server-safe; no client hooks.
 */
export function Logo({ variant = 'horizontal', size = 24, className }: LogoProps) {
  if (variant === 'mark') {
    return <LogoMark size={size} title="Blog AI" className={className} />
  }

  const stacked = variant === 'stacked'
  const capHeight = stacked ? size / 2 : size
  const fontSize = capHeight / WORDMARK_CAP_HEIGHT

  return (
    <span
      role="img"
      aria-label="Blog AI"
      className={cn(
        'inline-flex items-center gap-3 text-foreground',
        stacked && 'flex-col justify-center',
        className
      )}
    >
      <LogoMark size={size} aria-hidden />
      {/* The wordmark is one of the Serif Speaks Rule's named exceptions. */}
      <span
        data-voice="display"
        className="font-display leading-none font-bold tracking-tight"
        style={{ fontSize }}
      >
        Blog <span className="text-primary">AI</span>
      </span>
    </span>
  )
}

export default Logo
