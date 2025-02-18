/**
 * Integrated Logger with Sentry
 *
 * Environment-aware logging that:
 * - Logs to console in development
 * - Captures errors/warnings in Sentry in production
 * - Adds breadcrumbs for debugging
 */

import * as Sentry from '@sentry/nextjs'

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogContext {
  component?: string
  action?: string
  [key: string]: unknown
}

const isDev = process.env.NODE_ENV === 'development'

/**
 * Core logging function
 */
function log(level: LogLevel, message: string, context?: LogContext): void {
  const timestamp = new Date().toISOString()
  const prefix = `[${timestamp}] [${level.toUpperCase()}]`

  // Always log to console in development
  if (isDev) {
    const contextStr = context ? ` ${JSON.stringify(context)}` : ''
    switch (level) {
      case 'debug':
        console.debug(`${prefix} ${message}${contextStr}`)
        break
      case 'info':
        console.info(`${prefix} ${message}${contextStr}`)
        break
      case 'warn':
        console.warn(`${prefix} ${message}${contextStr}`)
        break
      case 'error':
        console.error(`${prefix} ${message}${contextStr}`)
        break
    }
    return
  }

  // In production, use Sentry
  switch (level) {
    case 'debug':
      // Add breadcrumb for debugging (doesn't create an event)
      Sentry.addBreadcrumb({
        category: context?.component || 'app',
        message,
        level: 'debug',
        data: context,
      })
      break

    case 'info':
      // Add breadcrumb only (info-level events are too noisy)
      Sentry.addBreadcrumb({
        category: context?.component || 'app',
        message,
        level: 'info',
        data: context,
      })
      break

    case 'warn':
      // Capture as a Sentry message
      Sentry.captureMessage(message, {
        level: 'warning',
        tags: {
          component: context?.component,
          action: context?.action,
        },
        extra: context,
      })
      break

    case 'error':
      // Capture as a Sentry exception (creates an event)
      Sentry.captureException(new Error(message), {
        tags: {
          component: context?.component,
          action: context?.action,
        },
        extra: context,
      })
      break
  }
}

/**
 * Logger instance with convenience methods
 */
export const logger = {
  debug: (message: string, context?: LogContext) => log('debug', message, context),
  info: (message: string, context?: LogContext) => log('info', message, context),
  warn: (message: string, context?: LogContext) => log('warn', message, context),
  error: (message: string, context?: LogContext) => log('error', message, context),

  /**
   * Log an error with full stack trace
   */
  exception: (error: Error, context?: LogContext) => {
    if (isDev) {
      console.error('[ERROR]', error.message, error.stack, context)
    } else {
      Sentry.captureException(error, {
        tags: {
          component: context?.component,
          action: context?.action,
        },
        extra: context,
      })
    }
  },
}

// Convenience exports for common patterns
export const logError = (message: string, context?: LogContext) =>
  logger.error(message, context)

export const logWarn = (message: string, context?: LogContext) =>
  logger.warn(message, context)

export const logInfo = (message: string, context?: LogContext) =>
  logger.info(message, context)

export const logDebug = (message: string, context?: LogContext) =>
  logger.debug(message, context)

export default logger
