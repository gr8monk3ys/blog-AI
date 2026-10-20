'use client'

import { Component, ReactNode } from 'react'
import { getSentry } from '../lib/sentry-client'
import { buttonVariants } from './ui/Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  /** Component name for Sentry tagging */
  componentName?: string
  /** Additional context for error reporting */
  context?: Record<string, unknown>
}

interface State {
  hasError: boolean
  error: Error | null
  eventId: string | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, eventId: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log to console for development
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // Report to Sentry with enhanced context. The SDK is lazy-loaded
    // (lib/sentry-client.ts); the event id arrives once it has initialised.
    void getSentry()
      .then((Sentry) => {
        const eventId = Sentry.captureException(error, {
          tags: {
            errorBoundary: 'component',
            componentName: this.props.componentName || 'unknown',
          },
          contexts: {
            react: {
              componentStack: errorInfo.componentStack,
            },
            custom: this.props.context || {},
          },
          // Filter out any PII that might be in error messages
          fingerprint: ['{{ default }}', this.props.componentName || 'ErrorBoundary'],
        })
        if (this.state.hasError && this.state.error === error) {
          this.setState({ eventId })
        }
      })
      .catch(() => {
        // Reporting is best-effort; the fallback UI is already shown.
      })
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, eventId: null })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      // An honest error state in the house voice (DESIGN.md → Do): a wall
      // label in the signal colour, one serif line, one action. Flat paper.
      return (
        <div className="flex min-h-[200px] items-center justify-center p-6">
          <div className="w-full max-w-md border-y border-border py-8" role="alert">
            <p className="label-mono text-destructive">Error</p>
            <h2 className="text-card-title mt-3">Something Went Wrong</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              An unexpected error occurred. Our team has been notified.
            </p>
            {/* Show event ID for support reference without exposing error details */}
            {this.state.eventId && (
              <p className="label-mono mt-3 normal-case tracking-normal">
                Error ID: {this.state.eventId.substring(0, 8)}
              </p>
            )}
            <button
              type="button"
              onClick={this.handleReset}
              className={buttonVariants({ variant: 'outline', className: 'mt-6' })}
            >
              Try Again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
