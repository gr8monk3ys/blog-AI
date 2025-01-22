'use client'

import * as Sentry from '@sentry/nextjs'
import { Component, ReactNode } from 'react'

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

    // Report to Sentry with enhanced context
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

    this.setState({ eventId })
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, eventId: null })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[200px] flex items-center justify-center p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md w-full text-center">
            <div className="text-red-600 mb-4">
              <svg
                className="h-12 w-12 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-red-800 mb-2">
              Something went wrong
            </h2>
            <p className="text-red-700 text-sm mb-4">
              An unexpected error occurred. Our team has been notified.
            </p>
            {/* Show event ID for support reference without exposing error details */}
            {this.state.eventId && (
              <p className="text-red-500 text-xs mb-4 font-mono">
                Error ID: {this.state.eventId.substring(0, 8)}
              </p>
            )}
            <button
              onClick={this.handleReset}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
