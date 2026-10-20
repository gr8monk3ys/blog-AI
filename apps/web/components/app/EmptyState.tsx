import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

export interface EmptyStateProps {
  /** The wall label: what kind of thing is missing. */
  kicker: string
  /** One serif line. */
  title: ReactNode
  description?: ReactNode
  /** The one primary action, or nothing. */
  action?: ReactNode
  className?: string
}

/**
 * An honest empty state in the notebook's voice (DESIGN.md → Do's): a wall
 * label, one serif line, an optional sentence in Ink Muted, and at most one
 * primary action. No illustration, no tinted box.
 */
export default function EmptyState({ kicker, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('py-16 text-center', className)}>
      <p className="label-mono">{kicker}</p>
      <h2 className="text-section-title mt-3">{title}</h2>
      {description ? <p className="mx-auto mt-3 max-w-md text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </div>
  )
}
