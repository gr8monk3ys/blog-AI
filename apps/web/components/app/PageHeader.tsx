import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

export interface PageHeaderProps {
  /** The wall label above the title (DESIGN.md → The Wall Label Rule). */
  kicker: string
  title: ReactNode
  description?: ReactNode
  /** The view's actions; at most one of them is the primary button. */
  actions?: ReactNode
  className?: string
}

/**
 * The head of every signed-in page: a mono wall label, the page's one
 * Fraunces headline (`text-page-title`), an optional description in Ink
 * Muted, and the view's actions at the right. Pages render it first inside
 * the shell's <main>.
 */
export default function PageHeader({ kicker, title, description, actions, className }: PageHeaderProps) {
  return (
    <header className={cn('mb-8 flex flex-wrap items-end justify-between gap-x-8 gap-y-4', className)}>
      <div className="min-w-0 max-w-2xl">
        <p className="label-mono">{kicker}</p>
        <h1 className="text-page-title mt-2">{title}</h1>
        {description ? <p className="mt-3 text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-3">{actions}</div> : null}
    </header>
  )
}
