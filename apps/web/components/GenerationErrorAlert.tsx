import Link from 'next/link'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

export type ErrorKind = 'auth' | 'forbidden' | 'rate-limit' | 'unavailable' | 'offline' | 'limit' | 'generic'

interface GenerationErrorAlertProps {
  error: string
  errorKind: ErrorKind
  retryAfterSeconds: number | null
  onDismiss: () => void
}

const ERROR_TITLES: Record<ErrorKind, string> = {
  limit: 'Usage Limit Reached',
  'rate-limit': 'Rate Limit',
  auth: 'Authentication Required',
  forbidden: 'Upgrade Required',
  unavailable: 'Service Unavailable',
  offline: 'Connection Error',
  generic: 'Error',
}

function isAmber(kind: ErrorKind) {
  return kind === 'limit' || kind === 'rate-limit'
}

export default function GenerationErrorAlert({
  error,
  errorKind,
  retryAfterSeconds,
  onDismiss,
}: GenerationErrorAlertProps) {
  const amber = isAmber(errorKind)

  return (
    <div
      className={`${
        amber
          ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200/40 dark:border-amber-700/30'
          : 'bg-red-50/50 dark:bg-red-950/20 border-red-200/40 dark:border-red-700/30'
      } border text-sm px-4 py-3 rounded-2xl backdrop-blur-sm`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <ExclamationTriangleIcon
          className={`h-5 w-5 flex-shrink-0 ${amber ? 'text-amber-500' : 'text-red-500'}`}
        />
        <div className="flex-1">
          <p className={`font-medium ${amber ? 'text-amber-700' : 'text-red-700'}`}>
            {ERROR_TITLES[errorKind]}
          </p>
          <p className={amber ? 'text-amber-700' : 'text-red-700'}>
            {error}
          </p>

          {errorKind === 'auth' && (
            <Link
              href="/sign-in"
              className="inline-flex items-center mt-2 text-sm font-medium text-red-600 hover:text-red-700"
            >
              Sign in
              <span className="ml-1">&rarr;</span>
            </Link>
          )}
          {(errorKind === 'forbidden' || errorKind === 'limit') && (
            <Link
              href="/pricing"
              className="inline-flex items-center mt-2 text-sm font-medium text-amber-600 hover:text-amber-700"
            >
              Upgrade your plan
              <span className="ml-1">&rarr;</span>
            </Link>
          )}
          {(errorKind === 'unavailable' || errorKind === 'offline') && (
            <button
              type="submit"
              className="mt-2 text-xs bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-900/70 px-2 py-1 rounded transition-colors"
            >
              Retry
            </button>
          )}
          {errorKind === 'rate-limit' && retryAfterSeconds && (
            <p className="mt-1 text-xs text-amber-600">
              Try again in {retryAfterSeconds}s
            </p>
          )}
          {errorKind === 'generic' && (
            <button
              type="button"
              onClick={onDismiss}
              className="mt-2 text-xs bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-900/70 px-2 py-1 rounded transition-colors"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
