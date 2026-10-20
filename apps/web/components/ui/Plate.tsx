import { forwardRef, type CSSProperties, type HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// The draft sheet — the notebook's signature object for the work itself. A
// square-cornered plate of tinted paper with a 1px hairline, like a sheet
// pasted onto the page: a post preview, a book cover, a template. Squareness
// marks the work; roundness marks the interface. Nothing on it scales, lifts
// or rounds on hover; an interactive parent warms the border to the ink at
// 45% instead. See DESIGN.md → Components → Draft Sheet.
export type PlateAspect = 'portrait' | 'landscape' | 'square' | 'auto'

// Inline rather than aspect-* utilities: the stylesheet is inlined into every
// document, and three arbitrary-value classes for one component is a cost
// every page would pay.
const ASPECT: Record<PlateAspect, CSSProperties['aspectRatio']> = {
  // A manuscript page: 3:4, the proportion of a sheet of paper.
  portrait: '3 / 4',
  landscape: '4 / 3',
  square: '1 / 1',
  auto: undefined,
}

export interface PlateProps extends HTMLAttributes<HTMLDivElement> {
  aspect?: PlateAspect
}

export const Plate = forwardRef<HTMLDivElement, PlateProps>(function Plate(
  { className, aspect = 'portrait', style, ...props },
  ref
) {
  const aspectRatio = ASPECT[aspect]
  return (
    <div
      ref={ref}
      className={cn('plate relative', className)}
      style={aspectRatio ? { aspectRatio, ...style } : style}
      {...props}
    />
  )
})

export default Plate
