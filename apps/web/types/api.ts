/**
 * Shapes of JSON bodies returned by our own API routes, for narrowing the
 * `unknown` that `Response.json()` yields under ts-reset.
 */

export interface ErrorBody {
  detail?: string
  error?: string
}

export type ApiEnvelope<T> =
  | { success: true; data: T }
  | { success?: false; error?: string }
